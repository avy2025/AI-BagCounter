# How It Works: AI Bag Counter

This project automates the counting of jute sacks in a warehouse environment. Since jute sacks are often handled by workers, we use the movement of the workers themselves as a proxy for the bags.

## The AI Pipeline

### 1. Detection (YOLOv8)
We use a pre-trained **YOLOv8** model to identify people in each frame of the video. YOLO (You Only Look Once) is extremely fast and accurate, making it ideal for real-time video analysis. Even though we are counting bags, detecting people is more reliable because standard AI models are already very good at recognizing humans.

### 2. Tracking (ByteTrack)
Detecting a person in one frame isn't enough; we need to know it's the *same* person in the next frame. **ByteTrack** solves this by assigning a unique ID (e.g., "Person #4") to each detection. It uses the speed and direction of movement to "guess" where the person will be in the next frame, even if they are briefly hidden behind someone else.

### 3. Virtual Counting Line
We draw an invisible vertical line across the video. In our code, we define this as a fraction of the video width (e.g., `0.5` means the middle of the screen).

### 4. Crossing Check
The system remembers the last position of every tracked person. 
*   If Person #A was on the **left** of the line in frame 100 and is now on the **right** in frame 101, we increment the **IN** count.
*   If they move from **right to left**, we increment the **OUT** count.

### 5. Cooldown Logic
Sometimes a person might stand right on top of the line, causing their position to "flicker" back and forth. To prevent counting the same person 10 times in one second, our system puts that specific ID on "cooldown" for 30 frames (about 1 second) after a count is recorded.

## Why this works for Mandis
Grain warehouses are busy. This system handles multiple workers simultaneously and accounts for movement in both directions, ensuring that sacks being moved *into* the warehouse are counted accurately while ignoring or separate-counting sacks being moved *out*.
