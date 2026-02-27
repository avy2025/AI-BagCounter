import cv2
import logging
from typing import Dict, Any, List
from .tracker import TrackerWrapper
from .line_crossing import LineCrossingDetector, Direction
from .visualizer import Visualizer
from .utils import get_video_properties, create_output_writer

logger = logging.getLogger(__name__)

class BagCounter:
    """Main class to orchestrate the bag counting process."""
    
    def __init__(self, config: Dict[str, Any], model: Any = None):
        self.config = config
        self.tracker = TrackerWrapper(model_path_or_model=model if model else config.get('model', 'yolov8n.pt'))
        self.detector = None
        self.visualizer = None
        self.reset()

    def reset(self) -> None:
        """Resets the counting state."""
        self.count_in = 0
        self.count_out = 0
        if self.detector:
            self.detector.tracks_history.clear()
            self.detector.tracks_cooldown.clear()

    def stream_video(self, video_path: str):
        """Generator that yields processed video frames as JPEG bytes."""
        if not cv2.os.path.exists(video_path):
            logger.error(f"Video not found: {video_path}")
            return

        props = get_video_properties(video_path)
        width, height = props['width'], props['height']
        
        line_x = int(width * self.config.get('line_position', 0.5))
        direction = Direction(self.config.get('count_direction', 'both'))
        
        self.detector = LineCrossingDetector(
            line_x=line_x, 
            direction=direction,
            cooldown_frames=self.config.get('cooldown_frames', 30)
        )
        self.visualizer = Visualizer(line_x=line_x, height=height)

        cap = cv2.VideoCapture(video_path)
        frame_idx = 0
        
        try:
            while cap.isOpened():
                success, frame = cap.read()
                if not success:
                    break
                
                frame_idx += 1
                
                # Tracking (persist=True is handled in TrackerWrapper)
                results = self.tracker.track(
                    frame, 
                    conf=self.config.get('confidence', 0.4),
                    classes=self.config.get('track_classes', [0])
                )
                
                if results.boxes.id is not None:
                    boxes = results.boxes.xyxy.cpu().numpy()
                    track_ids = results.boxes.id.cpu().numpy().astype(int)
                    
                    # Crossing Logic
                    centers = []
                    for box, track_id in zip(boxes, track_ids):
                        cx = (box[0] + box[2]) / 2
                        centers.append((track_id, cx))
                    
                    cin, cout = self.detector.update(centers)
                    self.count_in += cin
                    self.count_out += cout
                    
                    # Visualization
                    frame = self.visualizer.draw_detections(frame, boxes, track_ids)

                # HUD
                frame = self.visualizer.draw_hud(frame, self.count_in, self.count_out, frame_idx)
                
                # Encode to JPEG
                ret, buffer = cv2.imencode('.jpg', frame)
                if not ret:
                    continue
                
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        finally:
            cap.release()
            logger.info(f"Stream released for {video_path}")

    def process_video(self, video_path: str, output_path: str = None) -> Dict[str, int]:
        """Processes a video file and counts bag crossings."""
        if not cv2.os.path.exists(video_path):
            logger.error(f"Video not found: {video_path}")
            return {"in": 0, "out": 0}

        props = get_video_properties(video_path)
        width, height = props['width'], props['height']
        
        line_x = int(width * self.config.get('line_position', 0.5))
        direction = Direction(self.config.get('count_direction', 'both'))
        
        self.detector = LineCrossingDetector(
            line_x=line_x, 
            direction=direction,
            cooldown_frames=self.config.get('cooldown_frames', 30)
        )
        self.visualizer = Visualizer(line_x=line_x, height=height)

        cap = cv2.VideoCapture(video_path)
        writer = None
        if output_path:
            writer = create_output_writer(video_path, output_path, props['fps'], width, height)

        frame_idx = 0
        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                break
            
            frame_idx += 1
            
            # Tracking
            results = self.tracker.track(
                frame, 
                conf=self.config.get('confidence', 0.4),
                classes=self.config.get('track_classes', [0])
            )
            
            if results.boxes.id is not None:
                boxes = results.boxes.xyxy.cpu().numpy()
                track_ids = results.boxes.id.cpu().numpy().astype(int)
                
                # Crossing Logic
                centers = []
                for box, track_id in zip(boxes, track_ids):
                    cx = (box[0] + box[2]) / 2
                    centers.append((track_id, cx))
                
                cin, cout = self.detector.update(centers)
                self.count_in += cin
                self.count_out += cout
                
                # Visualization
                if writer or self.config.get('show_preview'):
                    frame = self.visualizer.draw_detections(frame, boxes, track_ids)

            # HUD
            if writer or self.config.get('show_preview'):
                frame = self.visualizer.draw_hud(frame, self.count_in, self.count_out, frame_idx)
                
                if writer:
                    if not writer.isOpened():
                         logger.error(f"VideoWriter not opened for {output_path}")
                    success_write = writer.write(frame)
                    if not success_write:
                        # writer.write doesn't return anything in some versions, but we check if we can
                        pass

                
                if self.config.get('show_preview'):
                    cv2.imshow("AI-BagCounter", frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break

        cap.release()
        if writer:
            writer.release()
        cv2.destroyAllWindows()
        
        logger.info(f"Processing complete for {video_path}. IN: {self.count_in}, OUT: {self.count_out}")
        return {"in": self.count_in, "out": self.count_out}
