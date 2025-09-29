from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
import torch

class LoRAChatModel:
    def __init__(self, base_model: str, adapter_dir: str, system_instruction: str,
                 dtype=torch.float32, device="auto"):
        """
        base_model: same base model used for training
        adapter_dir: path to your saved LoRA adapter (the folder with adapter_config.json)
        system_instruction: the fixed system prompt you used for fine-tuning
        """
        self.tokenizer = AutoTokenizer.from_pretrained(base_model)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        base = AutoModelForCausalLM.from_pretrained(base_model,
                                                   torch_dtype=dtype,
                                                   device_map=device)
        self.model = PeftModel.from_pretrained(base, adapter_dir).eval()
        self.system_instruction = system_instruction

    def query(self, user_text: str, max_new_tokens: int = 256,
              temperature: float = 0.0, do_sample: bool = False) -> str:
        """
        Run the fine-tuned model on a custom input.
        """
        messages = [
            {"role":"system","content":self.system_instruction},
            {"role":"user","content":user_text},
        ]
        prompt = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)

        with torch.no_grad():
            out = self.model.generate(**inputs,
                                      max_new_tokens=max_new_tokens,
                                      temperature=temperature,
                                      do_sample=do_sample)
        return self.tokenizer.decode(out[0], skip_special_tokens=True)
