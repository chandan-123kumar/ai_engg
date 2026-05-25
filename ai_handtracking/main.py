import math

def map_to_screen(lx, ly, frame_w, frame_h, screen_w, screen_h):
    sx = int(lx / frame_w * screen_w)
    sy = int(ly / frame_h * screen_h)
    return sx, sy

def is_pinching(thumb_x, thumb_y, index_x, index_y, threshold=40):
    dist = math.sqrt((thumb_x - index_x) ** 2 + (thumb_y - index_y) ** 2)
    return dist < threshold

def smooth(current, target, factor=0.2):
    return current + (target - current) * factor
