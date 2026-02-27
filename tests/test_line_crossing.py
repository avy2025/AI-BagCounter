import pytest
from src.line_crossing import LineCrossingDetector, Direction

def test_line_crossing_left_to_right():
    detector = LineCrossingDetector(line_x=100, direction=Direction.LEFT_TO_RIGHT, cooldown_frames=0)
    
    # Move from 90 to 110 (Crossing L->R)
    cin, cout = detector.update([(1, 90)])
    assert cin == 0 and cout == 0
    
    cin, cout = detector.update([(1, 110)])
    assert cin == 1 and cout == 0

def test_line_crossing_right_to_left():
    detector = LineCrossingDetector(line_x=100, direction=Direction.RIGHT_TO_LEFT, cooldown_frames=0)
    
    # Move from 110 to 90 (Crossing R->L)
    cin, cout = detector.update([(1, 110)])
    assert cin == 0 and cout == 0
    
    cin, cout = detector.update([(1, 90)])
    assert cin == 0 and cout == 1

def test_line_crossing_both():
    detector = LineCrossingDetector(line_x=100, direction=Direction.BOTH, cooldown_frames=0)
    
    # ID 1: L->R
    detector.update([(1, 90)])
    cin, cout = detector.update([(1, 110)])
    assert cin == 1 and cout == 0
    
    # ID 2: R->L
    detector.update([(2, 120)])
    cin, cout = detector.update([(2, 80)])
    assert cin == 0 and cout == 1

def test_cooldown_logic():
    detector = LineCrossingDetector(line_x=100, direction=Direction.LEFT_TO_RIGHT, cooldown_frames=5)
    
    # First crossing
    detector.update([(1, 90)])
    cin, cout = detector.update([(1, 110)])
    assert cin == 1
    
    # Immediate second crossing (within cooldown)
    detector.update([(1, 90)])
    cin, cout = detector.update([(1, 110)])
    assert cin == 0
    
    # After cooldown (5 frames)
    for _ in range(4):
        detector.update([])
    detector.update([(1, 90)])
    cin, cout = detector.update([(1, 110)])
    assert cin == 1
