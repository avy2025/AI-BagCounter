import unittest
from src.counter import BagCounter

class TestCustomClasses(unittest.TestCase):
    def test_class_mapping_logic(self):
        # Mock config
        config = {
            'person_classes': [0],
            'bag_classes': [0, 24],
            'model': 'yolov8n.pt',
            'line_position': 0.5,
            'line_orientation': 'vertical'
        }
        
        counter = BagCounter(config)
        
        # Simulate track results manually
        # In a real scenario, this would come from model.track
        class MockBox:
            def __init__(self, xyxy, id, cls):
                self.xyxy = xyxy
                self.id = id
                self.cls = cls

        class MockBoxes:
            def __init__(self, xyxy, id, cls):
                self.xyxy = MockAttr(xyxy)
                self.id = MockAttr(id)
                self.cls = MockAttr(cls)

        class MockAttr:
            def __init__(self, val):
                self.val = val
            def cpu(self):
                return self
            def numpy(self):
                return self.val

        class MockResults:
            def __init__(self, boxes_data):
                self.boxes = MockBoxes(
                    [b[0] for b in boxes_data],
                    [b[1] for b in boxes_data],
                    [b[2] for b in boxes_data]
                )

        # 1. Object with Class 0 (should be both Person and Bag)
        results = MockResults([([100, 100, 200, 200], 1, 0)])
        
        # Test the logic inside stream_video/process_video manually or by calling a helper
        # Since BagCounter is a bit monolithic, I'll test the association logic directly
        
        people = [{'box': [100, 100, 200, 200], 'id': 1}]
        bags = [{'box': [102, 102, 202, 202], 'id': 2}] # Different ID
        
        associated = counter._associate_bags_to_people(people, bags)
        self.assertEqual(len(associated), 1)
        self.assertEqual(associated[0]['id'], 2)
        self.assertTrue(people[0]['has_bag'])

    def test_overlapping_classes(self):
        # Case where class 0 is both Person and Sack
        config = {
            'person_classes': [0],
            'bag_classes': [0],
            'model': 'yolov8n.pt'
        }
        counter = BagCounter(config)
        
        # If the same detection is both person and bag
        people = [{'box': [100, 100, 200, 200], 'id': 31}]
        bags = [{'box': [100, 100, 200, 200], 'id': 31}]
        
        associated = counter._associate_bags_to_people(people, bags)
        self.assertEqual(len(associated), 1)
        self.assertEqual(associated[0]['id'], 31)
        self.assertTrue(people[0]['has_bag'])

if __name__ == "__main__":
    unittest.main()
