"""
Text output module for Voxtral dictation.
Handles typing text into active window (xdotool) and clipboard operations.
"""
import os
import subprocess
import shutil
from typing import Optional
from enum import Enum

# Never send keystrokes to these windows (X11 WM_CLASS, lowercase): in a media
# player every letter is a shortcut (space/p/. pause, s screenshot, m mute,
# f fullscreen), so dictation typed into a focused mpv "froze" the video
# (2026-10-31). Text meant for them goes to the clipboard instead.
# Override with DICTATION_NO_TYPE_CLASSES="mpv,vlc,..." ("" disables).
NO_TYPE_CLASSES = {
    c.strip().lower()
    for c in os.environ.get(
        "DICTATION_NO_TYPE_CLASSES", "mpv,vlc,celluloid,io.github.celluloid_player.celluloid,smplayer,totem"
    ).split(",")
    if c.strip()
}

# Type ONLY into terminal windows (user, 2026-11-01: "we only want to dictate into the
# terminal", Claude Code / agent TUIs included). Anything typed elsewhere is dropped
# (printed in the dictation console only), so noise hallucinations like "Thank you."
# cannot land in a browser or editor. Override with DICTATION_TYPE_ONLY_CLASSES="a,b"
# ("" types into every window except NO_TYPE_CLASSES, the old behaviour).
TYPE_ONLY_CLASSES = {
    c.strip().lower()
    for c in os.environ.get(
        "DICTATION_TYPE_ONLY_CLASSES",
        "gnome-terminal-server,gnome-terminal,org.gnome.ptyxis,ptyxis,org.gnome.console,kgx,"
        "xterm,uxterm,kitty,alacritty,konsole,terminator,tilix,wezterm,org.wezfurlong.wezterm,"
        "foot,xfce4-terminal,mate-terminal,lxterminal,urxvt,st-256color,ghostty,com.mitchellh.ghostty",
    ).split(",")
    if c.strip()
}


# Plain-text filter (user, 2026-11-01: "it should not make special characters ... like curly
# brackets or quotation marks"; "maybe m-dashes are okay"). Typed text keeps only letters,
# digits, spaces and . , ? plus dashes, typed as plain " - ".
# Apostrophes survive only inside words (don't, user's), hyphens only between letters/digits
# (re-run, large-v3). Non-ASCII is never typed: xdotool types such characters by remapping a
# spare key on the fly, and terminals sometimes read the wrong key (stray "}" after words).
_CHAR_MAP = {
    "\u2018": "'", "\u2019": "'", "\u02bc": "'", "`": "'",
    "\u2026": "...", "\u2014": " \x03 ", "\u2013": " \x03 ",
    "!": ".", ";": ",", "%": " percent ", "&": " and ",
    "\u00d7": " times ", "\u00b0": " degrees ", "\u2044": "/",
    "\u00df": "ss", "\u00e6": "ae", "\u00c6": "AE", "\u0153": "oe", "\u0152": "OE",
    "\u00f8": "o", "\u00d8": "O", "\u0142": "l", "\u0141": "L", "\u00f0": "d", "\u00fe": "th",
}


def _to_ascii(c: str) -> str:
    """ASCII for one character: its accent-free form (e -> e), else a space, so nothing
    is silently glued together (5x3 must not become 53)."""
    import unicodedata
    if c.isascii():
        return c
    out = "".join(_CHAR_MAP.get(d, d) for d in unicodedata.normalize("NFKD", c))
    out = "".join(d for d in out if d.isascii())
    return out if out.strip() else " "


def plain_text(text: str) -> str:
    """Reduce dictated text to letters, digits, spaces, . , ? and " - " dashes (plus in-word ' and -)."""
    import re
    if not text:
        return text
    lead = " " if text[:1].isspace() else ""
    t = text.replace("--", "\u2014")
    t = "".join(_CHAR_MAP.get(c, c) for c in t)
    t = "".join(_to_ascii(c) for c in t)                  # cafe for café, space for unknown symbols
    t = re.sub(r"(?<=\d):(?=\d)", "\x00", t)                # keep 10:30
    t = re.sub(r"(?<=\d)/(?=\d)", "\x04", t)                # keep 1/2, 24/7 (never a leading /command)
    t = re.sub(r"(?<=[A-Za-z0-9])'(?=[A-Za-z])", "\x01", t)   # don't, user's
    t = re.sub(r"(?<=[A-Za-z0-9])-(?=[A-Za-z0-9])", "\x02", t)  # re-run, large-v3
    t = re.sub(r"(?<=\s)-(?=\s)", "\x03", t)                 # spaced " - " is a dash
    t = t.replace(":", ",")
    t = re.sub(r"[^A-Za-z0-9 .,?\x00\x01\x02\x03\x04]", " ", t)
    t = t.replace("\x00", ":").replace("\x01", "'").replace("\x02", "-").replace("\x04", "/")
    t = re.sub(r"\s+([.,?])", r"\1", t)              # no space before punctuation
    t = re.sub(r",(\s*,)+", ",", t)                   # ", ," -> ","
    t = re.sub(r",\s*([.?])", r"\1", t)              # ", ." -> "."
    t = re.sub(r"^[\s.,?]*,", "", t)                  # no leading comma
    t = re.sub(r"(\s*\x03\s*)+", " \x03 ", t)            # one dash, spaced
    t = re.sub(r"^[\s\x03.,?]+|[\s\x03]+$", "", t)       # no leading dash/punct, no trailing dash
    t = re.sub(r",?\s*\x03\s*,?", " \x03 ", t)
    t = re.sub(r"\s+", " ", t).strip().replace("\x03", "-")
    return lead + t if t else ""


class OutputMode(Enum):
    TYPE = "type"           # Type directly into active window
    CLIPBOARD = "clipboard" # Copy to clipboard only
    BOTH = "both"           # Type and copy to clipboard


class TextOutput:
    """
    Outputs transcribed text to the system.
    Supports typing via xdotool and clipboard via xclip.
    """

    def __init__(
        self,
        mode: OutputMode = OutputMode.TYPE,
        typing_delay_ms: int = 0,
    ):
        self.mode = mode
        self.typing_delay_ms = typing_delay_ms

        # Check for required tools
        self._xdotool = shutil.which("xdotool")
        self._xclip = shutil.which("xclip")

        if mode in (OutputMode.TYPE, OutputMode.BOTH) and not self._xdotool:
            print("Warning: xdotool not found. Install with: sudo apt install xdotool")

        if mode in (OutputMode.CLIPBOARD, OutputMode.BOTH) and not self._xclip:
            print("Warning: xclip not found. Install with: sudo apt install xclip")

    def _focused_class(self) -> str:
        """WM_CLASS of the focused window as "instance,class", lowercase ('' if unknown)."""
        # This xdotool has no getwindowclassname; read WM_CLASS with xprop:
        #   WM_CLASS(STRING) = "instance", "Class"   (mpv: "gl", "mpv")
        try:
            wid = subprocess.run(
                ["xdotool", "getactivewindow"], capture_output=True, text=True, timeout=2,
            ).stdout.strip()
            if not wid:
                return ""
            out = subprocess.run(
                ["xprop", "-id", wid, "WM_CLASS"], capture_output=True, text=True, timeout=2,
            ).stdout
            names = out.split("=", 1)[1].replace('"', "").split(",") if "=" in out else []
            return ",".join(n.strip().lower() for n in names)
        except Exception:
            return ""

    def _blocked_window(self) -> str:
        """Return the focused window's class if keystrokes must not go there."""
        if not (self._xdotool and (NO_TYPE_CLASSES or TYPE_ONLY_CLASSES)):
            return ""
        cls = self._focused_class()
        names = set(cls.split(","))
        if NO_TYPE_CLASSES.intersection(names):
            return cls or "unknown window"
        if TYPE_ONLY_CLASSES and not TYPE_ONLY_CLASSES.intersection(names):
            return cls or "unknown window"
        return ""

    def type_text(self, text: str) -> bool:
        """
        Type text into the currently focused window using xdotool.
        Returns True on success.
        """
        if not self._xdotool:
            print("xdotool not available")
            return False

        if not text:
            return True

        blocked = self._blocked_window()
        if blocked:
            print(f" [focused window is {blocked}, not a terminal: not typed]", end="")
            return True

        try:
            cmd = ["xdotool", "type", "--clearmodifiers"]

            if self.typing_delay_ms > 0:
                cmd.extend(["--delay", str(self.typing_delay_ms)])

            cmd.append(text)

            subprocess.run(cmd, check=True, timeout=10)
            return True
        except subprocess.TimeoutExpired:
            print("xdotool timed out")
            return False
        except subprocess.CalledProcessError as e:
            print(f"xdotool error: {e}")
            return False

    def copy_to_clipboard(self, text: str) -> bool:
        """
        Copy text to system clipboard using xclip.
        Returns True on success.
        """
        if not self._xclip:
            print("xclip not available")
            return False

        if not text:
            return True

        try:
            subprocess.run(
                ["xclip", "-selection", "clipboard"],
                input=text.encode("utf-8"),
                check=True,
                timeout=5,
            )
            return True
        except subprocess.TimeoutExpired:
            print("xclip timed out")
            return False
        except subprocess.CalledProcessError as e:
            print(f"xclip error: {e}")
            return False

    def output(self, text: str) -> bool:
        """
        Output text according to configured mode.
        Returns True if all operations succeeded.
        """
        success = True
        text = plain_text(text)
        if not text.strip():
            return True

        if self.mode in (OutputMode.TYPE, OutputMode.BOTH):
            success = self.type_text(text) and success

        if self.mode in (OutputMode.CLIPBOARD, OutputMode.BOTH):
            success = self.copy_to_clipboard(text) and success

        return success

    def output_incremental(self, text: str, previous_text: str = "") -> bool:
        """
        Output only the new portion of text (for streaming transcription).
        Useful when Voxtral sends updated transcription as it processes.
        """
        if text.startswith(previous_text):
            new_text = text[len(previous_text):]
            if new_text:
                return self.output(new_text)
            return True
        else:
            # Text was revised, need to handle differently
            # For now, just output the full new text
            # A more sophisticated approach would backspace and retype
            return self.output(text)

    def backspace(self, count: int = 1) -> bool:
        """Send backspace keys to delete characters."""
        if not self._xdotool:
            return False
        if self._blocked_window():
            return True

        try:
            subprocess.run(
                ["xdotool", "key", "--clearmodifiers"] + ["BackSpace"] * count,
                check=True,
                timeout=5,
            )
            return True
        except Exception as e:
            print(f"Backspace error: {e}")
            return False

    def press_key(self, key: str) -> bool:
        """Press a specific key (e.g., 'Return', 'Tab')."""
        if not self._xdotool:
            return False
        if self._blocked_window():
            return True

        try:
            subprocess.run(
                ["xdotool", "key", "--clearmodifiers", key],
                check=True,
                timeout=5,
            )
            return True
        except Exception as e:
            print(f"Key press error: {e}")
            return False


class TextProcessor:
    """
    Processes transcribed text before output.
    Handles capitalization, punctuation, and formatting.
    """

    def __init__(
        self,
        auto_capitalize: bool = True,
        auto_punctuation: bool = True,
    ):
        self.auto_capitalize = auto_capitalize
        self.auto_punctuation = auto_punctuation
        self._sentence_start = True

    def process(self, text: str) -> str:
        """Process text with configured transformations."""
        if not text:
            return text

        result = plain_text(text)
        if not result:
            return result

        # Capitalize first letter of sentences
        if self.auto_capitalize and self._sentence_start:
            result = result[0].upper() + result[1:] if len(result) > 0 else result

        # Update sentence tracking
        if result:
            # Check if we end with sentence-ending punctuation
            self._sentence_start = result.rstrip().endswith(('.', '!', '?'))

        return result

    def reset(self) -> None:
        """Reset processor state (e.g., for new dictation session)."""
        self._sentence_start = True


def test_output():
    """Test text output functionality."""
    print("=== Text Output Test ===\n")

    output = TextOutput(mode=OutputMode.CLIPBOARD)

    print("Testing clipboard...")
    if output.copy_to_clipboard("Hello from Voxtral dictation!"):
        print("✓ Text copied to clipboard")
    else:
        print("✗ Clipboard copy failed")

    print("\nTo test typing, focus a text field and run:")
    print("  python -c \"from text_output import TextOutput, OutputMode; TextOutput(OutputMode.TYPE).type_text('Test typing')\"")


if __name__ == "__main__":
    test_output()
