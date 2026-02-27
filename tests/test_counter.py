import pytest
from src.counter import BagCounter

def test_bag_counter_init():
    config = {"model": "yolov8n.pt", "confidence": 0.4}
    counter = BagCounter(config)
    assert counter.config["confidence"] == 0.4
    assert counter.count_in == 0
    assert counter.count_out == 0

def test_bag_counter_invalid_video():
    counter = BagCounter({})
    results = counter.process_video("non_existent_video.mp4")
    assert results["in"] == 0
    assert results["out"] == 0
