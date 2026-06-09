import time
import json
from flask import Flask, Response, request, stream_with_context


app = Flask(__name__)


@app.route("/", methods=['GET'])
def home():
    return "welcome to flask server"


@app.route("/stream", methods=['POST'])
def stream():
    # TODO 1: Change silent=True to silent=False — send a bad JSON body and watch Flask crash with a 400 error. Then change it back.
    body = request.get_json(silent=True) or {}

    # TODO 2: Remove the `or {}` part — then call /stream with no body and see what error you get. Why does it crash?
    message = body.get("message", "hello")

    # TODO 3: Remove the int() cast — then send {"count": "3"} (a string) and see what happens in the for loop below.
    count = int(body.get("count", 5))

    def event_stream():
        for i in range(1, count + 1):
            data = json.dumps({"index": i, "message": f"{message} #{i}"})

            # TODO 4: Change \n\n to just \n (single newline) — run curl and notice events never arrive. SSE requires double newline to signal end of an event.
            yield f"data: {data}\n\n"

            # TODO 5: Change 0.5 to 5 — observe how slow the stream becomes. Then try 0 — events fire instantly. What's the tradeoff?
            time.sleep(0.5)

    # TODO 6: Remove stream_with_context() and call event_stream() directly — then access `request` inside the generator and watch it crash with a RuntimeError about context.
    # TODO 7: Change mimetype to "application/json" — run curl and notice events are no longer streamed, the response is buffered until the connection closes.
    # TODO 8: Remove the Cache-Control header — open the stream in a browser, reload, and see if you get replayed events from cache.
    # TODO 9: Remove the X-Accel-Buffering header — events still work locally but will be delayed in batches if you put Nginx in front of Flask.
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
