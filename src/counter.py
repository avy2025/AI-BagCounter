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
        # Focus region (relative Y) to prioritize closest truck / loading area
        roi_y_min = int(height * self.config.get('roi_y_min', 0.0))
        roi_y_max = int(height * self.config.get('roi_y_max', 1.0))
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
                    classes=self.config.get('track_classes', [0, 24, 26, 28]) # person, backpack, handbag, suitcase
                )
                
                if results.boxes.id is not None:
                    boxes = results.boxes.xyxy.cpu().numpy()
                    track_ids = results.boxes.id.cpu().numpy().astype(int)
                    cls_ids = results.boxes.cls.cpu().numpy().astype(int)
                    
                    # Separate people and bags
                    people = []
                    bags = []
                    for i in range(len(track_ids)):
                        if cls_ids[i] == 0:
                            people.append({'box': boxes[i], 'id': track_ids[i]})
                        else:
                            bags.append({'box': boxes[i], 'id': track_ids[i]})

                    # Association logic: Person with bag
                    # We mark person IDs that have a bag nearby
                    people_with_bags = set()
                    for p in people:
                        px1, py1, px2, py2 = p['box']
                        pcx, pcy = (px1 + px2) / 2, (py1 + py2) / 2
                        for b in bags:
                            bx1, by1, bx2, by2 = b['box']
                            bcx, bcy = (bx1 + bx2) / 2, (by1 + by2) / 2
                            # Euclidean distance between centers
                            dist = ((pcx - bcx)**2 + (pcy - bcy)**2)**0.5
                            # If bag is "within" the person's bounding box or very close
                            if dist < (px2 - px1) * 0.8: 
                                people_with_bags.add(p['id'])
                                break

                    # Crossing Logic:
                    # Use workers as a proxy for sacks, restricted to the closest-truck ROI.
                    person_centers = []
                    for p in people:
                        px1, py1, px2, py2 = p['box']
                        pcx, pcy = (px1 + px2) / 2, (py1 + py2) / 2
                        if roi_y_min <= pcy <= roi_y_max:
                            person_centers.append((p['id'], pcx))
                    
                    cin, cout = self.detector.update(person_centers)
                    # Track both directions; scenario config defines which flow is "into truck".
                    self.count_in += cin
                    self.count_out += cout
                    
                    # Visualization data preparation
                    detection_data = []
                    for p in people:
                        color = (0, 255, 0) if p['id'] in people_with_bags else (255, 0, 0) # Green if has bag, Blue otherwise
                        detection_data.append({'box': p['box'], 'id': p['id'], 'color': color, 'label': 'Person'})
                    
                    for b in bags:
                        detection_data.append({'box': b['box'], 'id': b['id'], 'color': (0, 255, 255), 'label': 'Bag'}) # Yellow for bags

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
        if not cv2.os.path.exists(video_path):
            logger.error(f"Video not found: {video_path}")
            return {"in": 0, "out": 0}

        props = get_video_properties(video_path)
        width, height = props['width'], props['height']
        
        line_x = int(width * self.config.get('line_position', 0.5))
        # Focus region (relative Y) to prioritize closest truck / loading area
        roi_y_min = int(height * self.config.get('roi_y_min', 0.0))
        roi_y_max = int(height * self.config.get('roi_y_max', 1.0))
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

                # Separate people and bags
                people = []
                bags = []
                for i in range(len(track_ids)):
                    if cls_ids[i] == 0:
                        people.append({'box': boxes[i], 'id': track_ids[i]})
                    else:
                        bags.append({'box': boxes[i], 'id': track_ids[i]})

                # Association logic
                people_with_bags = set()
                for p in people:
                    px1, py1, px2, py2 = p['box']
                    pcx, pcy = (px1 + px2) / 2, (py1 + py2) / 2
                    for b in bags:
                        bx1, by1, bx2, by2 = b['box']
                        bcx, bcy = (bx1 + bx2) / 2, (by1 + by2) / 2
                        dist = ((pcx - bcx)**2 + (pcy - bcy)**2)**0.5
                        if dist < (px2 - px1) * 0.8:
                            people_with_bags.add(p['id'])
                            break

                # Crossing Logic:
                # Use workers as a proxy for sacks, restricted to the closest-truck ROI.
                person_centers = []
                for p in people:
                    px1, py1, px2, py2 = p['box']
                    pcx, pcy = (px1 + px2) / 2, (py1 + py2) / 2
                    if roi_y_min <= pcy <= roi_y_max:
                        person_centers.append((p['id'], pcx))
                
                cin, cout = self.detector.update(person_centers)
                self.count_in += cin
                self.count_out += cout
                
                # Visualization
                if writer or self.config.get('show_preview'):
                    detection_data = []
                    for p in people:
                        color = (0, 255, 0) if p['id'] in people_with_bags else (255, 0, 0)
                        detection_data.append({'box': p['box'], 'id': p['id'], 'color': color, 'label': 'Person'})
                    for b in bags:
                        detection_data.append({'box': b['box'], 'id': b['id'], 'color': (0, 255, 255), 'label': 'Bag'})
                    
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
