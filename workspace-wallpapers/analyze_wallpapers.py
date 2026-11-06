#!/usr/bin/env python3
"""
Wallpaper Analysis Tool
Analyzes images for darkness level, resolution, and quality
"""

import os
import sys
from PIL import Image
import numpy as np
from pathlib import Path
import json

def analyze_image(image_path):
    """Analyze an image for darkness, resolution, and quality metrics"""
    try:
        with Image.open(image_path) as img:
            # Get basic info
            width, height = img.size
            aspect_ratio = width / height
            target_aspect = 5120 / 1440  # 3.556
            
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Convert to numpy array for analysis
            img_array = np.array(img)
            
            # Calculate average brightness (0-255)
            avg_brightness = np.mean(img_array)
            
            # Calculate darkness score (0-100, higher is darker)
            darkness_score = 100 - (avg_brightness / 255 * 100)
            
            # Calculate color distribution
            r_mean = np.mean(img_array[:,:,0])
            g_mean = np.mean(img_array[:,:,1])
            b_mean = np.mean(img_array[:,:,2])
            
            # Check if it's truly dark (low brightness in all channels)
            is_dark = avg_brightness < 80  # Less than ~31% brightness
            
            # Calculate quality score based on resolution match
            resolution_score = 100
            if width < 5120 or height < 1440:
                # Penalize for being smaller than target
                resolution_score = min(width/5120, height/1440) * 100
            
            # Aspect ratio match score
            aspect_score = 100 - abs(aspect_ratio - target_aspect) / target_aspect * 100
            aspect_score = max(0, aspect_score)
            
            # Overall score combining darkness and resolution
            overall_score = (darkness_score * 0.6 + resolution_score * 0.2 + aspect_score * 0.2)
            
            return {
                'path': str(image_path),
                'filename': os.path.basename(image_path),
                'resolution': f"{width}x{height}",
                'width': width,
                'height': height,
                'aspect_ratio': round(aspect_ratio, 3),
                'avg_brightness': round(avg_brightness, 1),
                'darkness_score': round(darkness_score, 1),
                'resolution_score': round(resolution_score, 1),
                'aspect_score': round(aspect_score, 1),
                'overall_score': round(overall_score, 1),
                'is_dark': is_dark,
                'rgb_means': {
                    'r': round(r_mean, 1),
                    'g': round(g_mean, 1),
                    'b': round(b_mean, 1)
                }
            }
    except Exception as e:
        return {
            'path': str(image_path),
            'error': str(e)
        }

def scan_directory(directory):
    """Scan directory for image files"""
    image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff'}
    images = []
    
    for path in Path(directory).rglob('*'):
        if path.is_file() and path.suffix.lower() in image_extensions:
            images.append(path)
    
    return images

def main():
    # Directories to scan
    from pathlib import Path
    home = Path.home()
    directories = [
        home / 'Documents/desktops/wallpapers',
        home / 'Documents/desktops/hand-picked',
        Path('/usr/share/backgrounds')
    ]
    
    all_results = []
    
    print("🔍 Analyzing wallpapers for darkness and resolution...\n")
    
    for directory in directories:
        if os.path.exists(directory):
            print(f"📁 Scanning: {directory}")
            images = scan_directory(directory)
            
            for img_path in images:
                result = analyze_image(img_path)
                if 'error' not in result:
                    all_results.append(result)
                    if result['is_dark']:
                        print(f"  ✓ {result['filename']}: Dark={result['darkness_score']:.1f}%, Res={result['resolution']}")
            print()
    
    # Sort by overall score
    all_results.sort(key=lambda x: x['overall_score'], reverse=True)
    
    print("\n🏆 TOP 11 WALLPAPERS (Balanced darkness & resolution):")
    print("-" * 80)
    
    top_11 = all_results[:11]
    for i, img in enumerate(top_11, 1):
        print(f"{i:2}. {img['filename'][:50]:<50}")
        print(f"    Score: {img['overall_score']:.1f} | Dark: {img['darkness_score']:.1f}% | Res: {img['resolution']} | Bright: {img['avg_brightness']:.1f}")
        print(f"    Path: {img['path']}")
        print()
    
    # Find truly dark AND high-res images
    dark_hires = [img for img in all_results 
                  if img['darkness_score'] > 70 
                  and img['width'] >= 3840 
                  and img['aspect_score'] > 80]
    
    if dark_hires:
        print("\n🌙 BEST DARK HIGH-RES WALLPAPERS:")
        print("-" * 80)
        for img in dark_hires[:11]:
            print(f"  • {img['filename']}: Dark={img['darkness_score']:.1f}%, {img['resolution']}")
    
    # Save results to JSON
    output_file = home / 'Documents/desktops/wallpaper_analysis.json'
    with open(output_file, 'w') as f:
        json.dump({
            'all_results': all_results,
            'top_11': top_11,
            'dark_hires': dark_hires[:11]
        }, f, indent=2)
    
    print(f"\n💾 Full analysis saved to: {output_file}")
    
    # Generate recommendation
    print("\n📊 RECOMMENDATION:")
    if dark_hires and len(dark_hires) >= 11:
        print("✅ Found enough dark high-res wallpapers! Use the 'dark_hires' list.")
    else:
        print("⚠️  Not enough dark high-res images. Options:")
        print("   1. Download more 5120x1440 dark wallpapers")
        print("   2. Use image editing to darken the bright ones")
        print("   3. Resize the dark low-res ones with AI upscaling")

if __name__ == "__main__":
    main()