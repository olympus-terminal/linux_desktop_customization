#!/usr/bin/env python3
"""
Preview wallpapers and filter out street-level images
"""

from pathlib import Path
from PIL import Image
import numpy as np

def quick_preview(image_path):
    """Get a quick text description based on image characteristics"""
    with Image.open(image_path) as img:
        img_array = np.array(img.convert('RGB'))
        
        # Get image dimensions
        width, height = img.size
        
        # Sample colors from different regions
        top_third = img_array[:height//3, :]
        middle_third = img_array[height//3:2*height//3, :]
        bottom_third = img_array[2*height//3:, :]
        
        # Calculate brightness of each region
        top_brightness = np.mean(top_third)
        middle_brightness = np.mean(middle_third)
        bottom_brightness = np.mean(bottom_third)
        
        # Check for common patterns
        has_horizon = abs(top_brightness - bottom_brightness) > 30
        bright_bottom = bottom_brightness > top_brightness + 20
        
        # Edge detection hint (simplified)
        edges_y = np.diff(np.mean(img_array, axis=(0,2)))
        vertical_lines = np.sum(np.abs(edges_y) > 50)
        
        return {
            'file': image_path.name,
            'size': f"{width}x{height}",
            'top_bright': round(top_brightness, 1),
            'mid_bright': round(middle_brightness, 1),
            'bot_bright': round(bottom_brightness, 1),
            'has_horizon': has_horizon,
            'bright_bottom': bright_bottom,
            'vertical_structures': vertical_lines > 100,
            'likely_type': guess_type(top_brightness, middle_brightness, bottom_brightness, vertical_lines)
        }

def guess_type(top, mid, bot, vlines):
    """Guess image type based on characteristics"""
    if bot > top + 30 and vlines > 100:
        return "STREET/BUILDINGS"
    elif abs(top - bot) < 20 and vlines < 50:
        return "ABSTRACT/SPACE"
    elif top < 50 and bot < 50 and mid < 50:
        return "DARK/MINIMAL"
    elif bot > 100:
        return "CITY LIGHTS"
    elif top < 30 and mid > 50:
        return "SKYLINE"
    else:
        return "UNKNOWN"

def main():
    wallpaper_dir = Path.home() / 'Documents' / 'desktops' / 'scraped-wallpapers'
    
    print("🔍 Analyzing wallpapers for street-level content...\n")
    print("=" * 80)
    
    keep_list = []
    remove_list = []
    
    for img_path in sorted(wallpaper_dir.glob('*.jpg')):
        info = quick_preview(img_path)
        
        print(f"\n{info['file']}")
        print(f"  Type: {info['likely_type']}")
        print(f"  Brightness: Top={info['top_bright']}, Mid={info['mid_bright']}, Bot={info['bot_bright']}")
        print(f"  Vertical structures: {info['vertical_structures']}")
        
        # Flag potential street-level images
        if info['likely_type'] in ["STREET/BUILDINGS", "CITY LIGHTS"] or info['bright_bottom']:
            print("  ⚠️  LIKELY STREET LEVEL - Consider removing")
            remove_list.append(info['file'])
        else:
            print("  ✓ Looks good (skyline/abstract/space)")
            keep_list.append(info['file'])
    
    print("\n" + "=" * 80)
    print(f"\n📊 Summary:")
    print(f"  Keep: {len(keep_list)} wallpapers")
    print(f"  Remove: {len(remove_list)} wallpapers")
    
    if remove_list:
        print(f"\n🗑️  Suggested removals (likely street-level):")
        for f in remove_list:
            print(f"  - {f}")
    
    return keep_list, remove_list

if __name__ == "__main__":
    keep, remove = main()
    
    print("\n💡 To remove street-level images, run:")
    if remove:
        for f in remove:
            print(f"  rm /home/drn2/Documents/desktops/scraped-wallpapers/{f}")