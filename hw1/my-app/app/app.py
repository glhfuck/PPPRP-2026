from flask import Flask, request, jsonify
import logging
import os

app = Flask(__name__)


LOG_FILE = "./app/logs/app.log"
if not os.path.exists(os.path.dirname(LOG_FILE)):
    os.makedirs(os.path.dirname(LOG_FILE))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        # logging.StreamHandler(), В этом случае DaemonSet не нужен
    ]
)

logger = logging.getLogger("my_app")

CONFIG_MAP = {
    "PORT": os.getenv("PORT", "5003"),
    "WELCOME_HEADER": os.getenv("WELCOME_HEADER", "Welcome to the my app")
}

@app.route("/", methods=["GET"])
def home():
    logger.info(f"{CONFIG_MAP['WELCOME_HEADER']} from pod {os.environ['HOSTNAME']}\n")
    return f"{CONFIG_MAP['WELCOME_HEADER']} from pod {os.environ['HOSTNAME']}\n"

@app.route("/status", methods=["GET"])
def status():
    return jsonify({"status": "ok"})

@app.route("/log", methods=["POST"])
def log_message():
    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"error": "Invalid input"}), 400
    
    message = data["message"]
    logger.info(f"Log message: {message}")
    return jsonify({"status": "logged"}), 200

@app.route("/logs", methods=["GET"])
def get_logs():
    try:
        with open(LOG_FILE, "r") as f:
            logs = f.read()
        return "<pre>" + logs + "</pre>"
    except FileNotFoundError:
        return jsonify({"error": "Log file not found"}), 404
