import os
import json
import tyro

from dataclasses import dataclass
from pathlib import Path
from datasets import load_dataset
# from unsloth import FastLanguageModel  # Commented out - requires NVIDIA/Intel GPU
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, TrainingArguments
from peft import LoraConfig, get_peft_model, TaskType
from trl import SFTTrainer, SFTConfig


SYSTEM_INSTRUCTION = "You are a pro Pokèmon Showdown player. Find the best action given this battle state"


@dataclass
class Args:
    model_name: str = "unsloth/mistral-7b"
    dataset: str = "dataset_gen9ou_100"
    out_dir: str = None
    use_qlora = True                  # 4-bit by default with Unsloth
    use_wandb = False              # set True to log to Weights & Biases
    wandb_project = "poke-llm"

    def __post_init__(self):
        self.train_path = os.path.join(f"dataset/processed/train/{self.dataset}.jsonl")
        self.val_path = os.path.join(f"dataset/processed/val/{self.dataset}.jsonl")

        if self.out_dir is None:

            os.makedirs("models", exist_ok=True)
            # take last part after slash, strip weird chars
            model_basename = self.model_name.split("/")[-1].replace(":", "_")
            self.out_dir = f"models/lora-{model_basename}"


if __name__ == "__main__":

    args = tyro.cli(Args)

    train_ds = load_dataset("json", data_files=args.train_path)["train"]
    val_ds = load_dataset("json", data_files=args.val_path)["train"] if args.val_path else None

    # Load base model + tokenizer
    # model, tokenizer = FastLanguageModel.from_pretrained(
    #     model_name=args.model_name,
    #     max_seq_length=2048,
    #     dtype=None,
    #     load_in_4bit=args.use_qlora,
    # )

    # Standard transformers loading
    quantization_config = None
    if args.use_qlora:
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype="float16",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4"
        )

    model = AutoModelForCausalLM.from_pretrained(
        args.model_name,
        quantization_config=quantization_config,
        device_map="auto" if quantization_config else None,
        torch_dtype="auto"
    )

    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Lora adapter
    # model = FastLanguageModel.get_peft_model(
    #     model,
    #     r=16, lora_alpha=16, lora_dropout=0.0, bias="none",
    #     target_modules=[
    #         "q_proj",
    #         "k_proj",
    #         "v_proj",
    #         "o_proj",
    #         "gate_proj",
    #         "up_proj",
    #         "down_proj"
    #     ],
    #     use_gradient_checkpointing=True,
    #     random_state=3407,
    # )

    # Standard PEFT LoRA configuration
    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=16,
        lora_alpha=16,
        lora_dropout=0.0,
        bias="none",
        target_modules=[
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj"
        ]
    )

    model = get_peft_model(model, lora_config)

    # 4) Turn each row into chat messages; SFTTrainer masks loss to assistant
    def to_messages(ex):
        return [
            {"role":"system",    "content": SYSTEM_INSTRUCTION},
            {"role":"user",      "content": ex["input"]},
            {"role":"assistant", "content": ex["output"]},
        ]

    # 5) Training config (tiny + sane defaults)
    if args.use_wandb:
        os.environ.setdefault("WANDB_PROJECT", args.wandb_project)
    report_to = "wandb" if args.use_wandb else "none"

    # General training arguments
    training_args = TrainingArguments(
        output_dir=args.out_dir,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=8,
        learning_rate=2e-4,
        num_train_epochs=2,
        warmup_ratio=0.03,
        logging_steps=10,
        save_steps=500,
        save_total_limit=2,
        # Markov do not support these
        bf16=False,  # Disabled for CPU/older GPU compatibility
        fp16=False,  # Also disable fp16 for CPU compatibility
        gradient_checkpointing=True,
        report_to=report_to,
        eval_strategy="steps" if val_ds else "no",
        eval_steps=500 if val_ds else None,
    )

    # SFT-specific configuration
    sft_config = SFTConfig(
        packing=True,
    )

    # Train
    trainer = SFTTrainer(
        model=model,
        train_dataset=train_ds,
        args=training_args,
        sft_config=sft_config,
        formatting_func=to_messages,
        max_seq_length=2048,
    )
    trainer.train()

    # 7) Save tiny LoRA adapter + tokenizer
    adapter_dir = Path(args.out_dir) / "adapter"
    trainer.model.save_pretrained(adapter_dir.as_posix())
    tokenizer.save_pretrained(adapter_dir.as_posix())
    print(f"✅ Done. Adapter saved to: {adapter_dir}")
