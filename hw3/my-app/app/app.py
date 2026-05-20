from flask import Flask, request, jsonify
import logging
import os
import time
import random
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

LOG_REQUEST_COUNT = Counter("log_request_count", "Total number of api/log requests")
SUCCESS_LOG_REQUEST_COUNT = Counter("success_log_request_count", "Total number of successful api/log requests")
FAILED_LOG_REQUEST_COUNT = Counter("failed_log_request_count", "Total number of failed api/log requests")
LOG_REQUEST_DURATION = Histogram("log_request_duration_milliseconds", "Duration of api/log requests")


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

@app.route("/api", methods=["GET"])
def home():
    logger.info(f"{CONFIG_MAP["WELCOME_HEADER"]} from pod {os.environ['HOSTNAME']}\n")
    return f"{CONFIG_MAP["WELCOME_HEADER"]} from pod {os.environ['HOSTNAME']}\n"

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

@app.route("/api/log/delayed", methods=["POST"])
def log_message_delayed():
    LOG_REQUEST_COUNT.inc()

    delay = random.randint(1, 5)
    start_time = time.time()
    time.sleep(delay)
    LOG_REQUEST_DURATION.observe(time.time() - start_time)

    if random.random() < 0.3:
        FAILED_LOG_REQUEST_COUNT.inc()
        return jsonify({"state": "failed"}), 500
    
    SUCCESS_LOG_REQUEST_COUNT.inc()
    return jsonify({"state": "success"}), 200

@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

@app.route("/api/logs", methods=["GET"])
def get_logs():
    try:
        with open(LOG_FILE, "r") as f:
            logs = f.read()
        return "<pre>" + logs + "</pre>"
    except FileNotFoundError:
        return jsonify({"error": "Log file not found"}), 404
