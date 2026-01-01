from PIL import Image, ImageDraw, ImageFont
import os

# Create a new image with a green background
img = Image.new('RGB', (128, 128), color='#4CAF50')
draw = ImageDraw.Draw(img)

# Draw a white shield shape
shield_points = [
    (64, 20),   # Top point
    (90, 45),   # Top right
    (90, 85),   # Right side
    (80, 100),  # Bottom right curve
    (64, 108),  # Bottom point
    (48, 100),  # Bottom left curve
    (38, 85),   # Left side
    (38, 45),   # Top left
]
draw.polygon(shield_points, fill='white')

# Draw "CS" text in green
try:
    # Try to use a nice font
    font = ImageFont.truetype("arial.ttf", 45)
except:
    # Fallback to default font
    font = ImageFont.load_default()

# Draw text
text = "CS"
# Get text bounding box for centering
bbox = draw.textbbox((0, 0), text, font=font)
text_width = bbox[2] - bbox[0]
text_height = bbox[3] - bbox[1]
x = (128 - text_width) // 2
y = (128 - text_height) // 2 - 10

draw.text((x, y), text, fill='#4CAF50', font=font)

# Save the image
output_path = os.path.join(os.path.dirname(__file__), 'icon128.png')
img.save(output_path)
print(f"Icon saved to {output_path}")
