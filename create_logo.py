from PIL import Image, ImageDraw, ImageFont

# Create a new image with white background
width, height = 128, 128
image = Image.new('RGB', (width, height), 'white')
draw = ImageDraw.Draw(image)

# Draw a plate (circle)
plate_radius = 50
center_x, center_y = width // 2, height // 2
draw.ellipse([
    (center_x - plate_radius, center_y - plate_radius),
    (center_x + plate_radius, center_y + plate_radius)
], outline='black', width=3)

# Draw fork (simple lines)
fork_width = 20
fork_height = 40
fork_x = center_x - fork_width // 2
fork_y = center_y - fork_height

draw.line([
    (fork_x, fork_y),
    (fork_x + fork_width, fork_y)
], fill='black', width=2)

draw.line([
    (fork_x + fork_width // 4, fork_y + fork_height // 3),
    (fork_x + fork_width // 4, fork_y + fork_height)
], fill='black', width=2)

draw.line([
    (fork_x + fork_width // 2, fork_y + fork_height // 3),
    (fork_x + fork_width // 2, fork_y + fork_height)
], fill='black', width=2)

draw.line([
    (fork_x + fork_width * 3 // 4, fork_y + fork_height // 3),
    (fork_x + fork_width * 3 // 4, fork_y + fork_height)
], fill='black', width=2)

# Save the image
image.save('static/img/logo.png')
