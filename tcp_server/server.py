from flask import Flask, request, jsonify

app = Flask(__name__)

@app.get("/")
def home():
    return jsonify({"status": 200})

@app.post("/echo")
def echo():
    data = request.get_json()
    return jsonify(data)

if __name__ == "__main__":
    app.run()
