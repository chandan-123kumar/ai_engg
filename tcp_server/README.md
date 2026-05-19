# Flask API (minimal)

Quick steps to run the API locally.

1. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the server

```bash
python server.py
```

4. Test the API (examples)

Create an item:

```bash
curl -s -X POST http://127.0.0.1:5000/items -H "Content-Type: application/json" -d '{"name":"example"}' | jq
```

List items:

```bash
curl -s http://127.0.0.1:5000/items | jq
```

Get item by id (replace 1 with actual id):

```bash
curl -s http://127.0.0.1:5000/items/1 | jq
```
