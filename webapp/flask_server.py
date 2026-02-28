import os
import logging
import sys
from flask import Flask, render_template, Response, jsonify, request, send_file

# Add parent directory to sys.path so we can import 'src'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

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
    "1": {"video": "data/samples/Problem Statement Scenario1.mp4", "config": "config/scenario1_config.yaml", "title": "Scenario 1: Main Entrance"},
    "2": {"video": "data/samples/Problem Statement Scenario2.mp4", "config": "config/scenario2_config.yaml", "title": "Scenario 2: Loading Platform"},
    "3": {"video": "data/samples/Problem Statement Scenario3.mp4", "config": "config/scenario3_config.yaml", "title": "Scenario 3: Busy Corridor"}
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


@app.route("/download/<scenario_id>")
def download_processed_video(scenario_id):
    """
    Generate and return an annotated MP4 for the given scenario.
    This reuses the BagCounter.process_video pipeline on the server side.
    """
    if scenario_id not in SCENARIOS:
        return jsonify({"error": "Unknown scenario"}), 404

    scenario = SCENARIOS[scenario_id]
    video_path = os.path.join(BASE_DIR, scenario["video"])
    config_path = os.path.join(BASE_DIR, scenario["config"])

    if not os.path.exists(video_path):
        logger.error(f"Video file {scenario['video']} not found for download")
        return jsonify({"error": "Video file not found on server"}), 404

    # Load config and run offline processing to produce an annotated MP4
    config = load_config(config_path)
    counter = BagCounter(config, model=shared_model)

    video_name = os.path.basename(video_path)
    output_dir = os.path.join(BASE_DIR, config.get("output_dir", "outputs"))
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"annotated_{video_name}")

    logger.info(f"Generating annotated video for download: {output_path}")
    counter.process_video(video_path, output_path)

    if not os.path.exists(output_path):
        logger.error(f"Expected output video not found at {output_path}")
        return jsonify({"error": "Failed to generate output video"}), 500

    return send_file(
        output_path,
        as_attachment=True,
        download_name=os.path.basename(output_path),
        mimetype="video/mp4",
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False, threaded=True)
