#!/usr/bin/env bash
# install_coding_fonts_linux.sh — Install a curated set of coding fonts on Ubuntu/Debian.
#
# Usage:
#   sudo bash install_coding_fonts_linux.sh          # install all tiers
#   sudo bash install_coding_fonts_linux.sh --tier1   # essentials only (8 fonts)
#   sudo bash install_coding_fonts_linux.sh --list    # show what would be installed

set -euo pipefail

# ── Configuration ────────────────────────────────────────────────────────

TIER1_APT=(
    fonts-jetbrains-mono      # JetBrains Mono — clean, modern, great ligatures
    fonts-firacode            # Fira Code — the original ligature font
    fonts-cascadia-code       # Cascadia Code — Microsoft/Windows Terminal default
    fonts-hack                # Hack — sharp, excellent readability
    fonts-ibm-plex            # IBM Plex Mono — elegant, corporate feel
    fonts-inconsolata         # Inconsolata — classic lightweight mono
    fonts-anonymous-pro       # Anonymous Pro — comfortable for long sessions
    fonts-mononoki            # Mononoki — soft, easy on the eyes
)

TIER2_APT=(
    fonts-fantasque-sans      # Fantasque Sans Mono — quirky, handwritten feel
    fonts-hermit              # Hermit — minimalist bitmap-inspired
    fonts-monoid              # Monoid — bitmap-like sharpness, compact
    fonts-agave               # Agave — rounded, friendly
    fonts-dm-mono             # DM Mono — Google's clean mono
    fonts-league-mono         # League Mono — variable-width mono
    fonts-monofur             # Monofur — rounded, playful
    fonts-kode-mono           # Kode Mono — modern developer font
    fonts-spleen              # Spleen — crisp bitmap-style
    fonts-terminus            # Terminus — classic bitmap terminal font
    fonts-proggy              # Proggy — tiny bitmap, great for dense views
    fonts-3270                # IBM 3270 — retro mainframe aesthetic
)

GITHUB_FONTS=(
    "SourceCodePro|https://github.com/adobe-fonts/source-code-pro/releases/latest/download/OTF-source-code-pro.tar.gz|tar.gz"
    "VictorMono|https://rubjo.github.io/victor-mono/VictorMonoAll.zip|zip"
    "CommitMono|https://github.com/eigilnikolajsen/commit-mono/releases/latest/download/CommitMono.zip|zip"
    "MapleMono|https://github.com/subframe7536/maple-font/releases/latest/download/MapleMono.zip|zip"
    "Monaspace|https://github.com/githubnext/monaspace/releases/latest/download/monaspace-v1.101-linux.zip|zip"
    "GeistMono|https://github.com/vercel/geist-font/releases/latest/download/geist-mono.zip|zip"
)

# ── Helpers ──────────────────────────────────────────────────────────────

list_fonts() {
    echo "=== Tier 1: Essentials (apt) ==="
    printf '  %s\n' "${TIER1_APT[@]}"
    echo ""
    echo "=== Tier 2: Alternatives (apt) ==="
    printf '  %s\n' "${TIER2_APT[@]}"
    echo ""
    echo "=== Tier 3: GitHub releases ==="
    for entry in "${GITHUB_FONTS[@]}"; do
        IFS='|' read -r name url _ <<< "$entry"
        echo "  $name ($url)"
    done
}

install_github_font() {
    local name="$1" url="$2" format="$3" dest="$4"
    local temp_dir
    temp_dir=$(mktemp -d)

    echo "  Downloading $name..."
    if curl -fsSL -o "$temp_dir/$name.$format" "$url"; then
        case "$format" in
            zip)
                unzip -qo "$temp_dir/$name.$format" -d "$temp_dir/$name" 2>/dev/null
                ;;
            tar.gz)
                mkdir -p "$temp_dir/$name"
                tar xzf "$temp_dir/$name.$format" -C "$temp_dir/$name"
                ;;
        esac
        find "$temp_dir/$name" \( -name '*.ttf' -o -name '*.otf' \) \
            -exec cp {} "$dest/" \;
        echo "  ✓ $name installed"
    else
        echo "  ✗ $name failed (URL may have changed)"
    fi
    rm -rf "$temp_dir"
}

# ── Main ─────────────────────────────────────────────────────────────────

case "${1:-all}" in
    --list)
        list_fonts
        exit 0
        ;;
    --tier1)
        INSTALL_TIERS="1"
        ;;
    --help|-h)
        echo "Usage: sudo bash $0 [--tier1|--list|--help]"
        echo "  (no args)  Install all tiers (apt + GitHub)"
        echo "  --tier1    Install only the 8 essential fonts from apt"
        echo "  --list     Show what would be installed"
        exit 0
        ;;
    *)
        INSTALL_TIERS="all"
        ;;
esac

if [[ $EUID -ne 0 ]]; then
    echo "Please run with sudo:  sudo bash $0"
    exit 1
fi

echo "=== Installing coding fonts ==="

# Tier 1: essentials
echo ""
echo "Installing ${#TIER1_APT[@]} essential font packages..."
apt-get update -qq
apt-get install -y "${TIER1_APT[@]}"

if [[ "$INSTALL_TIERS" == "all" ]]; then
    # Tier 2: alternatives from apt
    echo ""
    echo "Installing ${#TIER2_APT[@]} alternative font packages..."
    apt-get install -y "${TIER2_APT[@]}"

    # Tier 3: GitHub releases
    FONT_DIR="/usr/local/share/fonts/dev-typography"
    mkdir -p "$FONT_DIR"
    echo ""
    echo "Installing ${#GITHUB_FONTS[@]} fonts from GitHub..."
    for entry in "${GITHUB_FONTS[@]}"; do
        IFS='|' read -r name url format <<< "$entry"
        install_github_font "$name" "$url" "$format" "$FONT_DIR"
    done
fi

# Refresh font cache
echo ""
echo "Refreshing font cache..."
fc-cache -f

# Summary
TOTAL=$(fc-list :spacing=mono family | sort -u | wc -l)
echo ""
echo "=== Done! $TOTAL monospace font families now available ==="
echo ""
echo "Top picks for your editor:"
echo "  'JetBrains Mono'       — clean, modern, great ligatures"
echo "  'Fira Code'            — the OG ligature font"
echo "  'Cascadia Code'        — Microsoft's terminal font"
echo "  'Source Code Pro'      — Adobe classic"
echo "  'Victor Mono'          — cursive italics for comments"
echo "  'Monaspace Neon'       — GitHub's new variable font"
echo "  'Commit Mono'          — neutral, no-nonsense"
echo ""
echo "Restart your editor to see the new fonts."
