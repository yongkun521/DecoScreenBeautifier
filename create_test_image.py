from PIL import Image, ImageDraw

# 创建一个简单的测试图片
img = Image.new('RGB', (100, 50), color = (73, 109, 137))
d = ImageDraw.Draw(img)
d.text((10,10), "Deco", fill=(255,255,0))
d.text((10,25), "Screen", fill=(255,0,255))
img.save('assets/logo.png')
