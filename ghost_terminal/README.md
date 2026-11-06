<p align="center">
  <img src="assets/banner.png" alt="ghost_terminal banner" width="100%">
</p>

# ghost_terminal

Widescreen dark desktop environment for GNOME: transparent black terminals, sci-fi wallpapers, workspace-aware wallpaper switching, and window tiling. Built for ultrawide (5120x1440) displays.

## Quick Install

```bash
git clone git@github.com:olympus-terminal/ghost_terminal.git
cd ghost_terminal
./install.sh
```

This will:
- Load the transparent terminal profile (black bg, 42% transparency, green text)
- Set GNOME to dark mode
- Install 65+ dark/sci-fi wallpapers
- Set up workspace wallpaper daemon (auto-starts on login)
- Configure 11 static workspaces with tiling shortcuts

## The Terminal

- **Background:** Pure black `rgb(0,0,0)` with 42% transparency
- **Text:** Light green `rgb(150,213,162)`
- **Window size:** 96 columns x 42 rows

### Manual profile install

```bash
dconf load /org/gnome/terminal/legacy/profiles:/ < profiles/gnome-terminal.dconf
```

## Wallpapers

Four collections optimized for ultrawide displays:

| Directory | Count | Description |
|-----------|-------|-------------|
| `wallpapers/ultrawide/` | 20 | 5120x1440 dark cityscapes, stars, skylines |
| `wallpapers/cyberpunk-cities/` | 11 | Midjourney + Topaz AI megacities, biodomes, rain |
| `wallpapers/dark-scraped/` | 27 | WallHaven dark urban, jungle, plants |
| `wallpapers/dark-variants/` | 7 | Extra-darkened versions (84-98% black) |

All wallpapers score 70%+ darkness for eye comfort on OLED and IPS panels.

## Workspace Wallpaper Daemon

Each of 11 workspaces gets its own wallpaper. The daemon listens for D-Bus workspace-change signals and swaps instantly (no polling).

```bash
# Start manually
./daemon/workspace-wallpapers-fast.sh &

# The installer sets this up to auto-start on login via:
# ~/.config/autostart/workspace-wallpapers.desktop
```

## Window Tiling

Press `Super+T` to cycle through 7 tiling states:

1. Full screen (maximized)
2. Left half
3. Right half
4. Top-left quarter
5. Top-right quarter
6. Bottom-left quarter
7. Bottom-right quarter

### Setup

```bash
# Wayland (recommended)
./scripts/install_tiling_extension.sh

# Or manually
cp scripts/wayland_window_tiler.py ~/.local/bin/gnome-window-tiler
chmod +x ~/.local/bin/gnome-window-tiler
```

### Native GNOME shortcuts

After running `scripts/setup_native_tiling.sh`:

| Shortcut | Action |
|----------|--------|
| Super+Left | Tile left half |
| Super+Right | Tile right half |
| Super+Up | Maximize |
| Super+Down | Restore |

## Tools

Utilities for expanding and managing the wallpaper collection:

| Tool | Purpose |
|------|---------|
| `tools/wallpaper_scraper.py` | Download dark wallpapers from Unsplash/WallHaven |
| `tools/targeted_scraper.py` | Scrape cyberpunk/sci-fi themed wallpapers |
| `tools/darken_wallpapers.py` | Reduce brightness on too-bright images |
| `tools/analyze_wallpapers.py` | Score wallpapers by darkness, resolution, aspect ratio |
| `tools/preview_and_filter.py` | Preview and filter candidates |
| `tools/process_topaz_light.py` | Process Topaz-upscaled images |

## File Structure

```
ghost_terminal/
├── install.sh                         # One-shot setup script
├── profiles/
│   └── gnome-terminal.dconf           # Terminal transparency + colors
├── scripts/
│   ├── wayland_window_tiler.py        # Wayland tiling (gdbus)
│   ├── window_tiler.py                # X11 tiling (wmctrl/xdotool)
│   ├── install_tiling_extension.sh    # Super+T keybinding setup
│   └── setup_native_tiling.sh         # GNOME native tiling shortcuts
├── wallpapers/
│   ├── ultrawide/                     # 5120x1440 dark wallpapers
│   ├── cyberpunk-cities/              # AI-generated megacities
│   ├── dark-scraped/                  # WallHaven dark collection
│   └── dark-variants/                 # Extra-darkened versions
├── daemon/
│   ├── workspace-wallpapers-fast.sh   # Event-driven workspace wallpaper switcher
│   └── workspace-wallpapers.sh        # Fallback polling-based switcher
├── tools/
│   ├── wallpaper_scraper.py
│   ├── targeted_scraper.py
│   ├── darken_wallpapers.py
│   ├── analyze_wallpapers.py
│   ├── preview_and_filter.py
│   └── process_topaz_light.py
└── autostart/
    └── workspace-wallpapers.desktop   # Login autostart entry
```

## Requirements

- Ubuntu GNOME (tested on GNOME Shell 46)
- Wayland or X11
- `wmctrl`, `xdotool` (for X11 tiling)
- Python 3 with Pillow (for wallpaper tools)
