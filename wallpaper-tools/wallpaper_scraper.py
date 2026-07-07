#!/usr/bin/env python3
"""
Advanced Wallpaper Scraper
Finds ultra-dark, high-resolution wallpapers from multiple sources
"""

import requests
import json
import os
import time
from pathlib import Path
from urllib.parse import urlencode, quote
import re
from PIL import Image
import numpy as np
import io

class WallpaperScraper:
    def __init__(self):
        self.output_dir = Path.home() / 'Documents' / 'desktops' / 'scraped-wallpapers'
        self.output_dir.mkdir(exist_ok=True)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.min_width = 4096  # Slightly lower than 5120 to get more results
        self.min_height = 1440
        self.target_darkness = 70  # Minimum darkness percentage
        
    def analyze_image_darkness(self, img_data):
        """Quick darkness analysis without saving"""
        try:
            img = Image.open(io.BytesIO(img_data))
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Sample the image for quick analysis
            img.thumbnail((400, 400))  # Resize for faster analysis
            img_array = np.array(img)
            avg_brightness = np.mean(img_array)
            darkness_score = 100 - (avg_brightness / 255 * 100)
            
            return darkness_score
        except:
            return 0
    
    def search_unsplash(self, query, count=20):
        """Search Unsplash for high-quality dark wallpapers"""
        print(f"🔍 Searching Unsplash for: {query}")
        
        # Unsplash API (using public search)
        search_terms = [
            "dark night city skyline",
            "black minimal abstract",
            "dark space stars",
            "night cityscape neon",
            "dark ocean night",
            "black architecture",
            "dark forest night",
            "minimal dark geometric",
            "night tokyo cyberpunk",
            "dark mountain stars"
        ]
        
        results = []
        for term in search_terms[:5]:  # Limit to avoid rate limiting
            url = f"https://unsplash.com/napi/search/photos"
            params = {
                'query': term,
                'per_page': 10,
                'orientation': 'landscape'
            }
            
            try:
                response = requests.get(url, params=params, headers=self.headers)
                if response.status_code == 200:
                    data = response.json()
                    for photo in data.get('results', []):
                        # Get the high-res URL
                        raw_url = photo['urls']['raw']
                        # Customize for ultra-wide
                        download_url = f"{raw_url}&w=5120&h=1440&fit=crop&q=85"
                        
                        results.append({
                            'url': download_url,
                            'source': 'unsplash',
                            'description': photo.get('description', term),
                            'width': 5120,
                            'height': 1440
                        })
                        
                time.sleep(0.5)  # Be respectful
            except Exception as e:
                print(f"  Error: {e}")
                
        return results
    
    def search_wallhaven(self):
        """Search Wallhaven for dark wallpapers"""
        print("🔍 Searching Wallhaven...")
        
        # Wallhaven API
        base_url = "https://wallhaven.cc/api/v1/search"
        params = {
            'q': 'dark night',
            'categories': '100',  # General
            'purity': '100',      # SFW
            'sorting': 'relevance',
            'order': 'desc',
            'atleast': '5120x1440',
            'ratios': '32x9,21x9,16x9',
            'colors': '000000',  # Black/dark
            'page': 1
        }
        
        results = []
        try:
            response = requests.get(base_url, params=params, headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                for wall in data.get('data', [])[:15]:
                    results.append({
                        'url': wall['path'],
                        'source': 'wallhaven',
                        'description': f"wallhaven_{wall['id']}",
                        'width': wall['dimension_x'],
                        'height': wall['dimension_y']
                    })
        except Exception as e:
            print(f"  Error: {e}")
            
        return results
    
    def search_pexels(self):
        """Search Pexels for dark wallpapers"""
        print("🔍 Searching Pexels...")
        
        # Note: Pexels requires API key, using web scraping approach
        search_terms = ["dark wallpaper", "night city", "black minimal", "dark abstract"]
        results = []
        
        for term in search_terms[:3]:
            url = f"https://www.pexels.com/search/{quote(term)}/"
            params = {'orientation': 'landscape', 'size': 'large'}
            
            try:
                # This is a simplified approach - in production use their API
                response = requests.get(url, params=params, headers=self.headers)
                if response.status_code == 200:
                    # Extract image URLs from HTML (simplified regex approach)
                    img_pattern = r'"src":"(https://images\.pexels\.com/photos/[^"]+)"'
                    matches = re.findall(img_pattern, response.text)
                    
                    for img_url in matches[:5]:
                        # Modify URL for high resolution
                        hires_url = re.sub(r'\?.*', '?auto=compress&cs=tinysrgb&w=5120&h=1440&dpr=1', img_url)
                        results.append({
                            'url': hires_url,
                            'source': 'pexels',
                            'description': term,
                            'width': 5120,
                            'height': 1440
                        })
                        
                time.sleep(1)
            except Exception as e:
                print(f"  Error: {e}")
                
        return results
    
    def download_and_analyze(self, wallpaper_info, index):
        """Download and analyze a wallpaper"""
        try:
            print(f"  Downloading {index}: {wallpaper_info['description'][:30]}...")
            
            response = requests.get(wallpaper_info['url'], headers=self.headers, timeout=30)
            if response.status_code == 200:
                # Quick darkness check
                darkness = self.analyze_image_darkness(response.content)
                
                if darkness >= self.target_darkness:
                    # Save the dark image
                    filename = f"dark_{wallpaper_info['source']}_{index:03d}.jpg"
                    filepath = self.output_dir / filename
                    
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    
                    print(f"    ✓ Saved! Darkness: {darkness:.1f}%")
                    return True, darkness
                else:
                    print(f"    ✗ Too bright: {darkness:.1f}%")
                    return False, darkness
        except Exception as e:
            print(f"    ✗ Error: {e}")
            return False, 0
    
    def run(self):
        """Main scraper execution"""
        print("🌙 Ultra-Dark Wallpaper Scraper")
        print(f"📁 Output: {self.output_dir}")
        print("-" * 60)
        
        all_wallpapers = []
        
        # Gather from multiple sources
        all_wallpapers.extend(self.search_unsplash("dark"))
        all_wallpapers.extend(self.search_wallhaven())
        all_wallpapers.extend(self.search_pexels())
        
        print(f"\n📊 Found {len(all_wallpapers)} potential wallpapers")
        print("⬇️  Downloading and analyzing darkness levels...\n")
        
        downloaded = 0
        dark_enough = []
        
        for i, wall in enumerate(all_wallpapers[:30], 1):  # Limit to 30 to avoid too many downloads
            success, darkness = self.download_and_analyze(wall, i)
            if success:
                downloaded += 1
                dark_enough.append((wall, darkness))
                
            if downloaded >= 15:  # Stop after getting 15 dark ones
                break
                
            time.sleep(0.5)  # Be respectful to servers
        
        print("\n" + "=" * 60)
        print(f"✅ Downloaded {downloaded} ultra-dark wallpapers!")
        
        if dark_enough:
            print("\n🏆 Darkest wallpapers found:")
            dark_enough.sort(key=lambda x: x[1], reverse=True)
            for wall, darkness in dark_enough[:11]:
                print(f"  • {wall['description'][:40]:40} - Darkness: {darkness:.1f}%")
        
        return downloaded

def main():
    scraper = WallpaperScraper()
    count = scraper.run()
    
    if count >= 11:
        print("\n🎉 Success! You now have enough ultra-dark wallpapers!")
        print(f"📍 Location: {Path.home()}/Documents/desktops/scraped-wallpapers/")
    else:
        print(f"\n⚠️  Only found {count} dark wallpapers. You may need to:")
        print("   1. Adjust darkness threshold")
        print("   2. Search for more specific terms")
        print("   3. Try different wallpaper sites")

if __name__ == "__main__":
    main()