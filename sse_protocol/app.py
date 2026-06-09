import time
import json
from flask import Flask, Response, request, stream_with_context


app = Flask(__name__)


@app.route("/", methods=['GET'])
def home():
    return "welcome to flask server"


@app.route("/stream", methods=['POST'])
def stream():
    body = request.get_json(silent=True) or {}
    message = body.get("message", "hello")
    count = int(body.get("count", 5))

    def event_stream():
        for i in range(1, count + 1):
            data = json.dumps({"index": i, "message": f"{message} #{i}"})
            yield f"data: {data}\n\n"
            time.sleep(0.5)
        yield "data: {\"done\": true}\n\n"

    return Response(
        stream_with_context(event_stream()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


if __name__ == '__main__':
    app.run(debug=True, port=5001)
