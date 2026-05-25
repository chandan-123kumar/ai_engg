# Hand Tracking Mouse Control Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a minimal Python app that uses a webcam and MediaPipe to move the mouse cursor with the index finger and left-click via a pinch gesture.

**Architecture:** Single `main.py` file with a `while True` loop — each iteration reads a webcam frame, runs MediaPipe hand detection, maps landmark 8 (index tip) to screen coords with lerp smoothing, and fires a PyAutoGUI click when pinch distance (landmark 4 ↔ 8) drops below a threshold with a 0.5s cooldown.

**Tech Stack:** Python 3.11, OpenCV (`opencv-python`), MediaPipe, PyAutoGUI, pytest (tests only)

---

## File Map

| File | Role |
|---|---|
| `ai_handtracking/pyproject.toml` | Project metadata + dependencies |
| `ai_handtracking/main.py` | Entire app — capture, detect, control |
| `ai_handtracking/tests/test_coords.py` | Unit tests for coordinate mapping and pinch logic |

---

### Task 1: Project scaffold

**Files:**
- Create: `ai_handtracking/pyproject.toml`
- Create: `ai_handtracking/main.py` (empty stub)
- Create: `ai_handtracking/tests/__init__.py` (empty)
- Create: `ai_handtracking/tests/test_coords.py` (empty stub)

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[project]
name = "hand-tracking"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "opencv-python>=4.9",
    "mediapipe>=0.10",
    "pyautogui>=0.9",
    "pytest>=8.0",
]
```

- [ ] **Step 2: Create empty stub files**

```bash
touch ai_handtracking/main.py
mkdir -p ai_handtracking/tests
touch ai_handtracking/tests/__init__.py
touch ai_handtracking/tests/test_coords.py
```

- [ ] **Step 3: Install dependencies**

Run from `ai_handtracking/`:
```bash
cd ai_handtracking && pip install -e .
```

Expected: packages install without error. Verify:
```bash
python3 -c "import cv2, mediapipe, pyautogui; print('ok')"
```
Expected output: `ok`

- [ ] **Step 4: Commit**

```bash
git add ai_handtracking/
git commit -m "feat: scaffold hand tracking project"
```

---

### Task 2: Coordinate mapping utilities (TDD)

These are pure functions — no webcam needed. Test them in isolation.

**Files:**
- Modify: `ai_handtracking/main.py`
- Modify: `ai_handtracking/tests/test_coords.py`

- [ ] **Step 1: Write failing tests**

In `ai_handtracking/tests/test_coords.py`:

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from main import map_to_screen, is_pinching, smooth

def test_map_to_screen_center():
    # landmark at center of 640x480 frame → center of 1920x1080 screen
    sx, sy = map_to_screen(320, 240, 640, 480, 1920, 1080)
    assert sx == 960
    assert sy == 540

def test_map_to_screen_origin():
    sx, sy = map_to_screen(0, 0, 640, 480, 1920, 1080)
    assert sx == 0
    assert sy == 0

def test_map_to_screen_full():
    sx, sy = map_to_screen(640, 480, 640, 480, 1920, 1080)
    assert sx == 1920
    assert sy == 1080

def test_is_pinching_close():
    # thumb and index almost touching → pinch
    assert is_pinching(100, 100, 110, 110, threshold=40) is True

def test_is_pinching_far():
    # thumb and index far apart → no pinch
    assert is_pinching(0, 0, 200, 200, threshold=40) is False

def test_is_pinching_exact_threshold():
    # exactly at threshold → not pinching (strictly less than)
    import math
    # distance of exactly 40: use (40, 0) from origin
    assert is_pinching(0, 0, 40, 0, threshold=40) is False

def test_smooth_moves_toward_target():
    result = smooth(0, 100, factor=0.5)
    assert result == 50.0

def test_smooth_no_movement_when_at_target():
    result = smooth(100, 100, factor=0.5)
    assert result == 100.0
```

- [ ] **Step 2: Run tests — verify they FAIL**

```bash
cd ai_handtracking && python3 -m pytest tests/test_coords.py -v
```

Expected: `ImportError` or `AttributeError` — functions don't exist yet.

- [ ] **Step 3: Implement the three functions in `main.py`**

```python
import math

def map_to_screen(lx, ly, frame_w, frame_h, screen_w, screen_h):
    """Map landmark pixel coords to screen coords."""
    sx = int(lx / frame_w * screen_w)
    sy = int(ly / frame_h * screen_h)
    return sx, sy

def is_pinching(thumb_x, thumb_y, index_x, index_y, threshold=40):
    """Return True if thumb tip and index tip are closer than threshold pixels."""
    dist = math.sqrt((thumb_x - index_x) ** 2 + (thumb_y - index_y) ** 2)
    return dist < threshold

def smooth(current, target, factor=0.2):
    """Lerp current toward target by factor."""
    return current + (target - current) * factor
```

- [ ] **Step 4: Run tests — verify they PASS**

```bash
cd ai_handtracking && python3 -m pytest tests/test_coords.py -v
```

Expected: all 8 tests `PASSED`.

- [ ] **Step 5: Commit**

```bash
git add ai_handtracking/main.py ai_handtracking/tests/test_coords.py
git commit -m "feat: add coordinate mapping and pinch detection utilities"
```

---

### Task 3: Main webcam loop

This wires up OpenCV + MediaPipe + PyAutoGUI using the functions from Task 2.

**Files:**
- Modify: `ai_handtracking/main.py`

- [ ] **Step 1: Append the main loop to `main.py`**

Add this below the three utility functions:

```python
import time
import cv2
import mediapipe as mp
import pyautogui

def run():
    pyautogui.FAILSAFE = True  # move mouse to corner to emergency-stop

    screen_w, screen_h = pyautogui.size()

    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils
    hands = mp_hands.Hands(
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7,
    )

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Cannot open webcam")

    cursor_x, cursor_y = screen_w // 2, screen_h // 2
    last_click_time = 0.0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)  # mirror so movement feels natural
        frame_h, frame_w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb)

        if result.multi_hand_landmarks:
            hand = result.multi_hand_landmarks[0]
            lm = hand.landmark

            # landmark 8 = index finger tip, drives cursor
            ix = int(lm[8].x * frame_w)
            iy = int(lm[8].y * frame_h)
            target_x, target_y = map_to_screen(ix, iy, frame_w, frame_h, screen_w, screen_h)

            cursor_x = int(smooth(cursor_x, target_x))
            cursor_y = int(smooth(cursor_y, target_y))
            pyautogui.moveTo(cursor_x, cursor_y)

            # landmark 4 = thumb tip, check pinch with index
            tx = int(lm[4].x * frame_w)
            ty = int(lm[4].y * frame_h)
            now = time.time()
            if is_pinching(tx, ty, ix, iy) and (now - last_click_time) > 0.5:
                pyautogui.click()
                last_click_time = now

            mp_drawing.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)

        cv2.imshow("Hand Tracking — press q to quit", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    hands.close()


if __name__ == "__main__":
    run()
```

- [ ] **Step 2: Verify tests still pass (no regressions)**

```bash
cd ai_handtracking && python3 -m pytest tests/test_coords.py -v
```

Expected: all 8 tests `PASSED`.

- [ ] **Step 3: Smoke-test the app manually**

```bash
cd ai_handtracking && python3 main.py
```

Expected: webcam window opens, landmarks appear on your hand, moving your index finger moves the cursor, pinching triggers a click. Press `q` to quit.

- [ ] **Step 4: Commit**

```bash
git add ai_handtracking/main.py
git commit -m "feat: add webcam loop — hand tracking mouse control complete"
```

---

## Done Criteria

- [ ] `pytest tests/test_coords.py` — all 8 tests pass
- [ ] `python3 main.py` — webcam opens, cursor follows index finger, pinch clicks
- [ ] Press `q` cleanly exits
- [ ] Moving mouse to a screen corner triggers PyAutoGUI failsafe (emergency stop works)
