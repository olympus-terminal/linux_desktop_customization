#!/usr/bin/env python3
"""
Window Tiling Script for GNOME on Wayland
Uses gdbus to communicate with GNOME Shell
Cycles through: full-screen → half-screen left → half-screen right → quarter screens
"""

import subprocess
import sys
import os
import json
from typing import Dict, List, Tuple, Optional

class WaylandWindowTiler:
    def __init__(self):
        self.state_file = os.path.expanduser("~/.wayland_window_tiler_state.json")
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
    
    def run_gdbus_eval(self, js_code: str) -> Tuple[bool, str]:
        """Run JavaScript code in GNOME Shell via gdbus"""
        try:
            result = subprocess.run([
                'gdbus', 'call', '--session',
                '--dest=org.gnome.Shell',
                '--object-path=/org/gnome/Shell',
                '--method=org.gnome.Shell.Eval',
                js_code
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                # Parse gdbus output: (true, 'result') or (false, 'error')
                output = result.stdout.strip()
                if output.startswith('(true,'):
                    return True, output[7:-2]  # Extract result between quotes
                elif output.startswith('(false,'):
                    return False, output[8:-2]  # Extract error between quotes
            return False, result.stderr
        except Exception as e:
            return False, str(e)
    
    def get_active_window_info(self) -> Optional[Dict]:
        """Get information about the currently active window"""
        js_code = """
        let activeWindow = global.display.focus_window;
        if (!activeWindow) {
            'null';
        } else {
            JSON.stringify({
                id: activeWindow.get_id(),
                title: activeWindow.get_title(),
                rect: {
                    x: activeWindow.get_frame_rect().x,
                    y: activeWindow.get_frame_rect().y,
                    width: activeWindow.get_frame_rect().width,
                    height: activeWindow.get_frame_rect().height
                },
                maximized: activeWindow.maximized_horizontally && activeWindow.maximized_vertically,
                monitor: activeWindow.get_monitor()
            });
        }
        """
        
        success, result = self.run_gdbus_eval(js_code)
        if success and result != 'null':
            try:
                return json.loads(result)
            except:
                pass
        return None
    
    def get_monitor_geometry(self, monitor_index: int = 0) -> Tuple[int, int, int, int]:
        """Get monitor dimensions"""
        js_code = f"""
        let monitor = global.display.get_monitor_geometry({monitor_index});
        if (monitor) {{
            JSON.stringify({{
                x: monitor.x,
                y: monitor.y,
                width: monitor.width,
                height: monitor.height
            }});
        }} else {{
            'null';
        }}
        """
        
        success, result = self.run_gdbus_eval(js_code)
        if success and result != 'null':
            try:
                geom = json.loads(result)
                return geom['x'], geom['y'], geom['width'], geom['height']
            except:
                pass
        
        # Default fallback
        return 0, 0, 1920, 1080
    
    def tile_window(self, window_id: str, x: int, y: int, width: int, height: int, maximize: bool = False) -> bool:
        """Tile a window to specific coordinates"""
        if maximize:
            js_code = f"""
            let windows = global.get_window_actors();
            let window = null;
            for (let w of windows) {{
                if (w.meta_window.get_id() == {window_id}) {{
                    window = w.meta_window;
                    break;
                }}
            }}
            if (window) {{
                window.unmaximize(Meta.MaximizeFlags.BOTH);
                window.maximize(Meta.MaximizeFlags.BOTH);
                'success';
            }} else {{
                'window not found';
            }}
            """
        else:
            js_code = f"""
            let windows = global.get_window_actors();
            let window = null;
            for (let w of windows) {{
                if (w.meta_window.get_id() == {window_id}) {{
                    window = w.meta_window;
                    break;
                }}
            }}
            if (window) {{
                window.unmaximize(Meta.MaximizeFlags.BOTH);
                window.move_resize_frame(false, {x}, {y}, {width}, {height});
                'success';
            }} else {{
                'window not found';
            }}
            """
        
        success, result = self.run_gdbus_eval(js_code)
        return success and result == 'success'
    
    def get_next_tile_state(self, window_id: str, monitor_geom: Tuple[int, int, int, int]) -> Tuple[int, int, int, int, bool]:
        """Get the next tiling state for a window"""
        screen_x, screen_y, screen_width, screen_height = monitor_geom
        
        # Account for GNOME's top bar (usually 28-35 pixels)
        top_bar_height = 35
        usable_y = screen_y + top_bar_height
        usable_height = screen_height - top_bar_height
        
        current_state = self.window_states.get(window_id, 0)
        
        # Cycle through states with proper coordinates
        states = [
            # Full screen (maximize)
            (screen_x, screen_y, screen_width, screen_height, True),
            # Left half
            (screen_x, usable_y, screen_width // 2, usable_height, False),
            # Right half
            (screen_x + screen_width // 2, usable_y, screen_width // 2, usable_height, False),
            # Top-left quarter
            (screen_x, usable_y, screen_width // 2, usable_height // 2, False),
            # Top-right quarter
            (screen_x + screen_width // 2, usable_y, screen_width // 2, usable_height // 2, False),
            # Bottom-left quarter
            (screen_x, usable_y + usable_height // 2, screen_width // 2, usable_height // 2, False),
            # Bottom-right quarter
            (screen_x + screen_width // 2, usable_y + usable_height // 2, screen_width // 2, usable_height // 2, False),
        ]
        
        next_state = (current_state + 1) % len(states)
        self.window_states[window_id] = next_state
        
        return states[next_state]
    
    def tile_active_window(self) -> bool:
        """Tile the currently active window to the next state"""
        window_info = self.get_active_window_info()
        if not window_info:
            print("Could not get active window information")
            return False
        
        window_id = str(window_info['id'])
        monitor_index = window_info.get('monitor', 0)
        monitor_geom = self.get_monitor_geometry(monitor_index)
        
        x, y, width, height, maximize = self.get_next_tile_state(window_id, monitor_geom)
        
        success = self.tile_window(window_id, x, y, width, height, maximize)
        
        if success:
            self.save_state()
            state_names = ["Full Screen", "Left Half", "Right Half", "Top-Left Quarter", 
                          "Top-Right Quarter", "Bottom-Left Quarter", "Bottom-Right Quarter"]
            state_name = state_names[self.window_states[window_id]]
            print(f"Window '{window_info['title']}' tiled to: {state_name}")
        else:
            print("Failed to tile window")
        
        return success

def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print("Wayland Window Tiler for GNOME")
        print("Usage: python3 wayland_window_tiler.py")
        print()
        print("Cycles the active window through different tiling states:")
        print("  1. Full screen (maximized)")
        print("  2. Left half")
        print("  3. Right half") 
        print("  4. Top-left quarter")
        print("  5. Top-right quarter")
        print("  6. Bottom-left quarter")
        print("  7. Bottom-right quarter")
        print()
        print("This script uses GNOME Shell's JavaScript API via gdbus")
        print("and works on Wayland sessions.")
        return
    
    # Check if we're on Wayland
    if os.environ.get('XDG_SESSION_TYPE') != 'wayland':
        print("Warning: Not running on Wayland. This script is designed for Wayland sessions.")
    
    tiler = WaylandWindowTiler()
    tiler.tile_active_window()

if __name__ == "__main__":
    main()