#!/usr/bin/env python3
"""
Window Tiling Script for GNOME
Cycles through: full-screen → half-screen left → half-screen right → quarter screens
"""

import subprocess
import sys
import os
import json
from typing import Dict, List, Tuple, Optional

class WindowTiler:
    def __init__(self):
        self.state_file = os.path.expanduser("~/.window_tiler_state.json")
        self.window_states = self.load_state()
        
    def load_state(self) -> Dict:
        """Load window tiling state from file"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return {}
    
    def save_state(self):
        """Save window tiling state to file"""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.window_states, f)
        except Exception:
            pass
    
    def run_command(self, cmd: List[str]) -> Tuple[bool, str]:
        """Run a shell command and return success status and output"""
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return result.returncode == 0, result.stdout.strip()
        except Exception as e:
            return False, str(e)
    
    def get_active_window_id(self) -> Optional[str]:
        """Get the ID of the currently active window"""
        # Try wmctrl first
        success, output = self.run_command(['wmctrl', '-l'])
        if success:
            active_success, active_id = self.run_command(['xdotool', 'getactivewindow'])
            if active_success:
                return active_id.strip()
        
        # Fallback to gdbus for GNOME
        success, output = self.run_command([
            'gdbus', 'call', '--session',
            '--dest=org.gnome.Shell',
            '--object-path=/org/gnome/Shell',
            '--method=org.gnome.Shell.Eval',
            'global.get_window_actors().filter(a => a.meta_window.has_focus())[0].meta_window.get_id()'
        ])
        
        if success and output:
            # Parse the gdbus output
            try:
                import re
                match = re.search(r'\(true, \'(\d+)\'\)', output)
                if match:
                    return match.group(1)
            except:
                pass
        
        return None
    
    def get_screen_geometry(self) -> Tuple[int, int, int, int]:
        """Get screen dimensions (x, y, width, height)"""
        # Try xrandr first
        success, output = self.run_command(['xrandr', '--current'])
        if success:
            import re
            match = re.search(r'(\d+)x(\d+)\+0\+0', output)
            if match:
                width, height = int(match.group(1)), int(match.group(2))
                return 0, 0, width, height
        
        # Fallback to gdbus for GNOME
        success, output = self.run_command([
            'gdbus', 'call', '--session',
            '--dest=org.gnome.Shell',
            '--object-path=/org/gnome/Shell',
            '--method=org.gnome.Shell.Eval',
            'global.screen_width + "x" + global.screen_height'
        ])
        
        if success:
            try:
                import re
                match = re.search(r'\(true, \'(\d+)x(\d+)\'\)', output)
                if match:
                    width, height = int(match.group(1)), int(match.group(2))
                    return 0, 0, width, height
            except:
                pass
        
        # Default fallback
        return 0, 0, 1920, 1080
    
    def tile_window_wmctrl(self, window_id: str, x: int, y: int, width: int, height: int) -> bool:
        """Tile window using wmctrl"""
        success, _ = self.run_command([
            'wmctrl', '-i', '-r', window_id, 
            '-e', f'0,{x},{y},{width},{height}'
        ])
        return success
    
    def tile_window_gnome(self, x: int, y: int, width: int, height: int) -> bool:
        """Tile window using GNOME Shell extensions"""
        # Use keyboard shortcuts for common GNOME tiling
        if width == self.get_screen_geometry()[2]:  # Full width
            if height == self.get_screen_geometry()[3]:  # Full screen
                return self.run_command(['xdotool', 'key', 'F11'])[0]
        elif width == self.get_screen_geometry()[2] // 2:  # Half width
            if x == 0:  # Left half
                return self.run_command(['xdotool', 'key', 'Super_L+Left'])[0]
            else:  # Right half
                return self.run_command(['xdotool', 'key', 'Super_L+Right'])[0]
        
        # For other sizes, try to set window geometry directly
        cmd = [
            'gdbus', 'call', '--session',
            '--dest=org.gnome.Shell',
            '--object-path=/org/gnome/Shell',
            '--method=org.gnome.Shell.Eval',
            f'global.get_window_actors().filter(a => a.meta_window.has_focus())[0].meta_window.move_resize_frame(true, {x}, {y}, {width}, {height})'
        ]
        return self.run_command(cmd)[0]
    
    def get_next_tile_state(self, window_id: str) -> Tuple[int, int, int, int]:
        """Get the next tiling state for a window"""
        screen_x, screen_y, screen_width, screen_height = self.get_screen_geometry()
        
        current_state = self.window_states.get(window_id, 0)
        
        # Cycle through states: 0=full, 1=left_half, 2=right_half, 3=top_left, 4=top_right, 5=bottom_left, 6=bottom_right
        states = [
            # Full screen
            (screen_x, screen_y, screen_width, screen_height),
            # Left half
            (screen_x, screen_y, screen_width // 2, screen_height),
            # Right half
            (screen_x + screen_width // 2, screen_y, screen_width // 2, screen_height),
            # Top-left quarter
            (screen_x, screen_y, screen_width // 2, screen_height // 2),
            # Top-right quarter
            (screen_x + screen_width // 2, screen_y, screen_width // 2, screen_height // 2),
            # Bottom-left quarter
            (screen_x, screen_y + screen_height // 2, screen_width // 2, screen_height // 2),
            # Bottom-right quarter
            (screen_x + screen_width // 2, screen_y + screen_height // 2, screen_width // 2, screen_height // 2),
        ]
        
        next_state = (current_state + 1) % len(states)
        self.window_states[window_id] = next_state
        
        return states[next_state]
    
    def tile_active_window(self) -> bool:
        """Tile the currently active window to the next state"""
        window_id = self.get_active_window_id()
        if not window_id:
            print("Could not get active window ID")
            return False
        
        x, y, width, height = self.get_next_tile_state(window_id)
        
        # Try wmctrl first, then GNOME methods
        success = self.tile_window_wmctrl(window_id, x, y, width, height)
        if not success:
            success = self.tile_window_gnome(x, y, width, height)
        
        if success:
            self.save_state()
            state_name = ["Full Screen", "Left Half", "Right Half", "Top-Left Quarter", 
                         "Top-Right Quarter", "Bottom-Left Quarter", "Bottom-Right Quarter"][self.window_states[window_id]]
            print(f"Window tiled to: {state_name}")
        else:
            print("Failed to tile window")
        
        return success

def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print("Usage: python3 window_tiler.py")
        print("Cycles the active window through different tiling states:")
        print("  1. Full screen")
        print("  2. Left half")
        print("  3. Right half") 
        print("  4. Top-left quarter")
        print("  5. Top-right quarter")
        print("  6. Bottom-left quarter")
        print("  7. Bottom-right quarter")
        print()
        print("Dependencies (install with 'sudo apt-get install wmctrl xdotool'):")
        print("  - wmctrl (for window control)")
        print("  - xdotool (for keyboard simulation)")
        return
    
    tiler = WindowTiler()
    tiler.tile_active_window()

if __name__ == "__main__":
    main()