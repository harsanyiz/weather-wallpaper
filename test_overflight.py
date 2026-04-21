from PIL import Image, ImageDraw
img = Image.new('RGB', (1920, 1080), color = (73, 109, 137))
draw = ImageDraw.Draw(img)
draw.text((10,10), "Hello TV", fill=(255,255,255))
img.save('test.jpg', 'JPEG') # MINIMUM BEÁLLÍTÁSOKKAL
