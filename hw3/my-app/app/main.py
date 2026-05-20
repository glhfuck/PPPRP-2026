from app import *

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(CONFIG_MAP["PORT"]))