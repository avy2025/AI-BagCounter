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

    def _associate_bags_to_people(self, people: List[Dict], bags: List[Dict], threshold: float = 150.0) -> List[Dict]:
        """Associates bags with the nearest person and labels them as workers."""
        for p in people:
            p['has_bag'] = False
            p['bag_ids'] = []

        associated_bags = []
        for b in bags:
            bx1, by1, bx2, by2 = b['box']
            bcx, bcy = (bx1 + bx2) / 2, (by1 + by2) / 2
            
            min_dist = float('inf')
            best_person = None
            
            for p in people:
                px1, py1, px2, py2 = p['box']
                pcx, pcy = (px1 + px2) / 2, (py1 + py2) / 2
                dist = ((bcx - pcx)**2 + (bcy - pcy)**2)**0.5
                
                if dist < min_dist and dist < threshold:
                    min_dist = dist
                    best_person = p
            
            if best_person:
                best_person['has_bag'] = True
                best_person['bag_ids'].append(b['id'])
                b['associated'] = True
                associated_bags.append(b)
            else:
                b['associated'] = False
        
        return associated_bags

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
                
                # Tracking
                results = self.tracker.track(
                    frame, 
                    conf=self.config.get('confidence', 0.4),
                    classes=self.config.get('track_classes', [0, 24, 26, 28])
                )
                
                if results.boxes.id is not None:
                    boxes = results.boxes.xyxy.cpu().numpy()
                    track_ids = results.boxes.id.cpu().numpy().astype(int)
                    cls_ids = results.boxes.cls.cpu().numpy().astype(int)
                    
                    person_classes = self.config.get('person_classes', [0])
                    bag_classes = self.config.get('bag_classes', [24, 26, 28])
                    
                    people = []
                    bags = []
                    for i in range(len(track_ids)):
                        item = {'box': boxes[i], 'id': track_ids[i]}
                        if cls_ids[i] in person_classes:
                            people.append(item)
                        if cls_ids[i] in bag_classes:
                            bags.append(item)

                    # Association
                    associated_bags = self._associate_bags_to_people(people, bags)

                    # Crossing Logic for associated bags only (higher precision)
                    sack_points = []
                    for b in associated_bags:
                        bx1, by1, bx2, by2 = b['box']
                        bcx, bcy = (bx1 + bx2) / 2, (by1 + by2) / 2
                        coord = bcy if self.orientation == Orientation.HORIZONTAL else bcx
                        sack_points.append((b['id'], coord))
                    
                    cin, cout = self.detector.update(sack_points)
                    self.count_in += cin
                    self.count_out += cout
                    
                    # Visualization data
                    detection_data = []
                    for p in people:
                        color = (0, 255, 0) if p['has_bag'] else (255, 0, 0)
                        label = "Worker (Bag)" if p['has_bag'] else "Person"
                        detection_data.append({'box': p['box'], 'id': p['id'], 'color': color, 'label': label})
                    
                    for b in bags:
                        if b['associated']:
                            detection_data.append({'box': b['box'], 'id': b['id'], 'color': (0, 255, 255), 'label': 'Sack'})

                    frame = self.visualizer.draw_detections(frame, detection_data)

                frame = self.visualizer.draw_hud(frame, self.count_in, self.count_out, frame_idx)
                
                ret, buffer = cv2.imencode('.jpg', frame)
                if not ret:
                    continue
                
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        finally:
            cap.release()

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
            
            results = self.tracker.track(
                frame, 
                conf=self.config.get('confidence', 0.4),
                classes=self.config.get('track_classes', [0, 24, 26, 28])
            )
            
            if results.boxes.id is not None:
                boxes = results.boxes.xyxy.cpu().numpy()
                track_ids = results.boxes.id.cpu().numpy().astype(int)
                cls_ids = results.boxes.cls.cpu().numpy().astype(int)

                person_classes = self.config.get('person_classes', [0])
                bag_classes = self.config.get('bag_classes', [24, 26, 28])

                people = []
                bags = []
                for i in range(len(track_ids)):
                    item = {'box': boxes[i], 'id': track_ids[i]}
                    if cls_ids[i] in person_classes:
                        people.append(item)
                    if cls_ids[i] in bag_classes:
                        bags.append(item)

                associated_bags = self._associate_bags_to_people(people, bags)

                sack_points = []
                for b in associated_bags:
                    bx1, by1, bx2, by2 = b['box']
                    bcx, bcy = (bx1 + bx2) / 2, (by1 + by2) / 2
                    coord = bcy if self.orientation == Orientation.HORIZONTAL else bcx
                    sack_points.append((b['id'], coord))
                
                cin, cout = self.detector.update(sack_points)
                self.count_in += cin
                self.count_out += cout
                
                if writer or self.config.get('show_preview'):
                    detection_data = []
                    for p in people:
                        color = (0, 255, 0) if p['has_bag'] else (255, 0, 0)
                        label = "Worker (Bag)" if p['has_bag'] else "Person"
                        detection_data.append({'box': p['box'], 'id': p['id'], 'color': color, 'label': label})
                    
                    for b in bags:
                        if b['associated']:
                            detection_data.append({'box': b['box'], 'id': b['id'], 'color': (0, 255, 255), 'label': 'Sack'})
                    
                    frame = self.visualizer.draw_detections(frame, detection_data)

            if writer or self.config.get('show_preview'):
                frame = self.visualizer.draw_hud(frame, self.count_in, self.count_out, frame_idx)
                if writer:
                    writer.write(frame)
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
