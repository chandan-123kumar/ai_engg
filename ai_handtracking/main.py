import math
import time
import cv2
import mediapipe as mp
import pyautogui

def map_to_screen(lx, ly, frame_w, frame_h, screen_w, screen_h):
    sx = int(lx / frame_w * screen_w)
    sy = int(ly / frame_h * screen_h)
    return sx, sy

def is_pinching(thumb_x, thumb_y, index_x, index_y, threshold=40):
    dist = math.sqrt((thumb_x - index_x) ** 2 + (thumb_y - index_y) ** 2)
    return dist < threshold

def smooth(current, target, factor=0.2):
    return current + (target - current) * factor


def run():
    pyautogui.FAILSAFE = True

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

        frame = cv2.flip(frame, 1)
        frame_h, frame_w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb)

        if result.multi_hand_landmarks:
            hand = result.multi_hand_landmarks[0]
            lm = hand.landmark

            ix = int(lm[8].x * frame_w)
            iy = int(lm[8].y * frame_h)
            target_x, target_y = map_to_screen(ix, iy, frame_w, frame_h, screen_w, screen_h)

            cursor_x = int(smooth(cursor_x, target_x))
            cursor_y = int(smooth(cursor_y, target_y))
            pyautogui.moveTo(cursor_x, cursor_y)

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
