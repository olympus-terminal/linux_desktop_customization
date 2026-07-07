#!/usr/bin/env python3
"""
Targeted Wallpaper Scraper
Focuses on: Exotic city skylines, dark jungle/plants, and space themes
"""

import requests
import os
import time
from pathlib import Path
import io
from PIL import Image
import numpy as np

class TargetedScraper:
    def __init__(self):
        self.output_dir = Path.home() / 'Documents' / 'desktops' / 'scraped-wallpapers'
        self.output_dir.mkdir(exist_ok=True)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        }
        self.min_darkness = 65
        
    def analyze_darkness(self, img_data):
        """Quick darkness check"""
        try:
            img = Image.open(io.BytesIO(img_data))
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img.thumbnail((400, 400))
            img_array = np.array(img)
            avg_brightness = np.mean(img_array)
            darkness_score = 100 - (avg_brightness / 255 * 100)
            return darkness_score
        except:
            return 0
    
    def scrape_wallhaven_targeted(self):
        """Search Wallhaven with specific queries"""
        print("🔍 Searching Wallhaven for targeted themes...")
        
        # Specific search queries for our themes
        queries = [
            # Exotic city skylines
            ("skyline night neon", "city"),
            ("tokyo skyline dark", "city"),
            ("cyberpunk city skyline", "city"),
            ("hong kong skyline night", "city"),
            ("dubai skyline night", "city"),
            ("singapore skyline dark", "city"),
            
            # Dark jungle/plants
            ("dark jungle", "jungle"),
            ("tropical plants dark", "jungle"),
            ("rainforest night", "jungle"),
            ("dark leaves", "plants"),
            ("monstera dark", "plants"),
            ("dark botanical", "plants"),
            
            # Space themes
            ("deep space", "space"),
            ("nebula dark", "space"),
            ("galaxy black", "space"),
            ("stars night sky", "space"),
            ("cosmos dark", "space"),
            ("milky way", "space")
        ]
        
        results = []
        existing_files = list(self.output_dir.glob('*.jpg'))
        next_index = len(existing_files) + 1
        
        for query, theme in queries[:10]:  # Limit to avoid too many requests
            print(f"  Searching: {query}")
            
            base_url = "https://wallhaven.cc/api/v1/search"
            params = {
                'q': query,
                'categories': '100',
                'purity': '100',
                'sorting': 'relevance',
                'order': 'desc',
                'atleast': '3840x1080',  # Minimum resolution
                'ratios': '32x9,21x9,16x9',
                'page': 1
            }
            
            try:
                response = requests.get(base_url, params=params, headers=self.headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    
                    for wall in data.get('data', [])[:3]:  # Get top 3 from each query
                        # Check resolution
                        if wall['dimension_x'] >= 3840:
                            results.append({
                                'url': wall['path'],
                                'theme': theme,
                                'query': query,
                                'width': wall['dimension_x'],
                                'height': wall['dimension_y'],
                                'index': next_index
                            })
                            next_index += 1
                            
                time.sleep(1)  # Be respectful
            except Exception as e:
                print(f"    Error: {e}")
                
        return results
    
    def download_and_filter(self, wallpaper_info):
        """Download and check darkness"""
        try:
            print(f"  Downloading {wallpaper_info['theme']}: {wallpaper_info['query'][:20]}...")
            
            response = requests.get(wallpaper_info['url'], headers=self.headers, timeout=30)
            if response.status_code == 200:
                darkness = self.analyze_darkness(response.content)
                
                if darkness >= self.min_darkness:
                    filename = f"dark_wallhaven_{wallpaper_info['index']:03d}_{wallpaper_info['theme']}.jpg"
                    filepath = self.output_dir / filename
                    
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    
                    print(f"    ✓ Saved! {wallpaper_info['theme'].upper()} - Darkness: {darkness:.1f}%")
                    return True, darkness
                else:
                    print(f"    ✗ Too bright ({darkness:.1f}%) - Skipping")
                    return False, darkness
        except Exception as e:
            print(f"    ✗ Error: {e}")
            return False, 0
    
    def run(self):
        """Main execution"""
        print("🎯 Targeted Wallpaper Scraper")
        print("🌃 Themes: Exotic city skylines, Dark jungle/plants, Space")
        print(f"📁 Output: {self.output_dir}")
        print("-" * 60)
        
        # Search for wallpapers
        wallpapers = self.scrape_wallhaven_targeted()
        
        print(f"\n📊 Found {len(wallpapers)} potential wallpapers")
        print("⬇️  Downloading dark ones only...\n")
        
        downloaded = 0
        by_theme = {'city': 0, 'jungle': 0, 'plants': 0, 'space': 0}
        
        for wall in wallpapers:
            success, darkness = self.download_and_filter(wall)
            if success:
                downloaded += 1
                by_theme[wall['theme']] += 1
                
            if downloaded >= 15:  # Stop after getting enough
                break
                
            time.sleep(0.5)
        
        print("\n" + "=" * 60)
        print(f"✅ Downloaded {downloaded} wallpapers!")
        print("\n📊 By theme:")
        for theme, count in by_theme.items():
            if count > 0:
                print(f"  • {theme.capitalize()}: {count}")
        
        return downloaded

def main():
    scraper = TargetedScraper()
    count = scraper.run()
    
    if count > 0:
        print(f"\n🎉 Success! Added {count} new themed wallpapers")
        print("   Themes: Exotic skylines, Dark jungle/plants, Space")
    else:
        print("\n⚠️  No new wallpapers found. Try adjusting darkness threshold.")

if __name__ == "__main__":
    main()