# Scenario Analysis

This document analyzes the three provided problem statement scenarios and details the tuning applied to each.

## Scenario 1: Side View Wide Shot
**Video**: `Problem_Statement_Scenario1.mp4`
- **Angle**: Side view of a truck unloading.
- **Worker Movement**: Predominantly Left to Right (truck to dock).
- **Lighting**: Bright daylight.
- **Challenges**: Workers are far from the camera, small bounding boxes.
- **Tuned Config**:
  - `line_position: 0.40`: Placed closer to the truck to catch workers early.
  - `count_direction: left_to_right`: To focus on unloading.

## Scenario 2: Portrait Loading Platform
**Video**: `Problem_Statement_Scenario2.mp4`
- **Angle**: High-angle portrait view overlooking the platform.
- **Worker Movement**: Bi-directional.
- **Lighting**: Indoor/Mixed lighting.
- **Challenges**: Portrait orientation changes the aspect ratio. Higher risk of occlusion.
- **Tuned Config**:
  - `line_position: 0.50`: Center line is most effective here.
  - `confidence: 0.35`: Lowered slightly to maintain tracks during occlusions.
  - `count_direction: both`: Accounts for workers moving both ways on the narrow platform.

## Scenario 3: Front-Facing Busy Scene
**Video**: `Problem_Statement_Scenario3.mp4`
- **Angle**: Front-facing, low angle.
- **Worker Movement**: Cross-frame movement.
- **Lighting**: Bright sunlight, high contrast.
- **Challenges**: Very crowded, workers walking in front of each other.
- **Tuned Config**:
  - `line_position: 0.60`: Offset to catch workers after they clear the initial crowd.
  - `confidence: 0.35`: Lowered to help tracker stay persistent in dense crowds.
  - `count_direction: left_to_right`: Focus on the primary flow of movement.

## General Recommendations
1. **Camera Stability**: All videos show stable camera mounting, which is critical for consistent line crossing.
2. **Line Placement**: The virtual line should be placed in an area with minimal depth changes and clear visibility of the workers' centers.
3. **Model Choice**: While `yolov8n.pt` is used for efficiency, switching to `yolov8s.pt` or `yolov8m.pt` is recommended for Scenario 3 due to the high density of workers.
