import cv2
import numpy as np
from PIL import Image
import os
import pyautogui

def test_agent_on():
    haystack_path = 'test.jpg'
    needle_path = 'targets/agent_on.jpg'
    
    if not os.path.exists(haystack_path):
        print(f"Error: {haystack_path} not found")
        return
    if not os.path.exists(needle_path):
        print(f"Error: {needle_path} not found")
        return
        
    haystack_pil = Image.open(haystack_path).convert('RGB')
    needle_pil = Image.open(needle_path).convert('RGB')
    
    print(f"Haystack size: {haystack_pil.size}")
    print(f"Needle size: {needle_pil.size}")
    
    # Use pyautogui.locate style matching (which uses cv2.matchTemplate)
    try:
        # We use a lower confidence to see what we get
        for conf in [0.9, 0.8, 0.7, 0.6, 0.5]:
            loc = pyautogui.locate(needle_pil, haystack_pil, confidence=conf)
            if loc:
                print(f"Found at {loc} with confidence {conf}")
                # Save debug image
                haystack_cv = cv2.cvtColor(np.array(haystack_pil), cv2.COLOR_RGB2BGR)
                top_left = (int(loc.left), int(loc.top))
                bottom_right = (int(loc.left + loc.width), int(loc.top + loc.height))
                cv2.rectangle(haystack_cv, top_left, bottom_right, (0, 255, 0), 2)
                cv2.imwrite('debug_agent_on_test.png', haystack_cv)
                print("Saved debug_agent_on_test.png")
                break
            else:
                print(f"Not found with confidence {conf}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_agent_on()

