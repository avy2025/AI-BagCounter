from src.line_crossing import LineCrossingDetector, Direction, Orientation

def test_reproduction():
    # Setup similar to Scenario 1
    # Line at 60%, width 1000 -> line_coord = 600
    detector = LineCrossingDetector(line_coord=600, direction=Direction.BOTH, orientation=Orientation.VERTICAL, line_margin=2)
    
    # Track 31: Starts on the Right (e.g. 700)
    print("Frame 1: Track 31 at 700 (Right)")
    cin, cout = detector.update([(31, 700)])
    print(f"  Result -> IN: {cin}, OUT: {cout}")
    
    # Track 31: Moves to the Right (e.g. 650)
    print("Frame 2: Track 31 at 650 (Right)")
    cin, cout = detector.update([(31, 650)])
    print(f"  Result -> IN: {cin}, OUT: {cout}")
    
    # Track 31: Crosses to the Left (e.g. 550)
    print("Frame 3: Track 31 at 550 (Left)")
    cin, cout = detector.update([(31, 550)])
    print(f"  Result -> IN: {cin}, OUT: {cout}")
    
    # Track 31: Further Left (e.g. 500)
    print("Frame 4: Track 31 at 500 (Left)")
    cin, cout = detector.update([(31, 500)])
    print(f"  Result -> IN: {cin}, OUT: {cout}")

if __name__ == "__main__":
    test_reproduction()
