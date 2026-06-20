# Dark Glass — A Transparent Desktop Environment for GNOME/Ubuntu

A complete, portable desktop theme where every application layer is transparent black glass. Desktop wallpapers show through the terminal, file manager, and code editor. Built for Ubuntu 24.04 + GNOME Shell 46 on X11.

![concept](https://img.shields.io/badge/theme-dark_glass-000000?style=flat-square) ![platform](https://img.shields.io/badge/platform-Ubuntu_24.04-E95420?style=flat-square) ![de](https://img.shields.io/badge/DE-GNOME_46-4A86CF?style=flat-square)

## What You Get

- **Terminal** — GNOME Terminal with 42% transparent black background, green text (`rgb(150,213,162)`)
- **File manager** — Nemo with true-black surfaces at 82% compositor opacity, wallpaper visible through every window
- **Code editor** — VS Code with vibrancy + glass extensions, alpha-channel backgrounds on all surfaces
- **Wallpapers** — 11 dark sci-fi cityscapes (Midjourney v7 + Topaz upscale), one per workspace, auto-switching daemon
- **System** — Yaru-dark theme, `prefer-dark` color scheme, consistent green accent (`#96d5a2`) throughout

## Dependencies

### Tested Versions (known-good)

| Component | Version | Package |
|-----------|---------|---------|
| **OS** | Ubuntu 24.04.4 LTS | — |
| **Kernel** | 6.17.0-35-generic | — |
| **GNOME Shell** | 46.0 | `gnome-shell 46.0-0ubuntu6~24.04.14` |
| **Mutter** | 46.2 | `mutter-common 46.2-1ubuntu0.24.04.15` |
| **GTK3** | 3.24.41 | `libgtk-3-0t64 3.24.41-4ubuntu1.3` |
| **GTK4** | 4.14.5 | `libgtk-4-1 4.14.5+ds-0ubuntu0.10` |
| **X11 session** | x11 | — |
| **GPU driver** | NVIDIA 580.159.03 | — |
| **Bash** | 5.2.21 | — |

### Required Packages

```bash
sudo apt install gnome-shell gnome-terminal nemo wmctrl xdotool x11-utils xbindkeys
```

| Package | Version | Purpose |
|---------|---------|---------|
| `gnome-terminal` | 3.52.0 | Terminal with transparency support |
| `nemo` | 6.0.2 | File manager (glass effect target) |
| `wmctrl` | 1.07 | Workspace detection for wallpaper daemon |
| `xdotool` | 3.20160805.1 | Window search for nemo-glass opacity wrapper |
| `x11-utils` | 7.7+6 | Provides `xprop` for setting window opacity |
| `xbindkeys` | 1.8.7 | Custom keybinding (Ctrl+Space -> terminal) |

### GNOME Shell Extensions

Installed via `apt` on Ubuntu (or from [extensions.gnome.org](https://extensions.gnome.org) on other distros):

```bash
sudo apt install gnome-shell-extension-desktop-icons-ng gnome-shell-extension-appindicator gnome-shell-extension-ubuntu-dock
```

| Extension | Version | Package | Required? |
|-----------|---------|---------|-----------|
| `ding@rastersoft.com` (Desktop Icons NG) | 47.0.9 | `gnome-shell-extension-desktop-icons-ng 46+really47.0.9-1ubuntu5` | Yes — without it, no desktop icons; with it, the CSS `:not(.desktopwindow)` fix is critical |
| `tiling-assistant@ubuntu.com` | 46 | Ships with Ubuntu 24.04 | Optional — window tiling |
| `ubuntu-appindicators@ubuntu.com` | 58 | `gnome-shell-extension-appindicator 58-1ubuntu24.04.1` | Optional — system tray |
| `ubuntu-dock@ubuntu.com` | 90 | `gnome-shell-extension-ubuntu-dock 90ubuntu3` | Optional — dock |

After installing, enable:
```bash
gnome-extensions enable ding@rastersoft.com
gnome-extensions enable tiling-assistant@ubuntu.com
gnome-extensions enable ubuntu-appindicators@ubuntu.com
gnome-extensions enable ubuntu-dock@ubuntu.com
```

### VS Code (optional)

| Component | Version |
|-----------|---------|
| VS Code | 1.125.0 (x64) |
| `illixion.vscode-vibrancy-continued` | 1.1.81 |
| `s-nlf-fh.glassit` | 0.2.6 |
| `piousdeer.adwaita-theme` | 1.1.0 |
| `ms-python.python` | 2026.4.0 |
| `ms-python.vscode-pylance` | 2026.2.1 |
| `ms-python.debugpy` | 2026.6.0 |
| `ms-python.vscode-python-envs` | 1.36.0 |
| `ms-vscode-remote.remote-ssh` | 0.124.0 |
| `ms-vscode-remote.remote-ssh-edit` | 0.87.0 |
| `ms-vscode.remote-explorer` | 0.5.0 |

The theme extensions (`vscode-vibrancy-continued`, `glassit`, `adwaita-theme`) are required for the glass effect. The Python and Remote SSH extensions are development tools — install only if needed.

```bash
# Theme extensions only:
code --install-extension illixion.vscode-vibrancy-continued
code --install-extension s-nlf-fh.glassit
code --install-extension piousdeer.adwaita-theme

# All extensions:
cat configs/vscode-extensions.txt | xargs -L1 code --install-extension
```

---

## Quick Start

### Prerequisites

- Ubuntu 22.04+ or any GNOME 42-46 distro on X11 (Wayland partial — see Compatibility)
- Install required packages and extensions (see Dependencies above)
- VS Code (optional — skip Section 5 if not using it)

### Automated Install

```bash
git clone https://github.com/olympus-terminal/linux_desktop_customization.git
cd linux_desktop_customization
chmod +x restore.sh
./restore.sh --dry-run   # preview what will be changed
./restore.sh             # apply everything
```

Then log out and back in, or restart GNOME Shell: `killall -HUP gnome-shell`

### What `restore.sh` Does

| Step | Action | Files touched |
|------|--------|---------------|
| 1 | GTK3 dark-glass CSS | `~/.config/gtk-3.0/gtk.css` |
| 2 | VS Code settings + extensions | `~/.config/Code/User/settings.json` |
| 3 | Nemo glass wrapper script | `~/.local/bin/nemo-glass` |
| 4 | Wallpaper switching daemon | `~/Documents/desktops/workspace-wallpapers-fast.sh` |
| 5 | Autostart for wallpaper daemon | `~/.config/autostart/workspace-wallpapers.desktop` |
| 6 | Ctrl+Space keybinding | `~/.xbindkeysrc` |
| 7 | dconf databases (terminal, theme, Nemo, WM, extensions, background) | dconf user database |
| 8 | Wallpaper images (11 PNGs, ~119 MB) | `~/Documents/desktops/MJ7-Topaz/light-processed-dark20/` |
| 9 | System no-suspend override (needs sudo) | `/etc/dconf/db/local.d/00-no-suspend` |

### Manual / Selective Install

Pick the pieces you want:

**Theme only** (no wallpapers, no Nemo glass):
```bash
dconf load /org/gnome/desktop/interface/ < configs/gnome-desktop-interface.dconf
dconf load /org/gnome/terminal/ < configs/gnome-terminal.dconf
```

**VS Code only**:
```bash
cp configs/vscode-settings.json ~/.config/Code/User/settings.json
cat configs/vscode-extensions.txt | xargs -L1 code --install-extension
```

**Nemo glass only**:
```bash
cp configs/gtk-3.0-gtk.css ~/.config/gtk-3.0/gtk.css
cp configs/nemo-glass ~/.local/bin/nemo-glass && chmod +x ~/.local/bin/nemo-glass
dconf load /org/nemo/ < configs/nemo.dconf
# Launch with: nemo-glass [folder]
```

**Wallpapers only**:
```bash
mkdir -p ~/Documents/desktops/MJ7-Topaz/light-processed-dark20
cp wallpapers/*.png ~/Documents/desktops/MJ7-Topaz/light-processed-dark20/
cp configs/workspace-wallpapers-fast.sh ~/Documents/desktops/
chmod +x ~/Documents/desktops/workspace-wallpapers-fast.sh
cp configs/workspace-wallpapers.desktop ~/.config/autostart/
# Test: ~/Documents/desktops/workspace-wallpapers-fast.sh --test
```

---

## How Each Layer Works

### 1. System Theme

Dark mode everywhere via `prefer-dark` color scheme + Yaru-dark GTK theme. The dconf databases set:

| Setting | Value |
|---------|-------|
| GTK theme | `Yaru-dark` |
| Icon/cursor theme | `Yaru` |
| Color scheme | `prefer-dark` |
| Fonts | Ubuntu Sans 11 (UI), Ubuntu Sans Bold 11 (titlebar), Ubuntu Sans Mono 13 (mono) |
| Font rendering | rgba subpixel, slight hinting |
| Clock | 24h with date |

GNOME extensions used: DING (desktop icons), tiling-assistant, ubuntu-appindicators, ubuntu-dock.

### 2. GNOME Terminal

Black background with 42% transparency (compositor-rendered). Green foreground text matches the accent color. Standard 16-color palette.

| Setting | Value |
|---------|-------|
| Background | `rgb(0,0,0)`, 42% transparent |
| Foreground | `rgb(150,213,162)` |
| Size | 96x42 |
| Theme colors | custom (overridden) |

### 3. Nemo File Manager — Dark Glass

Two components work together:

**GTK3 CSS** (`~/.config/gtk-3.0/gtk.css`) — Sets all window surfaces to true black `#000000`. This is a global GTK3 override, so it affects all GTK3 apps. The key constraint is the `:not(.desktopwindow)` selector that prevents the DING desktop overlay from going opaque (see Troubleshooting).

**nemo-glass wrapper** (`~/.local/bin/nemo-glass`) — Launches Nemo and runs a background watcher that applies `_NET_WM_WINDOW_OPACITY` (82% opacity) on all Nemo windows via `xprop`. The watcher polls every 0.5s and self-terminates when Nemo exits. Opacity is configurable:
```bash
NEMO_GLASS_OPACITY=0.75 nemo-glass ~/Documents
```

To make `nemo-glass` the default file manager, set it in your `.desktop` file associations or launch via the alias.

### 4. Workspace Wallpapers

A bash daemon (`workspace-wallpapers-fast.sh`) polls `wmctrl` at 50ms intervals to detect workspace switches and sets the wallpaper via `gsettings`. Images from the wallpaper directory are assigned to workspaces in alphabetical order.

The daemon auto-starts at login via `~/.config/autostart/workspace-wallpapers.desktop`.

**Using your own wallpapers**: Replace the images in `~/Documents/desktops/MJ7-Topaz/light-processed-dark20/` with your own. Any `.jpg`, `.jpeg`, `.png`, `.bmp`, or `.tiff` files work. They're assigned to workspaces alphabetically — rename with numeric prefixes (e.g. `01-morning.png`, `02-night.png`) to control the order.

**Custom wallpaper directory**: Edit the `DEFAULT_BASE_DIR` and `IMAGE_DIR` variables in the script, or pass `--image-dir`:
```bash
./workspace-wallpapers-fast.sh --fast-poll --image-dir ~/Pictures/my-wallpapers
```

### 5. VS Code

Three extensions create the transparency stack:

| Extension | Role |
|-----------|------|
| `vscode-vibrancy-continued` | Blurs the window background for a frosted-glass effect |
| `glassit` | Sets window-level opacity (alpha 230/255) |
| `adwaita-theme` | Native GTK integration for consistent theming |

The `settings.json` overrides nearly every VS Code surface color with alpha-channel hex values (`#00000094` = black at ~58% opacity, `#00000000` = fully transparent). Widgets and menus use `#1e1e1ee6` (mostly opaque) for readability.

Token colors: green strings (`#85ff85`), cyan keywords (`#55ffff`), signature green functions (`#96d5a2`), muted comments (`#5c6370`).

**Note**: After installing `vscode-vibrancy-continued`, VS Code will prompt you to allow custom CSS injection. You must click "Allow" and restart VS Code.

---

## Compatibility

### Tested On

- Ubuntu 24.04 LTS, GNOME Shell 46.0, X11, NVIDIA RTX 4080 (driver 580)

### Should Work On

- Ubuntu 22.04+ / Fedora 38+ / any GNOME 42-46 distro on X11
- Any GPU with compositing support
- Displays of any resolution (wallpapers are 6513x1832 and 4096x1152 panoramics optimized for ultrawide; GNOME will zoom/crop for standard displays)

### Wayland Limitations

- **nemo-glass**: The `xprop`-based opacity wrapper requires X11. On Wayland, Nemo will render with the dark CSS but without transparency. A Wayland alternative would need a compositor-specific opacity rule (e.g. Mutter window rules or Sway/Hyprland `opacity` directives).
- **Wallpaper daemon**: `wmctrl` requires X11. On Wayland, replace with `gdbus` workspace monitoring.
- **xbindkeys**: X11 only. On Wayland, use GNOME custom keyboard shortcuts via `gsettings` or Settings > Keyboard.

### Adapting for Other Distros

- **Non-Ubuntu GTK themes**: Replace `Yaru-dark` / `Yaru` with your distro's dark theme in `configs/gnome-desktop-interface.dconf`. The glass effect comes from the CSS and compositor opacity, not the GTK theme itself.
- **Non-GNOME desktops**: The wallpaper daemon, GTK CSS, and Nemo wrapper are GNOME/GTK-specific. For KDE/Plasma, the transparency approach is completely different (use Kvantum themes + Plasma window rules).
- **Cinnamon**: Nemo is Cinnamon's native file manager, so the glass wrapper works. Replace GNOME-specific dconf paths with Cinnamon equivalents.

---

## Customization Guide

### Changing the Accent Color

The signature green (`rgb(150, 213, 162)` / `#96d5a2`) appears in three places:

1. **Terminal foreground**: `configs/gnome-terminal.dconf` — change `foreground-color`
2. **GTK3 selection highlight**: `configs/gtk-3.0-gtk.css` — change `rgba(150, 213, 162, 0.30)` in the selection rules
3. **VS Code**: `configs/vscode-settings.json` — change `functions` in `editor.tokenColorCustomizations` and the selection/hover colors in `workbench.colorCustomizations`

### Adjusting Transparency Levels

| Layer | Where | Default |
|-------|-------|---------|
| Terminal | `configs/gnome-terminal.dconf` — `background-transparency-percent` | 42% |
| Nemo | `NEMO_GLASS_OPACITY` env var or edit `OPACITY` in `configs/nemo-glass` | 0.82 (82%) |
| VS Code | `configs/vscode-settings.json` — `glassit.alpha` (0-255) | 230 |
| VS Code surfaces | Alpha channel in hex colors (`94` = 58%, `e6` = 90%, `00` = 0%) | varies |

### Using Different Wallpapers

Drop images into the wallpaper directory. The daemon assigns them to workspaces in alphabetical order. For best results:
- Use dark/moody images (light wallpapers clash with the dark glass)
- Match your display resolution or go larger (GNOME will zoom to fit)
- Use `.png` or `.jpg` under 50 MB per file
- Keep total image count to your number of workspaces or fewer

---

## Troubleshooting

### Black desktop — wallpaper is invisible

**Symptom**: Desktop is solid black. Wallpaper briefly flashes when GNOME Shell restarts but goes black again.

**Cause**: The GTK3 CSS rule `window.background { background-color: #000000 }` applies to the DING (Desktop Icons NG) extension's overlay window, painting it opaque black over the wallpaper.

**Fix**: Ensure all `window.background` rules in `~/.config/gtk-3.0/gtk.css` use the `:not(.desktopwindow)` exclusion:
```css
window.background:not(.desktopwindow) { background-color: #000000; }
```

**Diagnosis**: Run `pkill gjs` to kill DING. If the wallpaper appears and then goes black when DING respawns (~2 seconds), this is the issue.

### Wallpaper flashes then goes black

**Symptom**: When switching workspaces, the new wallpaper appears for an instant then the screen goes black.

**Cause**: The wallpaper daemon is using `dconf write` instead of `gsettings set`. GNOME Shell 46 monitors gsettings via D-Bus; raw dconf writes apply momentarily but the gsettings layer reasserts its (different) value.

**Fix**: The daemon must use `gsettings set org.gnome.desktop.background picture-uri` and `picture-uri-dark`.

### No wallpaper renders at all (even from GNOME Settings)

**Symptom**: Every wallpaper attempt results in black. Even the GNOME Settings > Appearance panel shows black.

**Cause**: Rapid wallpaper changes (e.g. daemon writing at 50ms intervals during boot) cancel GNOME Shell's image loading pipeline. The error `Failed to open sliced image: Operation was cancelled` appears in the journal. The background rendering actor gets stuck.

**Fix**: Restart GNOME Shell (safe — windows stay open):
```bash
killall -HUP gnome-shell
```

**Prevention**: The daemon should not re-set the wallpaper on every poll cycle. It should only write when the workspace actually changes or when the current wallpaper doesn't match the expected one.

### VS Code vibrancy not working

After installing `vscode-vibrancy-continued`, VS Code will show a warning about custom CSS modifications. You must:
1. Click "Allow" on the notification
2. Restart VS Code completely
3. If it still doesn't work, run VS Code with `--enable-features=UseOzonePlatform` or check that your compositor supports blur

### Nemo opens without transparency

- Ensure you're launching via `nemo-glass`, not plain `nemo`
- Check that `xdotool` and `xprop` are installed
- Verify compositing is enabled: `xprop -root | grep -i composite`
- On Wayland, the `xprop` approach won't work (see Compatibility section)

---

## File Reference

```
linux_desktop_customization/
  README.md                              # this file
  restore.sh                             # automated installer (supports --dry-run)
  configs/
    gtk-3.0-gtk.css                      # GTK3 dark-glass CSS (Nemo + all GTK3 apps)
    vscode-settings.json                 # VS Code settings with transparency
    vscode-extensions.txt                # VS Code extension list
    nemo-glass                           # Nemo transparency wrapper script
    workspace-wallpapers-fast.sh         # per-workspace wallpaper daemon
    workspace-wallpapers.desktop         # XDG autostart for wallpaper daemon
    xbindkeysrc                          # Ctrl+Space -> gnome-terminal
    gnome-terminal.dconf                 # terminal profile (colors, transparency, size)
    gnome-desktop-interface.dconf        # system theme, fonts, color scheme
    gnome-desktop-background.dconf       # wallpaper settings
    gnome-wm.dconf                       # window manager prefs (workspaces, titlebar)
    gnome-extensions.dconf               # GNOME Shell extension settings
    nemo.dconf                           # Nemo file manager preferences
    00-no-suspend                        # system dconf override (disable sleep/screensaver)
  wallpapers/                            # 11 dark sci-fi cityscape PNGs (~119 MB total)
    *.png
```

## For AI Agents Implementing This

If you are a Claude or other AI agent helping a user install this theme:

1. **Check prerequisites first**: Run `gnome-shell --version` to confirm GNOME 42-46, and `echo $XDG_SESSION_TYPE` to confirm X11 vs Wayland. If Wayland, warn about the limitations listed above.

2. **Back up before overwriting**: Before copying any config file, check if the target exists and back it up:
   ```bash
   [[ -f ~/.config/gtk-3.0/gtk.css ]] && cp ~/.config/gtk-3.0/gtk.css ~/.config/gtk-3.0/gtk.css.bak
   ```

3. **The GTK CSS is global**: `gtk-3.0/gtk.css` affects ALL GTK3 applications, not just Nemo. The user should understand that every GTK3 app will get true-black backgrounds. If they don't want this, skip the CSS and use Nemo's built-in dark mode instead (they'll lose the glass effect).

4. **The DING exclusion is critical**: If the user has the DING extension (default on Ubuntu), the `:not(.desktopwindow)` exclusion in the CSS is mandatory. Without it, the desktop will be solid black. This is the single most common issue.

5. **dconf paths are hardcoded to GNOME**: The dconf databases assume GNOME's schema paths. Don't load them on Cinnamon, KDE, or other DEs — the paths are different and it will either silently fail or write to wrong keys.

6. **Wallpaper paths in the autostart file are absolute**: The `.desktop` autostart file contains a hardcoded path to the user's home directory. After copying, update the `Exec=` line to match the actual install location.

7. **VS Code vibrancy requires user interaction**: The vibrancy extension modifies VS Code's internal CSS. After install, VS Code will show a "corrupt installation" warning — the user must click through this. You cannot automate this step.

8. **Test after each layer**: Don't apply everything at once and hope. Apply one layer, verify it works, then move to the next. Order: system theme -> terminal -> wallpapers -> Nemo glass -> VS Code.

9. **If wallpaper goes black after applying CSS**: This is the DING conflict. Fix the CSS `:not(.desktopwindow)` exclusion, then restart GNOME Shell with `killall -HUP gnome-shell`.

10. **The restore script is idempotent**: Running it multiple times is safe. It overwrites configs but doesn't accumulate state.
