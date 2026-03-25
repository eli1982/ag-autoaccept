import cv2
import numpy as np
from PIL import Image

def test_match():
    haystack_path = 'test_capture_Auto-Accept Test - G.png'
    needle_path = 'targets/approve.jpg'
    
    haystack_pil = Image.open(haystack_path).convert('RGB')
    needle_pil = Image.open(needle_path).convert('RGB')
    
    haystack = cv2.cvtColor(np.array(haystack_pil), cv2.COLOR_RGB2BGR)
    needle = cv2.cvtColor(np.array(needle_pil), cv2.COLOR_RGB2BGR)
    
    result = cv2.matchTemplate(haystack, needle, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    
    print(f"Max match score: {max_val}")
    print(f"Location: {max_loc}")
    
    # Check if max_val is above some threshold
    if max_val > 0.5:
        # Draw a rectangle and save debug
        h, w = needle.shape[:2]
        top_left = max_loc
        bottom_right = (top_left[0] + w, top_left[1] + h)
        cv2.rectangle(haystack, top_left, bottom_right, (0, 0, 255), 2)
        cv2.imwrite('cv2_match_debug.png', haystack)
        print("Saved cv2_match_debug.png")

if __name__ == "__main__":
    test_match()
