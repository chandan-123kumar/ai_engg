"""
FastAPI streaming chat server backed by Qwen3-0.6B on RTX 5090.
Run: uvicorn app:app --host 0.0.0.0 --port 8000
"""
import torch
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, HTMLResponse
from pydantic import BaseModel
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer

app = FastAPI()

MODEL_PATH = "/workspace/models/Qwen3-0.6B"

print(f"Loading model from {MODEL_PATH}...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    torch_dtype=torch.bfloat16,
    device_map="cuda",
)
print("Model ready!")


class ChatRequest(BaseModel):
    prompt: str
    max_tokens: int = 200


def build_input_ids(prompt: str) -> torch.Tensor:
    messages = [
        {"role": "system", "content": "You are a helpful assistant. Be concise."},
        {"role": "user", "content": prompt},
    ]
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False,
    )
    return tokenizer.encode(text, return_tensors="pt").to("cuda")


def stream_response(prompt: str, max_tokens: int):
    input_ids = build_input_ids(prompt)
    generated = input_ids
    eos_ids = {tokenizer.eos_token_id, 151645, 151643, 151644}

    for _ in range(max_tokens):
        with torch.no_grad():
            output = model(generated)
        next_token_id = int(output.logits[0, -1].argmax())

        if next_token_id in eos_ids:
            break

        text = tokenizer.decode([next_token_id], skip_special_tokens=True)
        yield f"data: {text}\n\n"

        generated = torch.cat(
            [generated, torch.tensor([[next_token_id]], device="cuda")], dim=1
        )

    yield "data: [DONE]\n\n"


@app.post("/chat")
async def chat(req: ChatRequest):
    return StreamingResponse(
        stream_response(req.prompt, req.max_tokens),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "gpu": torch.cuda.get_device_name(0),
        "vram_used_gb": round(torch.cuda.memory_allocated() / 1e9, 2),
    }


@app.get("/", response_class=HTMLResponse)
async def index():
    html_path = Path(__file__).parent / "index.html"
    if html_path.exists():
        return html_path.read_text()
    return "<h1>Qwen3 Server</h1><p>POST /chat with {\"prompt\": \"hello\"}</p>"
