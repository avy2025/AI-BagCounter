import logging
from enum import Enum
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

class Direction(Enum):
    # For Horizontal Orientation (Vertical movement)
    TOP_TO_BOTTOM = "top_to_bottom"
    BOTTOM_TO_TOP = "bottom_to_top"
    # For Vertical Orientation (Horizontal movement)
    LEFT_TO_RIGHT = "left_to_right"
    RIGHT_TO_LEFT = "right_to_left"
    BOTH = "both"

class Orientation(Enum):
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"

class LineCrossingDetector:
    """Detects if tracked objects cross a virtual line (horizontal or vertical)."""
    
    def __init__(self, line_coord: int, direction: Direction, orientation: Orientation, cooldown_frames: int = 30, line_margin: int = 0):
        self.line_coord = line_coord
        self.direction = direction
        self.orientation = orientation
        self.cooldown_frames = cooldown_frames
        self.line_margin = line_margin  # pixels: require clear crossing to reduce jitter
        self.tracks_history: Dict[int, float] = {}
        self.tracks_cooldown: Dict[int, int] = {}

    def update(self, tracks: List[Tuple[int, float]]) -> Tuple[int, int]:
        """
        Updates the detector with current frame tracks.
        tracks: List of (track_id, center_coord)
        Returns: (count_in, count_out)
        """
        count_in = 0
        count_out = 0
        m = self.line_margin
        
        for track_id in list(self.tracks_cooldown.keys()):
            self.tracks_cooldown[track_id] -= 1
            if self.tracks_cooldown[track_id] <= 0:
                del self.tracks_cooldown[track_id]

        for track_id, curr_coord in tracks:
            if track_id in self.tracks_history:
                prev_coord = self.tracks_history[track_id]
                
                if track_id not in self.tracks_cooldown:
                    # Generic crossing logic
                    if prev_coord <= self.line_coord - m and curr_coord >= self.line_coord + m:
                        # Top-to-Bottom OR Left-to-Right
                        if self.direction in [Direction.TOP_TO_BOTTOM, Direction.LEFT_TO_RIGHT, Direction.BOTH]:
                            count_in += 1
                            self.tracks_cooldown[track_id] = self.cooldown_frames
                    
                    elif prev_coord >= self.line_coord + m and curr_coord <= self.line_coord - m:
                        # Bottom-to-Top OR Right-to-Left
                        if self.direction in [Direction.BOTTOM_TO_TOP, Direction.RIGHT_TO_LEFT, Direction.BOTH]:
                            count_out += 1
                            self.tracks_cooldown[track_id] = self.cooldown_frames
                
            self.tracks_history[track_id] = curr_coord
            
        return count_in, count_out
