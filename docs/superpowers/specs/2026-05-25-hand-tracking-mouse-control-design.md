# Hand Tracking Mouse Control — Design Spec

**Date:** 2026-05-25  
**Location:** `ai_handtracking/`  
**Stack:** Python, MediaPipe, OpenCV, PyAutoGUI

---

## Goal

A minimal single-file Python app that uses a webcam to track a hand and control the mouse cursor. Moving the index finger moves the cursor. Pinching thumb and index finger together triggers a left click. Works with either hand.

---

## Architecture

Single file: `main.py`. No classes. One main loop running at webcam frame rate (~30fps).

```
Webcam frame (OpenCV)
  → Flip horizontal (mirror mode)
  → MediaPipe hand detection
  → Extract 21 landmarks per hand (first detected hand used)
  → Map index finger tip (landmark 8) → screen coordinates
  → Smooth cursor position (lerp)
  → Move mouse (PyAutoGUI)
  → Measure pinch distance (landmark 4 ↔ landmark 8)
  → If distance < threshold and cooldown elapsed → left click
  → Draw landmarks on frame (OpenCV)
  → Display frame in window
  → Press 'q' to quit
```

---

## File Structure

```
ai_handtracking/
├── pyproject.toml    # dependencies
└── main.py           # entire app
```

---

## Dependencies

| Package | Purpose |
|---|---|
| `opencv-python` | Webcam capture, frame display, landmark drawing |
| `mediapipe` | Hand landmark detection (21 points per hand) |
| `pyautogui` | OS-level mouse move and click |

---

## Key Implementation Details

### Coordinate Mapping

Camera frame resolution: 640×480 (default).  
Screen resolution: detected at runtime via `pyautogui.size()`.

```
screen_x = (landmark_x / frame_width)  * screen_width
screen_y = (landmark_y / frame_height) * screen_height
```

### Cursor Smoothing

Lerp between previous and new position to reduce jitter:
```
smooth_x = prev_x + (target_x - prev_x) * smoothing_factor  # e.g. 0.2
smooth_y = prev_y + (target_y - prev_y) * smoothing_factor
```

### Pinch Click Detection

Landmarks used:
- `4` = thumb tip
- `8` = index finger tip

```
distance = sqrt((thumb_x - index_x)² + (thumb_y - index_y)²)
if distance < 40 and time_since_last_click > 0.5s:
    pyautogui.click()
    update last_click_time
```

Cooldown of 0.5s prevents accidental repeated clicks.

### Hand Selection

`mediapipe` is configured for `max_num_hands=1`. The first hand detected is used regardless of which hand it is (left or right).

### Display

- OpenCV window shows mirrored webcam feed with landmarks drawn via `mp_drawing.draw_landmarks()`
- Press `q` to exit cleanly

---

## Error Handling

- If no hand is detected in a frame, skip processing (cursor stays in place)
- `pyautogui.FAILSAFE = True` (default) — moving mouse to screen corner aborts the script as an emergency stop

---

## Out of Scope

- Right click
- Drag
- Scroll
- Multi-hand support
- Gesture vocabulary beyond pinch-to-click
