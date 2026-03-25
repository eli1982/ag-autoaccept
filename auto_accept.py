import pyautogui
import time
import os
import glob
import pygetwindow as gw
import argparse
import ctypes
import ctypes.wintypes as wintypes
import json
import sys
import threading
from PIL import Image
import numpy as np

# Win32 Constants
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_MOUSEWHEEL = 0x020A
PW_RENDERFULLCONTENT = 0x02
BI_RGB = 0
DIB_RGB_COLORS = 0
SW_RESTORE = 9
SW_MINIMIZE = 6
SW_SHOWNOACTIVATE = 4
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x80000
WS_EX_TOOLWINDOW = 0x00000080
LWA_ALPHA = 0x2

# Low-level Win32 APIs
user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ('biSize', wintypes.DWORD),
        ('biWidth', wintypes.LONG),
        ('biHeight', wintypes.LONG),
        ('biPlanes', wintypes.WORD),
        ('biBitCount', wintypes.WORD),
        ('biCompression', wintypes.DWORD),
        ('biSizeImage', wintypes.DWORD),
        ('biXPelsPerMeter', wintypes.LONG),
        ('biYPelsPerMeter', wintypes.LONG),
        ('biClrUsed', wintypes.DWORD),
        ('biClrImportant', wintypes.DWORD),
    ]

class BITMAPINFO(ctypes.Structure):
    _fields_ = [
        ('bmiHeader', BITMAPINFOHEADER),
        ('bmiColors', wintypes.DWORD * 3),
    ]

class WINDOWPLACEMENT(ctypes.Structure):
    _fields_ = [
        ('length', wintypes.UINT),
        ('flags', wintypes.UINT),
        ('showCmd', wintypes.UINT),
        ('ptMinPosition', wintypes.POINT),
        ('ptMaxPosition', wintypes.POINT),
        ('rcNormalPosition', wintypes.RECT),
    ]

# Global tracking for IPC
heartbeat_time = time.time()

def stdin_listener():
    """Thread function to read commands from the VS Code extension."""
    global heartbeat_time
    while True:
        try:
            line = sys.stdin.readline()
            if not line: break
            cmd = line.strip().lower()
            if cmd == "heartbeat": heartbeat_time = time.time()
        except: break

def send_ipc(data):
    print(json.dumps(data), flush=True)

def log_ipc(message):
    send_ipc({"type": "log", "message": message})

def capture_window_to_pil(hwnd):
    """Captures a window's content into a PIL image using PrintWindow."""
    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    w = rect.right - rect.left
    h = rect.bottom - rect.top
    
    if w <= 0 or h <= 0: return None

    hdc_screen = user32.GetDC(0)
    hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
    hbmp = gdi32.CreateCompatibleBitmap(hdc_screen, w, h)
    gdi32.SelectObject(hdc_mem, hbmp)
    
    # Try with rendering full content (for overlapped windows)
    result = user32.PrintWindow(hwnd, hdc_mem, PW_RENDERFULLCONTENT)
    if not result:
        result = user32.PrintWindow(hwnd, hdc_mem, 0)
    
    if not result:
        # Final fallback: BitBlt if PrintWindow fails (requires visibility)
        hdc_window = user32.GetWindowDC(hwnd)
        gdi32.BitBlt(hdc_mem, 0, 0, w, h, hdc_window, 0, 0, 0x00CC0020) # SRCCOPY
        user32.ReleaseDC(hwnd, hdc_window)

    # Get bits
    bmi = BITMAPINFO()
    bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.bmiHeader.biWidth = w
    bmi.bmiHeader.biHeight = -h  # Top-down
    bmi.bmiHeader.biPlanes = 1
    bmi.bmiHeader.biBitCount = 32
    bmi.bmiHeader.biCompression = BI_RGB
    
    buffer = ctypes.create_string_buffer(w * h * 4)
    gdi32.GetDIBits(hdc_mem, hbmp, 0, h, buffer, ctypes.byref(bmi), DIB_RGB_COLORS)
    
    # Cleanup
    gdi32.DeleteObject(hbmp)
    gdi32.DeleteDC(hdc_mem)
    user32.ReleaseDC(0, hdc_screen)
    
    # Convert BGRA to RGBA for PIL
    return Image.frombuffer('RGBA', (w, h), buffer, 'raw', 'BGRA', 0, 1)

def background_click(hwnd, x, y):
    """Sends a click to a specific coordinate within a window without moving the mouse."""
    lParam = (y << 16) | x
    user32.PostMessageW(hwnd, WM_LBUTTONDOWN, 1, lParam)
    time.sleep(0.05)
    user32.PostMessageW(hwnd, WM_LBUTTONUP, 0, lParam)

def background_scroll(hwnd, dist, x=None, y=None):
    """Sends a mouse wheel scroll to the window at the specified coordinates."""
    # dist is in multiples of 120 (one notch)
    wParam = (dist << 16)
    
    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    w = rect.right - rect.left
    h = rect.bottom - rect.top
    
    if x is None: x = w // 2
    if y is None: y = h // 2
    
    lParam = (y << 16) | x
    user32.PostMessageW(hwnd, WM_MOUSEWHEEL, wParam, lParam)

def main():
    parser = argparse.ArgumentParser(description="Antigravity Auto-Accept.")
    parser.add_argument("--debug", action="store_true", help="Show verbose logs and save debug captures.")
    parser.add_argument("--conf", type=float, default=0.8, help="Default confidence (0.0 to 1.0).")
    parser.add_argument("--ipc", action="store_true", help="Enable IPC.")
    args = parser.parse_args()

    if args.ipc:
        t = threading.Thread(target=stdin_listener, daemon=True)
        t.start()
        log_ipc("Python engine started in Background Mode.")

    global heartbeat_time
    last_action = {"image": "", "location": (0,0), "time": 0, "hwnd": 0}
    last_scan_time = time.time()
    button_images = []
    last_reload_time = 0

    # --- Cache for Image Targets ---
    image_cache = {} # path -> {"image": PIL_Image, "hotspot": dict, "confidence": float, "mtime": float}

    try:
        while True:
            current_time = time.time()
            
            # --- Hot-Reload (Every 10s) ---
            if current_time - last_reload_time > 10:
                new_image_paths = glob.glob(os.path.join("targets", "*.[pj][np][ge]*"))
                
                # Check for new or removed files
                if set(new_image_paths) != set(image_cache.keys()):
                    # Purge removed files
                    for p in list(image_cache.keys()):
                        if p not in new_image_paths:
                            del image_cache[p]
                
                # Update/Load files
                loaded_any = False
                for img_path in new_image_paths:
                    try:
                        mtime = os.path.getmtime(img_path)
                        if img_path not in image_cache or image_cache[img_path]["mtime"] < mtime:
                            # Load Image
                            with Image.open(img_path) as img:
                                needle = img.convert("RGB") # Always use RGB for cv2 matching
                                needle.load() # Force load into memory
                            
                            # Load Config
                            conf = args.conf
                            json_path = img_path.rsplit('.', 1)[0] + ".json"
                            hotspot = None
                            if os.path.exists(json_path):
                                try:
                                    with open(json_path, 'r') as f:
                                        cfg = json.load(f)
                                        hotspot = cfg
                                        conf = cfg.get("confidence", args.conf)
                                except: pass
                            
                            image_cache[img_path] = {
                                "image": needle,
                                "hotspot": hotspot,
                                "confidence": conf,
                                "mtime": mtime
                            }
                            loaded_any = True
                    except Exception as e:
                        if args.debug: log_ipc(f"Failed to load {img_path}: {e}")

                if loaded_any:
                    log_ipc(f"Reloaded templates. Total: {len(image_cache)} image(s) active.")
                
                button_images = list(image_cache.keys())
                last_reload_time = current_time

            if not image_cache:
                time.sleep(1)
                continue

            # --- Target Windows ---
            all_windows = gw.getAllWindows()
            targets = [w for w in all_windows if any(sub in w.title.lower() for sub in ["antigravity", "visual studio code", "manager", "auto-accept", "chrome", "edge", "nemoclaw", "terminal"])]
            
            found_any_global = False
            for window in targets:
                hwnd = window._hWnd
                is_minimized = user32.IsIconic(hwnd)
                original_placement = None

                if is_minimized:
                    # --- Stealth Capture ---
                    # 1. Save state
                    placement = WINDOWPLACEMENT()
                    placement.length = ctypes.sizeof(WINDOWPLACEMENT)
                    user32.GetWindowPlacement(hwnd, ctypes.byref(placement))
                    original_placement = placement
                    
                    ex_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                    original_ex_style = ex_style

                    # 2. Set Stealth Styles (Transparent)
                    user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex_style | WS_EX_LAYERED)
                    user32.SetLayeredWindowAttributes(hwnd, 0, 0, LWA_ALPHA)
                    
                    # 3. Move off-screen and restore (no-activate)
                    # Dynamic Resolution: Use 4K or monitor resolution, whichever is larger
                    sw = user32.GetSystemMetrics(0) # SM_CXSCREEN
                    sh = user32.GetSystemMetrics(1) # SM_CYSCREEN
                    rw = max(3840, sw)
                    rh = max(2160, sh)
                    
                    offscreen_rect = wintypes.RECT(-20000, -20000, -20000 + rw, -20000 + rh)
                    new_placement = WINDOWPLACEMENT()
                    new_placement.length = ctypes.sizeof(WINDOWPLACEMENT)
                    new_placement.showCmd = SW_SHOWNOACTIVATE
                    new_placement.rcNormalPosition = offscreen_rect
                    user32.SetWindowPlacement(hwnd, ctypes.byref(new_placement))
                    time.sleep(0.3) # Wait for resize and render

                # 1. Capture
                haystack = capture_window_to_pil(hwnd)
                
                if haystack and args.debug:
                    haystack.save("debug_haystack.png")
                    # log_ipc(f"Debug: Captured '{window.title}' ({haystack.width}x{haystack.height})")

                # 2. Scan
                clicked_this_window = False
                if haystack:
                    # Convert haystack once to RGB (cv2 likes 3 channels)
                    haystack_rgb = haystack.convert("RGB")
                    hw, hh = haystack_rgb.size
                    
                    for i, img_path in enumerate(button_images):
                        try:
                            item = image_cache.get(img_path)
                            if not item: continue
                            
                            needle = item["image"]
                            conf = item["confidence"]
                            hotspot = item["hotspot"]
                            
                            nw, nh = needle.size
                            
                            # SAFETY: Skip if window is smaller than target
                            if nw > hw or nh > hh:
                                continue

                            loc = pyautogui.locate(needle, haystack_rgb, confidence=conf)
                            
                            if loc:
                                found_any_global = True
                                if (last_action["image"] == img_path and 
                                    last_action["location"] == (loc.left, loc.top) and 
                                    last_action["hwnd"] == hwnd and
                                    current_time - last_action["time"] < 3):
                                    if args.debug: log_ipc(f"Skipping '{os.path.basename(img_path)}' - recently clicked.")
                                    continue

                                # --- Action! ---
                                msg = f"Found '{os.path.basename(img_path)}' in '{window.title}'! Background clicking..."
                                log_ipc(msg)
                                
                                target_x, target_y = None, None
                                if hotspot and "x" in hotspot and "y" in hotspot:
                                    target_x = loc.left + hotspot['x']
                                    target_y = loc.top + hotspot['y']
                                else:
                                    target_x, target_y = int(loc.left + loc.width/2), int(loc.top + loc.height/2)
                                
                                background_click(hwnd, target_x, target_y)
                                
                                if args.ipc:
                                    send_ipc({"type": "click", "image": os.path.basename(img_path), "saved": 1})

                                # Expansion Check
                                fn = os.path.basename(img_path).lower()
                                if any(k in fn for k in ["expand", "input", "required"]):
                                    log_ipc("Expansion detected. Background scrolling.")
                                    background_scroll(hwnd, -600)

                                last_action = {"image": img_path, "location": (loc.left, loc.top), "time": current_time, "hwnd": hwnd}
                                clicked_this_window = True
                                # Reprioritize within window
                                button_images.append(button_images.pop(i))
                                break
                        except pyautogui.ImageNotFoundException:
                            # This is expected when an image is not found, do not log as an error.
                            continue
                        except Exception as e:
                            if args.debug:
                                log_ipc(f"Scan error on {img_path}: {type(e).__name__} - {e}")
                            continue
                
                # 3. Restore State if needed
                if is_minimized and original_placement:
                    user32.ShowWindow(hwnd, SW_MINIMIZE)
                    user32.SetWindowPlacement(hwnd, ctypes.byref(original_placement))
                    if 'original_ex_style' in locals():
                        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, original_ex_style)

                # --- Idle Peek per window ---
                if not clicked_this_window and (current_time - heartbeat_time > 15) and (current_time - last_scan_time > 20):
                    log_ipc(f"Idle peek in background window: {window.title}")
                    # Target the right side (50px from edge) for most main app windows
                    background_scroll(hwnd, -800, x=window.width - 50)
                    last_scan_time = current_time

            time.sleep(0.5)

    except KeyboardInterrupt:
        log_ipc("Python engine stopped.")
    except Exception as e:
        log_ipc(f"Critical error: {str(e)}")

if __name__ == "__main__":
    main()
