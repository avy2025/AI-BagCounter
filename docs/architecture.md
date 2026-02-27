# System Architecture

The AI-BagCounter system is designed with a modular pipeline approach to ensure reliability and ease of configuration.

## Data Flow Diagram

```text
+----------------+      +------------------+      +-------------------+
|  Input Video   |----->|  Preprocessing   |----->| YOLOv8 Detection  |
| (MP4 Scenarios)|      | (OpenCV Resize)  |      |   (Person Class)  |
+----------------+      +------------------+      +---------+---------+
                                                            |
                                                            v
+----------------+      +------------------+      +---------+---------+
| Output Video/  |      |  Count Manager   |      |   ByteTrack      |
| Result Summary |<-----+ (Line Crossing   |<-----|  ID Persistence   |
+----------------+      |     Logic)       |      +-------------------+
```

## Component Breakdown

1. **Video Ingester**: Reads frames from video files using OpenCV.
2. **Object Detector (YOLOv8)**: Extracts bounding boxes for the 'person' class in each frame.
3. **Multi-Object Tracker (ByteTrack)**: Assigns unique IDs to detected persons and maintains them across frames.
4. **Crossing Logic (LineCrossingDetector)**: Tracks the `x` coordinate of each ID. If the coordinate moves across a virtual vertical threshold, a crossing is registered.
5. **Cooldown Mechanism**: Prevents jitter from causing double counts by enforcing a frame-based cooldown per ID.
6. **Visualizer**: Renders the HUD, bounding boxes, and tracks onto the final output frames.
7. **CLI Orchestrator**: Handles user arguments and scenario-specific configurations.
