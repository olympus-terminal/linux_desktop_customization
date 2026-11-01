<p align="center">
  <img src="assets/banner.png" alt="voice-dictation banner" width="100%">
</p>

# Voice-to-Text GPU

GPU-accelerated real-time voice dictation using [faster-whisper](https://github.com/SYSTRAN/faster-whisper) and [Silero VAD](https://github.com/snakers4/silero-vad).

## Features

- **faster-whisper** (CTranslate2 backend) -- ~4x faster than openai-whisper, lower VRAM
- **Silero VAD** -- neural voice activity detection eliminates hallucinations on silence
- **Threaded pipeline** -- records audio while previous utterance is being transcribed
- **Push-to-talk** -- optional hold-to-record mode (Right Ctrl)
- **Window typing** -- types directly into any focused window via xdotool
- **Voice commands** -- punctuation and actions via spoken phrases
- **Microphone selection** -- choose input device from the command line
- Hallucination filtering and repetition loop detection

## Requirements

- NVIDIA GPU with CUDA support
- Python 3.8+
- ffmpeg
- xdotool (for window typing mode)
- PulseAudio or PipeWire

## Installation

```bash
# Create conda environment
conda create -n dictation python=3.11
conda activate dictation

# Install PyTorch with CUDA
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install dependencies
pip install faster-whisper silero-vad pyaudio numpy pynput

# System dependencies (Ubuntu/Debian)
sudo apt install ffmpeg xdotool portaudio19-dev
```

## Usage

### Voxtral API and Explicit Mock Mode

`run.sh` uses the Voxtral API by default. Install the optional
`mistralai[realtime]` client and set `MISTRAL_API_KEY` before starting it:

```bash
./run.sh
```

API mode fails closed: a missing client raises an error, and a missing API key
is rejected. It never substitutes placeholder output. The mock must be selected
explicitly and is only for testing application flow:

```bash
./run.sh --mock  # TEST/MOCK MODE: placeholder text; audio is not transcribed
```

Launchers do not force a machine-specific `LD_PRELOAD` path. If the hands-free
launcher should select a device by default, set `SOTTO_AUDIO_DEVICE`; otherwise
use its `--device` option.

### Terminal Mode

Prints transcribed text to the terminal (no xdotool needed):

```bash
python dictate_terminal.py
python dictate_terminal.py --model small         # faster, less accurate
python dictate_terminal.py --list-devices        # show microphones
python dictate_terminal.py --device 1            # pick a mic
```

### Window Typing Mode

Types directly into the focused window:

```bash
python dictate_to_window.py
python dictate_to_window.py --push-to-talk       # hold Right Ctrl to record
python dictate_to_window.py --model large-v3     # most accurate (default)
python dictate_to_window.py --no-type            # print only, don't type
python dictate_to_window.py --list-devices
python dictate_to_window.py --device 1
```

1. Run the script in a terminal
2. Click on the window you want to type into
3. Speak naturally -- pauses end an utterance
4. Text appears in the focused window

### Push-to-Talk

```bash
python dictate_to_window.py --push-to-talk
```

Hold **Right Ctrl** to record. Release to stop. Only speech recorded while the key is held will be transcribed.

## Voice Commands

Punctuation requires the `insert` prefix so normal speech isn't mangled:

| Command | Action |
|---------|--------|
| `send message` / `send it` / `press enter` | Press Enter |
| `new line` | Insert newline |
| `insert period` | `.` |
| `insert comma` | `,` |
| `insert question mark` | `?` |
| `insert exclamation` | `!` |
| `insert colon` | `:` |
| `insert semicolon` | `;` |
| `delete that` / `delete word` | Delete previous word |

## Models

faster-whisper uses CTranslate2-converted models. Available sizes:

| Model | VRAM | Speed | Accuracy | Notes |
|-------|------|-------|----------|-------|
| `tiny` | ~1 GB | Fastest | Basic | Good for testing |
| `base` | ~1 GB | Very fast | Fair | |
| `small` | ~2 GB | Fast | Good | Decent for most uses |
| `medium` | ~4 GB | Medium | Very good | |
| `large-v2` | ~5 GB | Slower | Excellent | |
| `large-v3` | ~5 GB | Slower | Best | Default, recommended |

All models are downloaded automatically on first use from Hugging Face.

## Architecture

```
Microphone
    |
    v
[Silero VAD] -- detects speech start/end
    |
    v
[Audio Buffer] -- accumulates frames until pause detected
    |
    v
[Queue] -------> [Transcription Thread]
                       |
                       v
                  [faster-whisper GPU]
                       |
                       v
                  [Hallucination Filter]
                       |
                       v
                  [Voice Commands]
                       |
                       v
                  [xdotool] --> Focused Window
```

The threaded pipeline means recording continues while the previous utterance is being transcribed, so you never miss speech.

## Troubleshooting

### Stopping dictation / it keeps listening

Any of these stops it and ends the process: Ctrl-C, closing the terminal window it runs in, clicking the tray icon (on GNOME there is no tray menu: a click quits), or `pkill -f hands_free.py`. If shutdown has not finished 5 seconds after the request (or you quit a second time), the process is force-ended. A copy started in the background without a terminal (for example by a script with `setsid`/`nohup`) has no window to close: click the tray icon or use `pkill -f hands_free.py`.

### Hallucinations ("Thanks for watching", etc.)

With Silero VAD this should be rare. If it still happens:
- Use a better microphone (wired > Bluetooth)
- Bluetooth mics use lossy compression that confuses Whisper
- The hallucination filter catches common phrases automatically

### Repetition loops

Set automatically by `condition_on_previous_text=False` in faster-whisper. The post-processing filter also catches remaining loops.

### X server crash / display manager restart

If `dictate_to_window.py` causes X issues:
- The script uses `--clearmodifiers` and a 12ms delay to be safer
- Consider using `--push-to-talk` mode to control when typing happens
- On Wayland, xdotool won't work; use ydotool instead

### JACK warnings

```
Cannot connect to server socket err = No such file or directory
jack server is not running or cannot be started
```

Harmless -- PyAudio prints these when JACK isn't installed. They can be safely ignored.

### Choosing a microphone

```bash
python dictate_to_window.py --list-devices
```

Then pass the device number:

```bash
python dictate_to_window.py --device 3
```

## License

MIT
