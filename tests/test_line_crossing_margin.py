import unittest
from src.line_crossing import LineCrossingDetector, Direction, Orientation

class TestLineCrossing(unittest.TestCase):
    def test_margin_slow_movement(self):
        # Line at 100, margin 5. Range is [95, 105]
        detector = LineCrossingDetector(line_coord=100, direction=Direction.BOTH, orientation=Orientation.VERTICAL, line_margin=5)
        
        # Object starts at 90 (below margin)
        cin, cout = detector.update([(1, 90)])
        self.assertEqual(cin, 0)
        self.assertEqual(cout, 0)
        
        # Moves to 96 (inside margin)
        cin, cout = detector.update([(1, 96)])
        self.assertEqual(cin, 0)
        self.assertEqual(cout, 0)
        
        # Moves to 104 (inside margin)
        cin, cout = detector.update([(1, 104)])
        self.assertEqual(cin, 0)
        self.assertEqual(cout, 0)
        
        # Moves to 106 (crosses above margin) - Should count!
        cin, cout = detector.update([(1, 106)])
        self.assertEqual(cin, 1)
        self.assertEqual(cout, 0)

    def test_no_double_count_in_margin(self):
        detector = LineCrossingDetector(line_coord=100, direction=Direction.BOTH, orientation=Orientation.VERTICAL, line_margin=5, cooldown_frames=10)
        
        # Start below
        detector.update([(1, 90)])
        # Cross above
        detector.update([(1, 110)]) # count_in = 1
        
        # Move back into margin
        cin, cout = detector.update([(1, 100)])
        self.assertEqual(cin, 0)
        
        # Move back above - should NOT count again (even without cooldown, it shouldn't as it didn't cross from below)
        cin, cout = detector.update([(1, 110)])
        self.assertEqual(cin, 0)

if __name__ == "__main__":
    unittest.main()
