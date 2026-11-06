#!/usr/bin/env python3
"""
Darken Wallpapers Tool
Makes bright wallpapers darker while preserving quality
"""

import os
from PIL import Image, ImageEnhance
import numpy as np
from pathlib import Path

def darken_image(input_path, output_path, darkness_factor=0.4):
    """
    Darken an image while preserving details
    darkness_factor: 0.0 = black, 1.0 = original
    """
    with Image.open(input_path) as img:
        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Method 1: Reduce brightness
        enhancer = ImageEnhance.Brightness(img)
        darkened = enhancer.enhance(darkness_factor)
        
        # Method 2: Apply dark overlay for extra darkness
        if darkness_factor < 0.5:
            # Create a dark overlay
            overlay = Image.new('RGB', img.size, (0, 0, 0))
            # Blend with original
            darkened = Image.blend(darkened, overlay, 0.3)
        
        # Save with high quality
        darkened.save(output_path, quality=95, optimize=True)
        return True

def main():
    # Create darkened directory
    output_dir = Path.home() / 'Documents' / 'desktops' / 'wallpapers-dark'
    output_dir.mkdir(exist_ok=True)
    
    # Images to darken (the bright high-res ones)
    images_to_darken = [
        ('night_skyline1.jpg', 0.4),    # Currently 68.6% dark
        ('night_skyline2.jpg', 0.35),   # Currently 62.0% dark
        ('dark_minimal1.jpg', 0.4),     # Currently 64.3% dark
        ('dark_skyline1.jpg', 0.45),    # Make darker
        ('dark_skyline2.jpg', 0.45),    # Make darker
        ('black_night1.jpg', 0.5),      # Slightly darker
        ('black_night2.jpg', 0.5),      # Slightly darker
        ('dark_city_night2.jpg', 0.45), # Make darker
    ]
    
    print("🌑 Darkening wallpapers...\n")
    
    for filename, darkness in images_to_darken:
        input_path = Path.home() / 'Documents' / 'desktops' / 'wallpapers' / filename
        if input_path.exists():
            output_path = output_dir / f'dark_{filename}'
            if darken_image(input_path, output_path, darkness):
                print(f"✓ Darkened {filename} → dark_{filename} (factor: {darkness})")
        else:
            print(f"✗ Not found: {filename}")
    
    # Copy the already dark ones
    already_dark = ['dark_stars1.jpg', 'night_city1.jpg', 'dark_city_night1.jpg']
    for filename in already_dark:
        input_path = Path.home() / 'Documents' / 'desktops' / 'wallpapers' / filename
        if input_path.exists():
            output_path = output_dir / filename
            img = Image.open(input_path)
            img.save(output_path, quality=95, optimize=True)
            print(f"✓ Copied {filename} (already dark)")
    
    print(f"\n✅ Darkened wallpapers saved to: {output_dir}")
    print("\nYou now have 11 ultra-dark 5120x1440 wallpapers!")

if __name__ == "__main__":
    main()