# Qwen3-0.6B Inference Server on RTX 5090

## What This Does

Runs Qwen3-0.6B as a streaming chat API on a Vast.ai RTX 5090 instance, accessible publicly via ngrok.

---

## Infrastructure

| Item | Value |
|---|---|
| GPU Machine | Vast.ai RTX 5090 (instance 40012089) |
| Public IP | 58.224.7.137 |
| SSH Port | 45658 |
| Server Port | 8000 |
| Model Path | `/workspace/models/Qwen3-0.6B` |

---

## Project Structure

```
quen3/
├── server/
│   ├── app.py          # FastAPI server (HuggingFace transformers backend)
│   ├── index.html      # Browser UI
│   └── pyproject.toml  # Dependencies (managed with uv)
└── qwen_megakernel/    # CUDA megakernel (Phase 3 — not yet integrated)
```

---

## How to Run

### 1. Sync local changes to GPU machine

```bash
rsync -avz -e "ssh -p 45658" \
  /Users/chandankumar/Desktop/AIEngg/quen3/server/ \
  root@58.224.7.137:/workspace/server/
```

### 2. SSH into the GPU machine

```bash
ssh -p 45658 root@58.224.7.137
```

### 3. Start the server

```bash
cd /workspace/server
uvicorn app:app --host 0.0.0.0 --port 8000
```

### 4. Expose publicly via ngrok

```bash
ngrok http 8000
```

Open the `https://xxx.ngrok-free.app` URL in your browser.

---

## API

### `POST /chat`
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is 2 + 2?"}'
```

Response is a streaming SSE (`text/event-stream`):
```
data: 2
data:  +
data:  2
data:  =
data:  4
data: [DONE]
```

### `GET /health`
```bash
curl http://localhost:8000/health
```
```json
{"status": "ok", "gpu": "NVIDIA GeForce RTX 5090", "vram_used_gb": 1.2}
```

---

## Phases

- [x] **Phase 1** — Run Qwen3-0.6B with HuggingFace transformers on RTX 5090
- [x] **Phase 2** — Expose as a FastAPI streaming server, accessible via ngrok
