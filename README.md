# AI-BagCounter 

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![YOLOv8](https://img.shields.io/badge/YOLO-v8-brightgreen.svg)](https://github.com/ultralytics/ultralytics)

AI-powered jute sack counting system for warehouse logistics using YOLOv8 + ByteTrack.

## 📌 Problem Statement
In grain warehouses (mandis), manual counting of jute sacks during truck unloading is labor-intensive and error-prone. This system automates the process using computer vision. By detecting workers carrying sacks and tracking their movement across a virtual counting line, the system provides accurate, real-time counts of bags being moved.

## 🎯 Features
- **Automated Counting**: Incremental counting as workers cross a virtual line.
- **Directional Detection**: Track IN and OUT movement separately.
- **Scenario Tuning**: Optimized configurations for different camera angles and environments.
- **Web Dashboard**: Real-time processed video streaming via Flask.
- **Visualization**: Live HUD overlay showing counts, tracks, and the counting line.
- **Batch Processing**: Easily run analysis on multiple videos at once.

## 🧠 How It Works
The system follows a multi-stage computer vision pipeline:

```
Video Frame → YOLO Detection (Person) → ByteTrack ID Assignment → Line Crossing Check → Count Update → Annotated Output
```

1. **Detection**: YOLOv8 detects people (used as a proxy for bag carriers).
2. **Tracking**: ByteTrack maintains consistent IDs for each person across frames.
3. **Line Crossing**: The system checks if a person's center point has crossed a pre-defined vertical line.
4. **Counting**: Crossings are categorized based on direction (Left to Right or Right to Left).
5. **Output**: An annotated video is saved with bounding boxes, IDs, and the current count.

## 📁 Project Structure
```
AI-BagCounter/
├── config/             # Scenario-specific configuration files
├── src/                # Core source code
├── notebooks/          # Analysis and demo notebooks
├── tests/              # Unit tests
├── docs/               # Technical documentation
└── assets/             # Sample images and media
```

## ⚙️ Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/AI-BagCounter.git
   cd AI-BagCounter
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. (Optional) Install as a package:
   ```bash
   pip install -e .
   ```

## ▶️ Usage
### Single Video Run
```bash
python main.py --video scenario1.mp4 --config config/scenario1_config.yaml
```

### Batch Run
```bash
python run_all_scenarios.py
```

### Web Dashboard (Real-time Streaming)
1. Start the Flask server:
   ```bash
   $env:PYTHONPATH = ".;$env:PYTHONPATH"
   python webapp/flask_server.py
   ```
2. Open your browser and navigate to `http://localhost:8000`.
3. Select a scenario and click **"Start Analysis"** to view real-time processed results.

## 📊 Results Summary
| Scenario | Count IN | Count OUT | Total |
|----------|----------|-----------|-------|
| Scenario 1 | - | - | - |
| Scenario 2 | - | - | - |
| Scenario 3 | - | - | - |

## 📸 Sample Output
Sample outputs can be found in the `assets/` directory.

## 🔧 Improving Accuracy
- **Model Selection**: Switch to `yolov8m.pt` or `yolov8l.pt` for better detection at the cost of speed.
- **Custom Training**: Fine-tune YOLOv8 specifically on jute sacks to avoid using "person" as a proxy.
- **Confidence Threshold**: Adjust `--conf` in the YAML config to filter out false positives.

## 🛣️ Roadmap
- Support for real-time RTSP streams.
- Cloud deployment and database integration for long-term storage.
- REST API for integration with warehouse management systems.
- Custom-trained model for sack detection.

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
