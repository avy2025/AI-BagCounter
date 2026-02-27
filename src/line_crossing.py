from enum import Enum
from typing import Dict, List, Tuple

class Direction(Enum):
    LEFT_TO_RIGHT = "left_to_right"
    RIGHT_TO_LEFT = "right_to_left"
    BOTH = "both"

class LineCrossingDetector:
    """Detects if tracked objects cross a vertical virtual line."""
    
    def __init__(self, line_x: int, direction: Direction, cooldown_frames: int = 30):
        self.line_x = line_x
        self.direction = direction
        self.cooldown_frames = cooldown_frames
        self.tracks_history: Dict[int, List[float]] = {}  # {track_id: [prev_x]}
        self.tracks_cooldown: Dict[int, int] = {}       # {track_id: cooldown_remaining}

    def update(self, tracks: List[Tuple[int, float]]) -> Tuple[int, int]:
        """
        Updates the detector with current frame tracks.
        tracks: List of (track_id, center_x)
        Returns: (count_in, count_out)
        """
        count_in = 0
        count_out = 0
        
        # Update cooldowns
        for track_id in list(self.tracks_cooldown.keys()):
            self.tracks_cooldown[track_id] -= 1
            if self.tracks_cooldown[track_id] <= 0:
                del self.tracks_cooldown[track_id]

        for track_id, curr_x in tracks:
            if track_id in self.tracks_history:
                prev_x = self.tracks_history[track_id]
                
                # Check for crossing
                if track_id not in self.tracks_cooldown:
                    # Left to Right: prev_x < line_x and curr_x >= line_x
                    if prev_x < self.line_x <= curr_x:
                        if self.direction in [Direction.LEFT_TO_RIGHT, Direction.BOTH]:
                            count_in += 1
                            self.tracks_cooldown[track_id] = self.cooldown_frames
                    
                    # Right to Left: prev_x > line_x and curr_x <= line_x
                    elif prev_x > self.line_x >= curr_x:
                        if self.direction in [Direction.RIGHT_TO_LEFT, Direction.BOTH]:
                            count_out += 1
                            self.tracks_cooldown[track_id] = self.cooldown_frames
                
            self.tracks_history[track_id] = curr_x
            
        return count_in, count_out
