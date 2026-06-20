# Linux Desktop Customization — Portable Reference

Complete state of the dark-glass desktop environment as of 2026-06-20.
Machine: ADUAED16433LPLX, Ubuntu 24.04, GNOME Shell 46.0, NVIDIA RTX 4080 Laptop (driver 580.159), X11.

## Design Philosophy

Every layer is transparent black glass. The desktop wallpapers (dark sci-fi cityscapes) show through the terminal, file manager, and code editor. Selection highlights use a signature green (`rgb(150, 213, 162)`). The entire stack is dark-mode, true-black surfaces with compositor-level opacity.

---

## 1. System Theme & Appearance

| Setting | Value |
|---------|-------|
| GTK theme | `Yaru-dark` |
| Icon theme | `Yaru` |
| Cursor theme | `Yaru` |
| Color scheme | `prefer-dark` |
| UI font | `Ubuntu Sans 11` |
| Titlebar font | `Ubuntu Sans Bold 11` |
| Monospace font | `Ubuntu Sans Mono 13` |
| Document font | `Sans 11` |
| Font rendering | rgba subpixel, slight hinting |
| Clock | 24h with date |
| Animations | enabled |
| Hot corners | disabled |
| Shell theme | default (no custom) |

### GNOME Extensions (enabled)

| Extension | Purpose |
|-----------|---------|
| `ding@rastersoft.com` | Desktop Icons NG — transparent desktop icon overlay |
| `tiling-assistant@ubuntu.com` | Window tiling |
| `ubuntu-appindicators@ubuntu.com` | System tray indicators |
| `ubuntu-dock@ubuntu.com` | Dock |

### System-level dconf overrides (`/etc/dconf/db/local.d/00-no-suspend`)

```ini
[org/gnome/settings-daemon/plugins/power]
sleep-inactive-ac-type='nothing'
sleep-inactive-battery-type='nothing'

[org/gnome/desktop/session]
idle-delay=uint32 0

[org/gnome/desktop/screensaver]
idle-activation-enabled=false
```

### Keybinding (`~/.xbindkeysrc`)

```
"gnome-terminal"
  Control + space
```

---

## 2. Workspace Wallpapers

Per-workspace wallpapers via a polling daemon that auto-starts at login.

### How it works

- **Daemon**: `~/Documents/desktops/workspace-wallpapers-fast.sh --fast-poll`
- **Autostart**: `~/.config/autostart/workspace-wallpapers.desktop`
- **Image source**: `~/Documents/desktops/MJ7-Topaz/light-processed-dark20/` (11 images, ~118 MB total)
- **Images**: Midjourney v7 dark futuristic cityscapes, Topaz upscaled to 6513x1832 or 4096x1152 (panoramic for 3840x1080 super-ultrawide)
- **Mechanism**: Polls `wmctrl` at 50ms intervals, sets wallpaper via `gsettings set org.gnome.desktop.background picture-uri[-dark]`
- **Workspaces**: 4 (dynamic workspaces enabled, so GNOME can add more)

### Critical fix: DING + dark-glass CSS conflict

The GTK3 dark-glass CSS (`~/.config/gtk-3.0/gtk.css`) sets `window.background { background-color: #000000 }` for the Nemo glass effect. This also hits DING's desktop overlay window, painting it opaque black and hiding the wallpaper.

**Fix**: All `window.background` rules must use `:not(.desktopwindow)` to exclude DING:
```css
window.background:not(.desktopwindow) { background-color: #000000; }
```

### Critical fix: gsettings vs dconf

The daemon must use `gsettings set` (not `dconf write`) to change wallpapers. GNOME Shell 46 monitors gsettings change notifications via D-Bus — raw `dconf write` applies briefly but gets overwritten by the stale gsettings value, causing a flash-then-black.

### Autostart file (`~/.config/autostart/workspace-wallpapers.desktop`)

```ini
[Desktop Entry]
Type=Application
Name=Workspace Wallpapers
Comment=Automatically change wallpapers when switching workspaces
Exec=/home/drn2/Documents/desktops/workspace-wallpapers-fast.sh --fast-poll
Icon=preferences-desktop-wallpaper
Terminal=false
Categories=Utility;
StartupNotify=false
X-GNOME-Autostart-enabled=true
```

---

## 3. GNOME Terminal

| Setting | Value |
|---------|-------|
| Background | `rgb(0,0,0)` with 42% transparency |
| Foreground | `rgb(150,213,162)` (signature green) |
| Default size | 96 columns x 42 rows |
| Theme colors | overridden (custom) |
| GPU acceleration | N/A (uses system compositor) |

### Color palette (16 standard colors)

```
 0 rgb(0,0,0)         8 rgb(85,85,85)
 1 rgb(170,0,0)       9 rgb(255,85,85)
 2 rgb(0,170,0)      10 rgb(85,255,85)
 3 rgb(170,85,0)     11 rgb(255,255,85)
 4 rgb(0,0,170)      12 rgb(85,85,255)
 5 rgb(170,0,170)    13 rgb(255,85,255)
 6 rgb(0,170,170)    14 rgb(85,255,255)
 7 rgb(170,170,170)  15 rgb(255,255,255)
```

### Apply via dconf

```bash
dconf load /org/gnome/terminal/ < configs/gnome-terminal.dconf
```

---

## 4. Nemo File Manager (Dark Glass)

Two components create the glass effect:

### 4a. GTK3 CSS (`~/.config/gtk-3.0/gtk.css`)

Sets all Nemo surfaces to true black `#000000`. The compositor then applies partial opacity to make the wallpaper show through. Selection highlight is `rgba(150, 213, 162, 0.30)`.

**Important**: The `:not(.desktopwindow)` exclusion on `window.background` rules is required to avoid breaking DING's desktop overlay (see Section 2).

### 4b. nemo-glass wrapper (`~/.local/bin/nemo-glass`)

Launches Nemo and runs a background watcher (polls every 0.5s) that sets `_NET_WM_WINDOW_OPACITY` on all Nemo windows to 82% opacity. Self-terminates when Nemo exits. Opacity is configurable via `NEMO_GLASS_OPACITY` env var.

### Nemo preferences (non-default)

| Setting | Value |
|---------|-------|
| Default view | list-view |
| Sort by | modification time, newest first |
| Directories first | yes |
| Ignore view metadata | yes (global view always used) |
| Visible columns | name, size, date_modified |
| Desktop icons | enabled (but all individual icons hidden) |
| Ignored desktop handlers | conky, csd-background |

---

## 5. VS Code

### Theme stack

| Layer | Value |
|-------|-------|
| Base theme | `Dark+` |
| Vibrancy | `vscode-vibrancy-continued` — type: `under-window`, theme: `Dark (Only Subbar)`, opacity: `-1` |
| Glass | `glassit` — alpha: `230` |
| Adwaita | `piousdeer.adwaita-theme` (for native GTK integration) |

### Color overrides (`workbench.colorCustomizations`)

All editor surfaces use alpha channels for see-through:

| Surface | Color |
|---------|-------|
| Editor background | `#00000094` |
| Sidebar background | `#00000094` |
| Activity bar | `#00000094` |
| Title bar | `#00000000` (fully transparent) |
| Active tab | `#00000000` |
| Inactive tab | `#00000094` |
| Terminal background | `#00000000` |
| Panel background | `#00000000` |
| Status bar | `#00000000` |
| Widgets/menus | `#1e1e1ee6` (mostly opaque for readability) |
| Selection | `#1a3a1a` |
| Hover | `#0d1f0d` |

### Token colors

| Token | Color |
|-------|-------|
| Comments | `#5c6370` |
| Strings | `#85ff85` |
| Keywords | `#55ffff` |
| Functions | `#96d5a2` (signature green) |

### Editor settings

| Setting | Value |
|---------|-------|
| Font | `Liberation Mono, monospace` |
| Minimap | disabled |
| Breadcrumbs | disabled |
| Activity bar | hidden |
| Status bar | hidden |
| Title bar | custom |
| Menu bar | toggle |
| GPU acceleration (terminal) | off |

### Extensions

```
illixion.vscode-vibrancy-continued
ms-python.debugpy
ms-python.python
ms-python.vscode-pylance
ms-python.vscode-python-envs
ms-vscode-remote.remote-ssh
ms-vscode-remote.remote-ssh-edit
ms-vscode.remote-explorer
piousdeer.adwaita-theme
s-nlf-fh.glassit
```

---

## 6. Shell Aliases & Environment

### Key aliases (`~/.bashrc`)

| Alias | Command |
|-------|---------|
| `jubail` | SSH to NYU Abu Dhabi HPC |
| `cl` | Launch Claude Code (Opus, skip permissions) |
| `d` | Dictation/TTS via conda env |
| `c` | Activate circos_gorilla conda env |
| `up` | `sudo apt update && sudo apt upgrade -y` |
| `l` | `ls -lthr` |
| `vpn` / `vpn2` | NYU Abu Dhabi VPN split tunnel |
| `hitme` | Play random MP3 from current dir |
| `obs` | Launch Obsidian AppImage |
| `spark1` | SSH to DGX Spark |
| `cla` | Copy GreatClaudeConfig.md template to cwd |
| `fig` | Copy FIGURE_PROTOCOL_v1.2.md template to cwd |

### Environment

| Variable | Value |
|----------|-------|
| `GOPATH` | `$HOME/go` |
| `CUDA` | `/usr/local/cuda-12.2` (bin + lib64) |
| `BLASTDB` | `/data/blastdb` |
| `NVM_DIR` | `$HOME/.nvm` |
| `NO_PROXY` | `api.anthropic.com,statsig.anthropic.com,sentry.io,localhost,127.0.0.1` |
| Conda | miniconda3 (auto-initialized) |
| Deno | `$HOME/.deno/bin` in PATH |

---

## Portability / Restore Checklist

1. **System packages**: `gnome-shell`, `gnome-terminal`, `nemo`, `wmctrl`, `xdotool`, `xprop`, `imagemagick` (for `identify`)
2. **GNOME extensions**: Install `ding@rastersoft.com`, `tiling-assistant@ubuntu.com`, `ubuntu-appindicators@ubuntu.com`, `ubuntu-dock@ubuntu.com`
3. **Copy config files** (all paths relative to `$HOME`):
   - `.config/gtk-3.0/gtk.css`
   - `.config/Code/User/settings.json`
   - `.config/autostart/workspace-wallpapers.desktop`
   - `.local/bin/nemo-glass`
   - `.xbindkeysrc`
   - Wallpaper images to `Documents/desktops/MJ7-Topaz/light-processed-dark20/`
   - `Documents/desktops/workspace-wallpapers-fast.sh`
4. **Load dconf settings**:
   ```bash
   dconf load /org/gnome/terminal/ < configs/gnome-terminal.dconf
   dconf load /org/gnome/desktop/interface/ < configs/gnome-desktop-interface.dconf
   dconf load /org/gnome/desktop/background/ < configs/gnome-desktop-background.dconf
   dconf load /org/nemo/ < configs/nemo.dconf
   dconf load /org/gnome/shell/extensions/ < configs/gnome-extensions.dconf
   dconf load /org/gnome/desktop/wm/preferences/ < configs/gnome-wm.dconf
   ```
5. **Set dark mode**: `gsettings set org.gnome.desktop.interface color-scheme 'prefer-dark'`
6. **Install VS Code extensions**:
   ```bash
   cat configs/vscode-extensions.txt | xargs -L1 code --install-extension
   ```
7. **Make scripts executable**: `chmod +x ~/Documents/desktops/workspace-wallpapers-fast.sh ~/.local/bin/nemo-glass`
8. **System overrides** (requires sudo): Copy `configs/00-no-suspend` to `/etc/dconf/db/local.d/` and run `sudo dconf update`

---

## Known Issues & Fixes

### Black desktop (wallpaper invisible)

**Cause**: `~/.config/gtk-3.0/gtk.css` rule `window.background { background-color: #000000 }` applies to DING's desktop overlay, painting it opaque black over the wallpaper.

**Fix**: Use `window.background:not(.desktopwindow)` on all rules.

**Diagnosis**: Kill DING (`pkill gjs`) — if wallpaper flashes then goes black when DING respawns, this is the issue.

### Wallpaper flashes then goes black

**Cause**: Wallpaper daemon using `dconf write` instead of `gsettings set`. GNOME Shell 46 monitors gsettings via D-Bus; raw dconf writes apply momentarily but get overwritten.

**Fix**: Use `gsettings set org.gnome.desktop.background picture-uri` in the daemon.

### GNOME Shell background stuck (no wallpaper renders at all)

**Cause**: Rapid wallpaper changes at boot cancel image loads ("Failed to open sliced image: Operation was cancelled" in `journalctl`). Background actor gets stuck.

**Fix**: `killall -HUP gnome-shell` (restarts compositor without closing windows).
