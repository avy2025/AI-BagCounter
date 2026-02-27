import os
import yaml
import logging
import cv2
from typing import Any, Dict

def setup_logging(level: int = logging.INFO) -> None:
    """Sets up the logging configuration."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

def load_config(config_path: str) -> Dict[str, Any]:
    """Loads a YAML configuration file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config

def get_video_properties(video_path: str) -> Dict[str, Any]:
    """Gathers basic properties of a video file."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")
    
    props = {
        "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        "fps": cap.get(cv2.CAP_PROP_FPS),
        "total_frames": int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    }
    cap.release()
    return props

def create_output_writer(video_path: str, output_path: str, fps: float, width: int, height: int) -> cv2.VideoWriter:
    """Creates a cv2.VideoWriter object for saving the output."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    return cv2.VideoWriter(output_path, fourcc, fps, (width, height))
