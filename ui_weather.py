from PIL import Image, ImageDraw
import numpy as np

# Create a test background (simulate TV screen)
test_bg = Image.new('RGB', (3840, 2160), color=(20, 25, 35))  # 4K dark background

# Your weather widget code here...

# Save to see result
test_bg.save('test_widget.png')
print("Widget saved as test_widget.png")
