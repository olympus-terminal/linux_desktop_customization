#!/usr/bin/env python3
"""
Process TOPAZ wallpapers with light adjustments:
- 3% darkening (brightness -3%)
- 2% contrast increase
"""

import os
from PIL import Image, ImageEnhance

# Directories
SOURCE_DIR = "MJ7-Topaz/TOPAZ-MJ-scaleUps"
OUTPUT_DIR = "MJ7-Topaz/light-processed"

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)

def process_image(input_path, output_path):
    """Apply light processing to an image"""
    try:
        # Open image
        img = Image.open(input_path)

        # Apply brightness adjustment (-3% = 0.97)
        brightness_enhancer = ImageEnhance.Brightness(img)
        img = brightness_enhancer.enhance(0.97)

        # Apply contrast adjustment (+2% = 1.02)
        contrast_enhancer = ImageEnhance.Contrast(img)
        img = contrast_enhancer.enhance(1.02)

        # Save processed image
        img.save(output_path, "PNG", optimize=True)
        print(f"✓ Processed: {os.path.basename(output_path)}")

    except Exception as e:
        print(f"✗ Error processing {input_path}: {e}")

def main():
    print("Processing TOPAZ wallpapers with light adjustments...")
    print("Settings: -3% brightness, +2% contrast")
    print()

    # Process all PNG files in source directory
    for filename in os.listdir(SOURCE_DIR):
        if filename.endswith('.png') and not filename.startswith('.'):
            input_path = os.path.join(SOURCE_DIR, filename)
            output_path = os.path.join(OUTPUT_DIR, filename)
            process_image(input_path, output_path)

    print(f"\nProcessing complete! Images saved to {OUTPUT_DIR}")

if __name__ == "__main__":
    main()