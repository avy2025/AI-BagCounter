import os
import logging
from flask import Flask, render_template, Response, jsonify, request
from src.counter import BagCounter
from src.utils import load_config, setup_logging
from ultralytics import YOLO

# Initialize
setup_logging()
logger = logging.getLogger("flask_webapp")
app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = BASE_DIR
MODEL_PATH = os.path.join(MODELS_DIR, "yolov8n.pt")

# 1. Load YOLO Model ONLY ONCE at startup
logger.info(f"Loading YOLO model from {MODEL_PATH}...")
shared_model = YOLO(MODEL_PATH)

# Scenario Mapping
SCENARIOS = {
    "1": {"video": "Problem Statement Scenario1.mp4", "config": "config/scenario1_config.yaml", "title": "Scenario 1: Main Entrance"},
    "2": {"video": "Problem Statement Scenario2.mp4", "config": "config/scenario2_config.yaml", "title": "Scenario 2: Loading Platform"},
    "3": {"video": "Problem Statement Scenario3.mp4", "config": "config/scenario3_config.yaml", "title": "Scenario 3: Busy Corridor"}
}

# Global counter instance (or per request if preferred, but user implies persist)
# We recreate it per scenario to reset state
active_counter = None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/scenarios")
def get_scenarios():
    return jsonify([{"id": k, **v} for k, v in SCENARIOS.items()])

def gen_frames(scenario_id):
    global active_counter
    if scenario_id not in SCENARIOS:
        return
    
    scenario = SCENARIOS[scenario_id]
    video_path = os.path.join(BASE_DIR, scenario["video"])
    config_path = os.path.join(BASE_DIR, scenario["config"])
    
    if not os.path.exists(video_path):
        logger.error(f"Video file {scenario['video']} not found")
        return

    # Load config and initialize/reset counter
    config = load_config(config_path)
    active_counter = BagCounter(config, model=shared_model)
    active_counter.reset()
    
    logger.info(f"Started streaming scenario {scenario_id}")
    yield from active_counter.stream_video(video_path)

@app.route("/video_feed/<scenario_id>")
def video_feed(scenario_id):
    """Video streaming route. Put this in the src attribute of an img tag."""
    # Add timestamp/cache-buster check if needed here, but usually handled in frontend
    return Response(gen_frames(scenario_id),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/api/counts")
def get_counts():
    if active_counter:
        return jsonify({
            "in": active_counter.count_in,
            "out": active_counter.count_out,
            "total": active_counter.count_in + active_counter.count_out
        })
    return jsonify({"in": 0, "out": 0, "total": 0})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False, threaded=True)
