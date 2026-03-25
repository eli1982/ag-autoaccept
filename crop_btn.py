from PIL import Image
try:
    img = Image.open('test_capture_Auto-Accept Test - G.png')
    # Better guess for the button based on (1296x1028)
    # Simulation header was at y=500-560
    # Button should be around y=600-650
    btn = img.crop((590, 600, 710, 660))
    btn.save('haystack_button_crop_3.png')
    print("Saved haystack_button_crop_3.png")
except Exception as e:
    print(e)
