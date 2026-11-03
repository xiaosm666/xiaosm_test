from flask import Flask, request, jsonify

app = Flask(__name__)


@app.get("/host")
def show_host():
    return jsonify({
        "host": request.host,
        "url": request.url,
        "scheme": request.scheme
    })


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=8137,
        debug=False
    )