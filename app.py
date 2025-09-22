from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import os
from config import MODEL_ID


# Load API key from file
def load_api_key():
    try:
        with open('.api-key', 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return "change-me"


API_KEY = load_api_key()


class GenRequest(BaseModel):
    prompt: str
    max_new_tokens: int = 64


app = FastAPI()

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, use_fast=True)
model = AutoModelForCausalLM.from_pretrained(MODEL_ID, dtype=torch.float16, device_map="auto")
model.eval()


def _auth(x_api_key: str | None):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.post("/generate")
def generate(req: GenRequest, x_api_key: str | None = Header(None)):
    _auth(x_api_key)
    inputs = tokenizer(req.prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model.generate(
            **inputs,
            max_new_tokens=req.max_new_tokens,
            do_sample=True,
            temperature=0.7,
            top_p=0.95,
        )
    text = tokenizer.decode(out[0], skip_special_tokens=True)
    return {"text": text}
