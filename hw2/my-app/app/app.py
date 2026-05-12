from flask import Flask, request, jsonify
import logging
import os
import time

app = Flask(__name__)

LOG_FILE = "./app/logs/app.log"
if not os.path.exists(os.path.dirname(LOG_FILE)):
    os.makedirs(os.path.dirname(LOG_FILE))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
    ]
)

logger = logging.getLogger("my_app")

CONFIG_MAP = {
    "PORT": os.getenv("PORT", "5003"),
    "WELCOME_HEADER": os.getenv("WELCOME_HEADER", "Welcome to the my app")
}

@app.route("/api", methods=["GET"])
def home():
    logger.info(f"{CONFIG_MAP['WELCOME_HEADER']} from pod {os.environ['HOSTNAME']}\n")
    return f"{CONFIG_MAP['WELCOME_HEADER']} from pod {os.environ['HOSTNAME']}\n"

@app.route("/api/status", methods=["GET"])
def status():
    return jsonify({"status": "ok"})

@app.route("/api/log", methods=["POST"])
def log_message():
    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"error": "Invalid input"}), 400

    message = data["message"]
    logger.info(f"Log message: {message}")
    return jsonify({"status": "logged"}), 200

# Эндпоинт для тестирования таймаутов Istio
@app.route("/api/log/delayed", methods=["POST"])
def sleep_demo():
    time.sleep(5)
    return f"Slept for 5 seconds"

@app.route("/api/logs", methods=["GET"])
def get_logs():
    try:
        with open(LOG_FILE, "r") as f:
            logs = f.read()
        return "<pre>" + logs + "</pre>"
    except FileNotFoundError:
        return jsonify({"error": "Log file not found"}), 404
