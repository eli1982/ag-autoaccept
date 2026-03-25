import cv2
import numpy as np
from PIL import Image
import os

def update_all():
    haystack_path = 'test_capture_ag_autoaccept - Anti.png'
    if not os.path.exists(haystack_path):
        print(f"Haystack {haystack_path} not found")
        return
        
    haystack_pil = Image.open(haystack_path).convert('RGB')
    haystack = cv2.cvtColor(np.array(haystack_pil), cv2.COLOR_RGB2BGR)
    
    # Target 1: Run Buttons (Reject / Accept)
    # Search in bottom right
    # (x, y, w, h)
    # Let's take a crop and then find the buttons in it
    br_crop = haystack[850:1000, 950:1280]
    # In this crop, we want to pick a good section.
    # Looking at debug_bottom_right.png (Step 216)
    # We'll take a crop covering both buttons
    run_crop = haystack_pil.crop((1040, 875, 1240, 915)).convert('RGB')
    run_crop.save('targets/run_agent_manager.jpg')
    run_crop.save('targets/run_editor.jpg')
    print("Saved run_agent_manager.jpg and run_editor.jpg")
    
    # Target 2: Expand Button
    # Search in the middle divider area (x=707)
    # Let's look at the crop from Step 172. 
    # The divider is exactly at x=707. The button is a small vertical box.
    expand_crop = haystack_pil.crop((706, 490, 718, 525)).convert('RGB')
    expand_crop.save('targets/expand_agent_manager.jpg')
    expand_crop.save('targets/expand_editor.jpg')
    print("Saved expand_agent_manager.jpg and expand_editor.jpg")

if __name__ == "__main__":
    update_all()
