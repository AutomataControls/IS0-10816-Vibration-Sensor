#!/usr/bin/env python3
"""
Create icon.png from AutomataNexus logo
This will be run during installation to generate the icon
"""

import os
import sys

try:
    from PIL import Image, ImageDraw
except ImportError:
    print("PIL not installed, creating fallback icon...")
    # Create a simple fallback icon without PIL
    import base64
    
    # Base64 encoded 40x40 orange/teal gradient PNG
    fallback_icon = b'iVBORw0KGgoAAAANSUhEUgAAACgAAAAoCAYAAACM/rhtAAAACXBIWXMAAAsTAAALEwEAmpwYAAAEsklEQVRYhe2YW2wUVRjHf2dmZ3a3u91uS0uhUKBQoFwKiFykIhcVUYkaMTExPvjgg4kJiQ8+mPjggy8+mJj4YEJ88MEHH3zwwQcTEyMqGhWQS0GuLZRCW9pSut3d7uzszJyZOR5mZne2u7vTFhIffJOTnO+c73zn+5/vfOc7Z1b4n0OIJVi+fPns6urqFovFUm+1Wmu0/3g8fj0ej1+LRqO/X7ly5WImPysqVTFlypTpNTU1O+bPn79xzpw5y+x2u5DJp6oqkUjkbH9//4nTp08fvHDhwpnhoacsCsDq6uqla9eu3bN69eqtDoejrBjfYDDYe+LEiYOHDx8+EAwGb432flKAs2bNWv3KK6982NTUtKbU4OPj4+EvvvjivaNHjx4r5m8qBtDlcjVu2LDhvZaWlldtNps5k5+cnBx59OhR4vG4UlVV5XC73eU2m82cyfdHIpE/Dhw48O7+/fv3xmKx0GLPCgLMnTt39uuvv/5pS0vLdjGTSFEU5datW+H+/v6w3++PlJWV2RoaGmr8fn/fxMTExLVr1+bl8vX7/YEvv/xy75dffvmJJElxffuEYgDnzp27ddu2bR81NjYukiRJGR0djQwMDITHxsYiqqrOmjdv3jwhhJCTk5NnT548ecJsNpuqq6vtLpdLGB8fj8ZisYiiKLJer66u7u7Ozs73jx07dlyvE0wFeO+997a88847+z0eT7nf7w/5fL5RURQXVlRUeFwuV1V5eXllLBa7dePGjb5Lly79lhxwMBiMXL9+fcRkMtHQ0FDr8XhcHo+nXAhhunjx4rmDBw9+oOvYYtTa2tp2VlRUvHXu3LkrLS0tb8+bN2+l0+msMJvNgslkEmw2W4XT6ayYPXt2Q2Nj48L29vZN3d3d7dFoNAiQjVHbbjAYOHfu3O8DAwNXent7r5w9e/asLMsqQHQ8CC0tLW8VEjIajRW1tbWelpYWt8ViEQwGAwaDAZPJZKFAJCzmqqrCrFmz6jZu3Lje4/FU63UKKa6urm7lwoULl2bzbW5ufqi+vn5uJgBFUejr6xvdtGnTmoGBgWt2u12YNm2aa+rUqR6bzWaJx+OJvr6+vre1P4CUSkYWiUQif/b09Fzo6enpaGtr21FoIiZJkoiJeCSyxBMJSWpoaKix2+0pKYhEIrLRaFxcXl5eMT4+Hmlra1tz7dq1v9xutzfP38OGDRuWLV++fFEikVAaGhrqpk6d6i4kKwAb8SxJCwsEAqHVq1ev6Ozs/DmzsaKion7Lli3bH3/88XWlKiwtLXW9+uqrb9bW1nqSKU5oAJvb2trW/vHHH5fzgCYdRiKRSUlJiSspHwgEwk8++eSa3t7etE5RJRKJiN1utxuNRuw1NTVOZ3JXJwSZSCTUcDgcUSQlAaBtPBwJaQsGg2FZlmOKskzQ52azGb/fP1pVVVUpCJnzx2g0mgRBENzJukR4eDjgDwQCwWQyI0dHR4Pj4+MTPp9vpBhAnU0oHkdKJDKa0tqDweCk2Wy2eDye8ilTpqTQu3v37tAMrfAW0T9FpzBsf1NYXFxcBSgJh8MjMRBs6UOL/UvB2nBbLBa7NWVfXV1d3dDQ0KKoqmrOB2kCDAA2INVJCPCjF6l/A/tZLR13ZRQvAAAAAElFTkSuQmCC'
    
    # Write fallback icon
    with open('icon.png', 'wb') as f:
        f.write(base64.b64decode(fallback_icon))
    print("Created fallback icon.png")
    sys.exit(0)

def create_icon_from_logo(logo_path=None):
    """Create a 40x40 icon suitable for the web app"""
    
    if logo_path and os.path.exists(logo_path):
        # Use provided logo
        try:
            img = Image.open(logo_path)
            # Convert to RGBA if not already
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            # Resize to 40x40 maintaining aspect ratio
            img.thumbnail((40, 40), Image.Resampling.LANCZOS)
            # Create new 40x40 image with transparent background
            icon = Image.new('RGBA', (40, 40), (0, 0, 0, 0))
            # Paste resized image centered
            offset = ((40 - img.width) // 2, (40 - img.height) // 2)
            icon.paste(img, offset)
            icon.save('icon.png')
            print(f"Created icon.png from {logo_path}")
        except Exception as e:
            print(f"Error processing logo: {e}")
            create_gradient_icon()
    else:
        # Create gradient icon
        create_gradient_icon()

def create_gradient_icon():
    """Create a gradient icon with AN text"""
    size = 40
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Create circular gradient background
    center = size // 2
    for i in range(size//2, 0, -1):
        # Gradient from orange to teal
        ratio = i / (size//2)
        r = int(249 * ratio + 20 * (1-ratio))
        g = int(115 * ratio + 184 * (1-ratio))
        b = int(22 * ratio + 166 * (1-ratio))
        
        draw.ellipse([center-i, center-i, center+i, center+i], 
                     fill=(r, g, b, 255))
    
    # Add text
    try:
        from PIL import ImageFont
        # Try to use a nice font
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
    except:
        # Use default font
        font = ImageFont.load_default()
    
    # Draw text with shadow for better visibility
    text = "AN"
    # Get text bounding box
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Center text
    x = (size - text_width) // 2
    y = (size - text_height) // 2 - 2  # Slight adjustment
    
    # Draw shadow
    draw.text((x+1, y+1), text, fill=(0, 0, 0, 128), font=font)
    # Draw text
    draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)
    
    img.save('icon.png')
    print("Created gradient icon.png with AN text")

if __name__ == "__main__":
    # Check if logo path provided as argument
    logo_path = sys.argv[1] if len(sys.argv) > 1 else None
    create_icon_from_logo(logo_path)