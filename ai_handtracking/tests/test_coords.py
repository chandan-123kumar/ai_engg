import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from main import map_to_screen, is_pinching, smooth

def test_map_to_screen_center():
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
    assert is_pinching(100, 100, 110, 110, threshold=40) is True

def test_is_pinching_far():
    assert is_pinching(0, 0, 200, 200, threshold=40) is False

def test_is_pinching_exact_threshold():
    import math
    assert is_pinching(0, 0, 40, 0, threshold=40) is False

def test_smooth_moves_toward_target():
    result = smooth(0, 100, factor=0.5)
    assert result == 50.0

def test_smooth_no_movement_when_at_target():
    result = smooth(100, 100, factor=0.5)
    assert result == 100.0
