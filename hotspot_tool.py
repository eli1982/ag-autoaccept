import cv2
import json
import os
import sys
import glob
import pyautogui

def select_hotspot(image_path):
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: Could not read {image_path}")
        return

    window_name = f"Click the hotspot for {os.path.basename(image_path)}"
    hotspot = None

    def click_event(event, x, y, flags, param):
        nonlocal hotspot
        if event == cv2.EVENT_LBUTTONDOWN:
            hotspot = {"x": x, "y": y}
            print(f"Selected hotspot: {hotspot}")
            cv2.circle(img, (x, y), 5, (0, 255, 0), -1)
            cv2.imshow(window_name, img)

    cv2.imshow(window_name, img)
    # Bring window to front and center it
    cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1)
    try:
        import pygetwindow as gw
        # Small wait to ensure window is created and sized
        cv2.waitKey(100) 
        win = gw.getWindowsWithTitle(window_name)
        if win:
            # Get screen size and window size
            sw, sh = pyautogui.size()
            w, h = win[0].width, win[0].height
            # Center it
            win[0].moveTo((sw - w) // 2, (sh - h) // 2)
            win[0].activate()
    except:
        pass
    
    cv2.setMouseCallback(window_name, click_event)
    
    print("Click on the image where you want the script to click.")
    print("Press 's' to save and exit, or 'q' to quit without saving.")
    
    while True:
        key = cv2.waitKey(1) & 0xFF
        if key == ord('s') and hotspot:
            json_path = image_path.rsplit('.', 1)[0] + ".json"
            with open(json_path, 'w') as f:
                json.dump(hotspot, f)
            print(f"Saved hotspot to {json_path}")
            break
        elif key == ord('q'):
            print("Quit without saving.")
            break

    cv2.destroyAllWindows()

def main():
    target_dir = "targets"
    if not os.path.exists(target_dir):
        print(f"Error: {target_dir} folder not found.")
        return

    # Find all images in targets
    extensions = ['*.png', '*.jpg', '*.jpeg']
    images = []
    for ext in extensions:
        images.extend(glob.glob(os.path.join(target_dir, ext)))

    if not images:
        print("No images found in targets/ folder.")
        return

    print("Available images in targets/:")
    for i, img in enumerate(images):
        print(f"{i}: {img}")

    choice = input("Enter the number of the image to set a hotspot for (or 'a' for all): ")
    
    if choice.lower() == 'a':
        for img in images:
            select_hotspot(img)
    else:
        try:
            idx = int(choice)
            if 0 <= idx < len(images):
                select_hotspot(images[idx])
            else:
                print("Invalid index.")
        except ValueError:
            print("Invalid input.")

if __name__ == "__main__":
    main()
