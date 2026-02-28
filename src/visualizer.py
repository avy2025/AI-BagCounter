import cv2
import numpy as np
from typing import Any, List, Tuple, Dict

class Visualizer:
    """Handles drawing of HUD, bounding boxes, and counting line."""
    
    def __init__(self, line_x: int, height: int):
        self.line_x = line_x
        self.height = height

    def draw_hud(self, frame: Any, count_in: int, count_out: int, frame_idx: int) -> Any:
        """Draws the counting line and HUD overlay."""
        # Draw counting line
        cv2.line(frame, (self.line_x, 0), (self.line_x, self.height), (0, 0, 255), 3)
        
        # HUD Background
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (250, 140), (0, 0, 0), -1)
        alpha = 0.6
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
        
        # HUD Text
        cv2.putText(frame, f"Frame: {frame_idx}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(frame, f"IN: {count_in}", (20, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.putText(frame, f"OUT: {count_out}", (20, 105), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        cv2.putText(frame, f"TOTAL: {count_in + count_out}", (20, 135), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        
        return frame

    def draw_detections(self, frame: Any, detection_data: List[Dict[str, Any]]) -> Any:
        """
        Draws bounding boxes and track IDs with custom colors.
        detection_data: List of {'box': [x1, y1, x2, y2], 'id': int, 'color': tuple, 'label': str}
        """
        for data in detection_data:
            box = data['box']
            track_id = data['id']
            color = data['color']
            label = data.get('label', 'Object')
            
            x1, y1, x2, y2 = map(int, box)
            # Draw box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            # Draw ID and Label
            cv2.putText(frame, f"{label} ID: {track_id}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            # Draw center point
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
            cv2.circle(frame, (cx, cy), 5, color, -1)
            
        return frame
