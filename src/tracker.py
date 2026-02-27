from ultralytics import YOLO
from typing import List, Any

class TrackerWrapper:
    """Wrapper for YOLOv8 ByteTrack tracking."""
    
    def __init__(self, model_path_or_model: Any = "yolov8n.pt"):
        if isinstance(model_path_or_model, str):
            self.model = YOLO(model_path_or_model)
        else:
            self.model = model_path_or_model

    def track(self, frame: Any, conf: float = 0.4, classes: List[int] = [0]) -> Any:
        """Runs tracking on a single frame."""
        results = self.model.track(
            frame, 
            persist=True, 
            conf=conf, 
            classes=classes, 
            tracker="bytetrack.yaml",
            verbose=False
        )
        return results[0]
