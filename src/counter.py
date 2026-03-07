import os
import cv2
import logging
from typing import Dict, Any, List
from .tracker import TrackerWrapper
from .line_crossing import LineCrossingDetector, Direction, Orientation
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
        if not os.path.exists(video_path):
            logger.error(f"Video not found: {video_path}")
            return

        props = get_video_properties(video_path)
        width, height = props['width'], props['height']
        
        orientation_str = self.config.get('line_orientation', 'horizontal')
        self.orientation = Orientation(orientation_str)
        
        if self.orientation == Orientation.HORIZONTAL:
            self.line_coord = int(height * self.config.get('line_position', 0.5))
        else:
            self.line_coord = int(width * self.config.get('line_position', 0.5))
        
        direction = Direction(self.config.get('count_direction', 'both'))
        
        self.detector = LineCrossingDetector(
            line_coord=self.line_coord, 
            direction=direction,
            orientation=self.orientation,
            cooldown_frames=self.config.get('cooldown_frames', 30),
            line_margin=self.config.get('line_margin', 0)
        )
        self.visualizer = Visualizer(line_coord=self.line_coord, orientation=self.orientation, width=width, height=height)

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
                    classes=self.config.get('track_classes', [0, 24, 26, 28]) # person, backpack, handbag, suitcase
                )
                
                if results.boxes.id is not None:
                    boxes = results.boxes.xyxy.cpu().numpy()
                    track_ids = results.boxes.id.cpu().numpy().astype(int)
                    
                    sacks = []
                    for i in range(len(track_ids)):
                        sacks.append({'box': boxes[i], 'id': track_ids[i]})

                    # Crossing Logic for sacks
                    sack_points = []
                    for s in sacks:
                        sx1, sy1, sx2, sy2 = s['box']
                        scx, scy = (sx1 + sx2) / 2, (sy1 + sy2) / 2
                        
                        coord = scy if self.orientation == Orientation.HORIZONTAL else scx
                        sack_points.append((s['id'], coord))
                    
                    cin, cout = self.detector.update(sack_points)
                    self.count_in += cin
                    self.count_out += cout
                    
                    # Visualization data preparation
                    detection_data = []
                    for s in sacks:
                        detection_data.append({'box': s['box'], 'id': s['id'], 'color': (0, 255, 255), 'label': 'Sack'})

                    # Visualization
                    frame = self.visualizer.draw_detections(frame, detection_data)

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
        if not os.path.exists(video_path):
            logger.error(f"Video not found: {video_path}")
            return {"in": 0, "out": 0}

        props = get_video_properties(video_path)
        width, height = props['width'], props['height']
        
        orientation_str = self.config.get('line_orientation', 'horizontal')
        self.orientation = Orientation(orientation_str)
        
        if self.orientation == Orientation.HORIZONTAL:
            self.line_coord = int(height * self.config.get('line_position', 0.5))
        else:
            self.line_coord = int(width * self.config.get('line_position', 0.5))
        
        direction = Direction(self.config.get('count_direction', 'both'))
        
        self.detector = LineCrossingDetector(
            line_coord=self.line_coord, 
            direction=direction,
            orientation=self.orientation,
            cooldown_frames=self.config.get('cooldown_frames', 30),
            line_margin=self.config.get('line_margin', 0)
        )
        self.visualizer = Visualizer(line_coord=self.line_coord, orientation=self.orientation, width=width, height=height)

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
            
            # Tracking (people + bag-like classes)
            results = self.tracker.track(
                frame, 
                conf=self.config.get('confidence', 0.4),
                classes=self.config.get('track_classes', [0, 24, 26, 28])
            )
            
            if results.boxes.id is not None:
                boxes = results.boxes.xyxy.cpu().numpy()
                track_ids = results.boxes.id.cpu().numpy().astype(int)
                cls_ids = results.boxes.cls.cpu().numpy().astype(int)

                if frame_idx % 30 == 0:
                    logger.info(f"Frame {frame_idx}: Detected classes: {cls_ids}, Track IDs: {track_ids}")

                sacks = []
                for i in range(len(track_ids)):
                    if cls_ids[i] == 0:
                        sacks.append({'box': boxes[i], 'id': track_ids[i]})

                # Crossing Logic for sacks
                sack_points = []
                for s in sacks:
                    sx1, sy1, sx2, sy2 = s['box']
                    scx, scy = (sx1 + sx2) / 2, (sy1 + sy2) / 2
                    
                    coord = scy if self.orientation == Orientation.HORIZONTAL else scx
                    sack_points.append((s['id'], coord))
                
                cin, cout = self.detector.update(sack_points)
                self.count_in += cin
                self.count_out += cout
                
                # Visualization
                if writer or self.config.get('show_preview'):
                    detection_data = []
                    for s in sacks:
                        detection_data.append({'box': s['box'], 'id': s['id'], 'color': (0, 255, 255), 'label': 'Sack'})
                    
                    frame = self.visualizer.draw_detections(frame, detection_data)

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
