# SSE Protocol — Flask Server-Sent Events Demo

A minimal Flask server demonstrating **Server-Sent Events (SSE)** over a POST endpoint.

---

## What is SSE?

**Server-Sent Events (SSE)** is a web standard that lets a server push real-time updates to a client over a single, long-lived HTTP connection. Unlike WebSockets, SSE is:

- **One-directional** — server pushes to client only
- **Built on plain HTTP** — works through proxies and firewalls
- **Text-based** — each event is a line starting with `data:`
- **Simple to implement** — no special protocol handshake needed

Each SSE message follows this format:
```
data: <your payload here>

```
The blank line after `data:` signals the end of one event.

---

## Project Structure

```
sse_protocol/
├── app.py          # Flask server with SSE endpoint
├── main.py         # Entry point placeholder
├── pyproject.toml  # Project dependencies
└── README.md       # This file
```

---

## Key Concepts in `app.py`

### `stream_with_context`

Flask processes requests inside an application context. When you use a generator to stream a response, that context can be torn down before the generator finishes yielding. `stream_with_context` wraps the generator so the Flask app context stays alive for the entire duration of the stream — without it, accessing `request`, `g`, or `current_app` inside the generator would raise a runtime error.

```python
return Response(
    stream_with_context(event_stream()),  # keeps context alive
    mimetype="text/event-stream",
)
```

### `Response` with `mimetype="text/event-stream"`

Setting the MIME type to `text/event-stream` tells the client (browser or curl) that this is an SSE stream, not a regular HTTP response. The client will read events line by line as they arrive rather than waiting for the full response to finish.

### `Cache-Control: no-cache`

Prevents proxies and browsers from caching the stream. Without this, intermediary caches might buffer the entire response before forwarding it, breaking the real-time behaviour.

### `X-Accel-Buffering: no`

Tells Nginx (if used as a reverse proxy) to disable its response buffering for this route. Nginx buffers responses by default, which would delay SSE events from reaching the client.

### `time.sleep(0.5)`

Simulates a delay between events — in a real app this would be replaced by actual work (e.g. reading from a queue, processing a file, calling an LLM API).

---

## Running the Server

```bash
uv run python app.py
```

The server starts on `http://localhost:5001`.

---

## API Reference

### `GET /`

Health check — returns a plain text welcome message.

```bash
curl http://localhost:5001/
```

---

### `POST /stream`

Streams SSE events back to the caller.

**Request body (JSON):**

| Field     | Type   | Default   | Description                          |
|-----------|--------|-----------|--------------------------------------|
| `message` | string | `"hello"` | Text included in each streamed event |
| `count`   | int    | `5`       | Number of events to emit             |

**Response:** `text/event-stream` — one event per interval, ending with `{"done": true}`.

---

## curl Examples

### Basic call with defaults

```bash
curl -X POST http://localhost:5001/stream \
  -H "Content-Type: application/json" \
  -d '{}' \
  --no-buffer
```

`--no-buffer` tells curl to print output as it arrives instead of waiting for the connection to close.

---

### Custom message and count

```bash
curl -X POST http://localhost:5001/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "ping", "count": 10}' \
  --no-buffer
```

---

### Pretty-print each SSE event with jq

```bash
curl -sX POST http://localhost:5001/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "event", "count": 3}' \
  --no-buffer \
  | grep "^data:" \
  | sed 's/^data: //' \
  | while read line; do echo "$line" | jq .; done
```

---

### Save the stream to a file

```bash
curl -X POST http://localhost:5001/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "log", "count": 5}' \
  --no-buffer \
  -o stream_output.txt
```

---

## JavaScript Example

```js
const response = await fetch("http://localhost:5001/stream", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ message: "ping", count: 5 }),
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { value, done } = await reader.read();
  if (done) break;

  const text = decoder.decode(value);
  // Each chunk looks like: "data: {...}\n\n"
  for (const line of text.split("\n")) {
    if (line.startsWith("data: ")) {
      const event = JSON.parse(line.slice(6));
      console.log(event);
    }
  }
}
```

---

## Expected Output

```
data: {"index": 1, "message": "ping #1"}

data: {"index": 2, "message": "ping #2"}

data: {"index": 3, "message": "ping #3"}

data: {"done": true}
```
