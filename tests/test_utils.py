import os
import yaml
import pytest
from src.utils import load_config

def test_load_config_success(tmp_path):
    d = tmp_path / "config"
    d.mkdir()
    config_file = d / "test_config.yaml"
    config_data = {"model": "test.pt", "confidence": 0.5}
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)
    
    loaded = load_config(str(config_file))
    assert loaded["model"] == "test.pt"
    assert loaded["confidence"] == 0.5

def test_load_config_not_found():
    with pytest.raises(FileNotFoundError):
        load_config("non_existent.yaml")
