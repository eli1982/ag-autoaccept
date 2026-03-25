# Antigravity Auto-Accept

This is a robust Python script that uses `PyAutoGUI` and OpenCV to visually scan your screen for the "Approve/Continue" button and click it automatically.

## Setup

1. **Install Python dependencies:**
   *(Since you are using Anaconda, use conda)*
   ```bash
   conda install -y -c conda-forge pyautogui opencv Pillow pygetwindow
   ```

2. **Create target images:**
   Take small screenshots of the buttons and save them in the `targets/` folder as `.png` or `.jpg`.

## Advanced Features

### Hotspot Selection
Run `python hotspot_tool.py` to precisely choose where to click within a larger screenshot. This will create a `.json` file for that image.

### Dynamic Confidence
If an image matches too generically (like the "Collapse" row), you can manually edit its `.json` file to increase the confidence threshold:
```json
{
  "x": 308, 
  "y": 24,
  "confidence": 0.98
}
```

### Idle-Peek (Below the Fold)
If the script doesn't find any matches for 10 seconds AND you haven't moved your mouse, it will automatically scroll down slightly to check for hidden buttons "below the fold." This is non-disruptive as it stops the moment you move your mouse.

### Loop Protection
Clicked images are moved to the back of the queue, ensuring multi-step prompts (like Expand -> Run) work correctly without looping on the first button.
