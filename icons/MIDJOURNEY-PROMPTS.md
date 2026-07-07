# Dark-Glass Icon Prompts for Midjourney

Style reference: the existing `terminal-glass` and `nemo-glass` icons — dark translucent
glass panel with soft cyan/teal edge glow, minimal symbol in the center, near-black
background, flat icon style, no perspective distortion.

Generate each at **1024x1024** (square), then resize down to the required sizes.

---

## 1. Settings (gear icon)

```
dark translucent glass gear icon, minimal flat design, soft cyan teal edge glow,
dark matte background, single gear symbol etched into frosted glass panel, subtle
inner light refraction, app icon style, square format, no text, no shadow --s 250
--style raw --ar 1:1
```

**Install as:** `settings-glass` → override `org.gnome.Settings` in `.desktop` file

---

## 2. Media Player (music/play icon)

```
dark translucent glass music player icon, minimal flat design, soft cyan teal edge
glow, dark matte background, play triangle and music note symbol etched into frosted
glass panel, subtle inner light refraction, app icon style, square format, no text,
no shadow --s 250 --style raw --ar 1:1
```

**Install as:** `rhythmbox-glass` → override `org.gnome.Rhythmbox3` in `.desktop` file

---

## 3. External Drive (USB/removable media icon)

```
dark translucent glass USB drive icon, minimal flat design, soft cyan teal edge glow,
dark matte background, portable hard drive symbol etched into frosted glass panel,
subtle inner light refraction, app icon style, square format, no text, no shadow
--s 250 --style raw --ar 1:1
```

**Install as:** `drive-removable-media.png` in `hicolor/*/devices/` (theme override, no `.desktop` file needed)

---

## 4a. Trash — Empty

```
dark translucent glass trash bin icon empty, minimal flat design, soft cyan teal edge
glow, dark matte background, empty wastepaper basket symbol etched into frosted glass
panel, subtle inner light refraction, app icon style, square format, no text, no
shadow --s 250 --style raw --ar 1:1
```

**Install as:** `user-trash.png` in `hicolor/*/places/` (theme override)

---

## 4b. Trash — Full

```
dark translucent glass trash bin icon with crumpled paper inside, minimal flat design,
soft cyan teal edge glow, dark matte background, full wastepaper basket symbol etched
into frosted glass panel, subtle inner light refraction, app icon style, square
format, no text, no shadow --s 250 --style raw --ar 1:1
```

**Install as:** `user-trash-full.png` in `hicolor/*/status/` (theme override)

---

## Post-generation checklist

1. Pick the best variant from each Midjourney grid
2. Upscale to max resolution
3. Crop/trim to exact square if needed
4. Save as PNG with transparency (remove the dark background in GIMP/Photoshop)
5. Place the 1024px source PNGs in `icons/src/` in this repo
6. Run `./icons/install-icons.sh` to resize and install
