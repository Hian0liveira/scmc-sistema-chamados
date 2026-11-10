from pathlib import Path
from flask import Flask, jsonify, send_file

BASE_DIR = Path(__file__).resolve().parent
APP_FILE = BASE_DIR / "cyrex-preview" / "index.html"
app = Flask(__name__, static_folder=None)


@app.get("/")
def cyrex_home():
    return send_file(APP_FILE)


@app.get("/health")
def health():
    return jsonify(status="ok", app="Cyrex - Suporte")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
