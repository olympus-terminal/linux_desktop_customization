#!/usr/bin/env python3
"""
Hands-free continuous dictation mode.
Automatically detects speech and transcribes without any keyboard input.

Usage:
    ./run.sh --hands-free           # Continuous dictation with local whisper
    ./run.sh --hands-free -m small  # Use small model for better accuracy
    ./run.sh --hands-free -c        # Output to clipboard instead of typing
"""
import asyncio
import os
import signal
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
from collections import deque

from config import get_config
from audio_capture import AudioCapture
from transcriber_local import create_local_transcriber, LocalTranscriber
from text_output import TextOutput, TextProcessor, OutputMode
from tray_icon import create_indicator, TrayStatus
from vad import VoiceActivityDetector, SileroVAD, VADState
from voice_commands import VoiceCommandProcessor, CommandExecutor, CommandAction
from homonym_fixer import HomonymFixer, RuleBasedFixer, create_fixer


# After a quit request, force the process to end if shutdown has not finished by then
SHUTDOWN_TIMEOUT_S = 5.0


class HandsFreeDictation:
    """
    Hands-free dictation that automatically detects speech.

    Flow:
    1. Continuously monitor audio with VAD
    2. When speech detected, start buffering audio
    3. When speech ends, transcribe the buffered audio
    4. Type the result into the focused window
    """

    def __init__(
        self,
        output_mode: OutputMode = OutputMode.TYPE,
        model_size: str = "large-v3-turbo",
        language: str = "en",
        use_tray: bool = True,
        enable_commands: bool = True,
        fix_homonyms: bool = False,
        homonym_llm: bool = True,
        device_name: Optional[str] = None,
        energy_vad: bool = False,
    ):
        self.config = get_config()

        # Audio capture (CLI --device overrides config)
        mic_device = device_name or self.config.audio.device_name
        self.audio = AudioCapture(
            sample_rate=self.config.audio.sample_rate,
            channels=self.config.audio.channels,
            chunk_duration_ms=self.config.audio.chunk_duration_ms,
            device_name=mic_device,
        )

        # Voice activity detection: Silero (voice, not loudness) by default since
        # 2026-11-01; the old energy VAD stays available with --energy-vad.
        if energy_vad:
            self.vad = VoiceActivityDetector(
                sample_rate=self.config.audio.sample_rate,
                min_speech_ms=200,
                min_silence_ms=600,
                trailing_silence_ms=1200,
            )
        else:
            self.vad = SileroVAD(sample_rate=self.config.audio.sample_rate)

        # Transcribe on a worker thread so the microphone keeps being read
        # (transcribing inside the read loop caused "input overflow" = lost audio).
        # One worker keeps the text in spoken order.
        self._worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix="transcribe")

        # Local transcriber (load model eagerly so first utterance isn't slow)
        print(f"Loading faster-whisper {model_size}...")
        self.transcriber = create_local_transcriber(
            model_size=model_size,
            language=language,
            sample_rate=self.config.audio.sample_rate,
        )
        self.transcriber._load_model()

        # Text output
        self.output = TextOutput(
            mode=output_mode,
            typing_delay_ms=0,
        )

        self.processor = TextProcessor(
            auto_capitalize=True,
            auto_punctuation=True,
        )

        # Status indicator
        self.indicator = create_indicator(use_tray=use_tray, on_quit=self.request_stop)

        # Voice commands (optional)
        self.enable_commands = enable_commands
        if enable_commands:
            self.command_processor = VoiceCommandProcessor()
            self.command_executor = CommandExecutor(self.output)
        else:
            self.command_processor = None
            self.command_executor = None

        # Homonym fixer (optional)
        self.fix_homonyms = fix_homonyms
        if fix_homonyms:
            self.homonym_fixer = create_fixer(use_llm=homonym_llm)
            fixer_type = "LLM" if homonym_llm else "rule-based"
            print(f"Homonym correction: {fixer_type}")
        else:
            self.homonym_fixer = None

        # State
        self._is_running = False
        self._stop_requested = False
        self._audio_buffer = bytearray()
        self._is_transcribing = False
        self._utterance_count = 0
        self._paused = False

        # Set up VAD callbacks
        self.vad.set_callbacks(
            on_speech_start=self._on_speech_start,
            on_speech_end=self._on_speech_end,
            on_level=self._on_level,
        )

    def request_stop(self, reason: str = "tray Quit"):
        """Ask the main loop to stop (safe from signal handlers and the tray thread).

        A second request, or a shutdown that takes longer than
        SHUTDOWN_TIMEOUT_S, ends the process immediately so dictation can never
        keep listening after it was told to quit.
        """
        if self._stop_requested:
            print(f"\n{reason} again: forcing exit", flush=True)
            os._exit(1)
        self._stop_requested = True
        self._is_running = False
        print(f"\n\nShutting down ({reason})...", flush=True)

        def _force_exit():
            print(f"\nShutdown took over {SHUTDOWN_TIMEOUT_S:.0f}s: forcing exit", flush=True)
            os._exit(1)

        timer = threading.Timer(SHUTDOWN_TIMEOUT_S, _force_exit)
        timer.daemon = True
        timer.start()

    def _on_speech_start(self):
        """Called when VAD detects speech start."""
        self._audio_buffer.clear()
        if hasattr(self.vad, "preroll"):
            self._audio_buffer.extend(self.vad.preroll())
        self.indicator.set_status(TrayStatus.RECORDING)
        print("\n🎤 Listening...", end="", flush=True)

    def _on_speech_end(self):
        """Called when VAD detects speech end."""
        audio_bytes = len(self._audio_buffer)
        audio_seconds = audio_bytes / 2 / 16000  # 16-bit mono at 16kHz

        if audio_bytes < 8000:  # Less than 250ms at 16kHz
            print(f" (too short: {audio_seconds:.1f}s)", flush=True)
            self.indicator.set_status(TrayStatus.IDLE)
            return

        self._utterance_count += 1
        audio_data = bytes(self._audio_buffer)
        self._audio_buffer.clear()

        # Transcribe
        self.indicator.set_status(TrayStatus.PROCESSING)
        print(f" ({audio_seconds:.1f}s) transcribing...", end="", flush=True)

        # Run transcription off the audio loop
        self._worker.submit(self._transcribe_and_output, audio_data)

    def _on_level(self, level: float, is_speech: bool):
        """Called with audio level updates."""
        self.indicator.set_audio_level(level)

    def _transcribe_and_output(self, audio_data: bytes):
        """Transcribe audio and output the text."""
        try:
            text = self.transcriber.transcribe_audio(audio_data)

            if text and text.strip():
                text = text.strip()

                # Apply homonym correction (if enabled)
                if self.fix_homonyms and self.homonym_fixer:
                    result = self.homonym_fixer.fix(text)
                    if result.changed:
                        print(f" [homonyms: {result.corrections}]", end="")
                        text = result.corrected

                # Check for voice commands (if enabled)
                if self.enable_commands and self.command_processor:
                    command, remaining_text = self.command_processor.process(text)

                    if command:
                        # Handle special mode commands
                        if command.action == CommandAction.STOP_LISTENING:
                            print(f" \"{text}\" -> [STOP LISTENING]")
                            self._is_running = False
                            return

                        if command.action == CommandAction.PAUSE:
                            print(f" \"{text}\" -> [PAUSED]")
                            self._paused = True
                            return

                        if command.action == CommandAction.CAPS_ON:
                            self.command_processor.set_caps_mode(True)
                            print(f" \"{text}\" -> [CAPS ON]")
                        elif command.action == CommandAction.CAPS_OFF:
                            self.command_processor.set_caps_mode(False)
                            print(f" \"{text}\" -> [CAPS OFF]")
                        else:
                            # Execute the command
                            print(f" \"{text}\"", end="")
                            self.command_executor.execute(command)

                        # Type any remaining text after the command
                        if remaining_text:
                            processed = self.processor.process(remaining_text)
                            processed = self.command_processor.apply_formatting(processed)
                            self.output.output(processed + " " if processed else processed)
                            print(f" + \"{processed}\"")

                        self.indicator.set_status(TrayStatus.IDLE)
                        return

                # No command (or commands disabled) - just type the text
                processed = self.processor.process(text)

                print(f" \"{processed}\"")
                # Space after, not before: utterances stay apart ("stuff. I thought", never
                # "stuff.I thought") and a fresh prompt does not start with a space.
                self.output.output(processed + " " if processed else processed)
            else:
                print(" (no speech detected)")

        except Exception as e:
            print(f" error: {e}")

        self.indicator.set_status(TrayStatus.IDLE)

    async def run(self):
        """Main loop - continuously listen and transcribe."""
        self._is_running = True

        # Start components
        self.indicator.start()
        self.indicator.set_status(TrayStatus.IDLE)
        self.audio.start()

        print("=" * 50)
        print("  Hands-Free Dictation")
        print("  Speak naturally - text appears where you type")
        if self.enable_commands:
            print("  Voice commands: ON (say 'kimmy <command>')")
        else:
            print("  Voice commands: OFF (pure dictation)")
        if self.fix_homonyms:
            fixer_type = "LLM" if isinstance(self.homonym_fixer, HomonymFixer) else "rules"
            print(f"  Homonym correction: ON ({fixer_type})")
        print("=" * 50)
        print()
        print("Calibrating ambient noise (1 second, stay quiet)...")
        print()

        # Stop on Ctrl-C, kill/pkill, and terminal window closed (SIGHUP)
        def signal_handler(sig, frame):
            self.request_stop(signal.Signals(sig).name)

        for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
            signal.signal(sig, signal_handler)

        try:
            while self._is_running:
                chunk = self.audio.read_chunk()
                if chunk:
                    # Process through VAD
                    is_speaking = self.vad.process_chunk(chunk)

                    # Buffer audio while speaking
                    if is_speaking:
                        self._audio_buffer.extend(chunk)

                await asyncio.sleep(0.001)

        finally:
            self.cleanup()

    def cleanup(self):
        """Clean up resources."""
        self._worker.shutdown(wait=False, cancel_futures=True)
        for step in (self.audio.close, self.indicator.stop):
            try:
                step()
            except Exception as e:
                print(f"Cleanup error in {step.__qualname__}: {e}")
        print(f"\nTotal utterances: {self._utterance_count}", flush=True)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Hands-free voice dictation"
    )
    parser.add_argument(
        "--model", "-m",
        default="large-v3-turbo",
        choices=["tiny", "base", "small", "medium", "large-v3", "large-v3-turbo"],
        help="Whisper model (default: large-v3-turbo; ~0.2 s per 8 s of speech on the RTX 4080 laptop GPU)"
    )
    parser.add_argument(
        "--clipboard", "-c",
        action="store_true",
        help="Output to clipboard instead of typing"
    )
    parser.add_argument(
        "--both", "-b",
        action="store_true",
        help="Output to both typing and clipboard"
    )
    parser.add_argument(
        "--no-tray",
        action="store_true",
        help="Disable system tray icon"
    )
    parser.add_argument(
        "--commands",
        action="store_true",
        help="Enable voice commands (experimental, say 'kimmy <command>')"
    )
    parser.add_argument(
        "--test-vad",
        action="store_true",
        help="Test VAD without transcription"
    )
    parser.add_argument(
        "--fix-homonyms",
        action="store_true",
        help="Enable context-aware homonym correction (their/there/they're, etc.)"
    )
    parser.add_argument(
        "--homonym-rules",
        action="store_true",
        help="Use rule-based homonym fixer instead of LLM (faster but less accurate)"
    )
    parser.add_argument(
        "--device", "-d",
        default=None,
        help="Microphone device name pattern (e.g. 'RØDE NT-USB+', 'Blue Yeti')"
    )
    parser.add_argument(
        "--energy-vad",
        action="store_true",
        help="Use the old loudness-based speech detector instead of Silero",
    )
    parser.add_argument(
        "--list-devices",
        action="store_true",
        help="List available audio input devices and exit"
    )

    args = parser.parse_args()

    if args.list_devices:
        from audio_capture import AudioCapture
        ac = AudioCapture()
        print("Available input devices:")
        for dev in ac.list_devices():
            print(f"  [{dev['index']}] {dev['name']} ({dev['sample_rate']}Hz, {dev['channels']}ch)")
        return

    if args.test_vad:
        from vad import test_vad
        test_vad()
        return

    # Determine output mode
    if args.both:
        output_mode = OutputMode.BOTH
    elif args.clipboard:
        output_mode = OutputMode.CLIPBOARD
    else:
        output_mode = OutputMode.TYPE

    app = HandsFreeDictation(
        output_mode=output_mode,
        model_size=args.model,
        use_tray=not args.no_tray,
        enable_commands=args.commands,
        fix_homonyms=args.fix_homonyms,
        homonym_llm=not args.homonym_rules,
        device_name=args.device,
        energy_vad=args.energy_vad,
    )

    asyncio.run(app.run())

    # Leave without interpreter teardown: the tray (X11), PortAudio and CUDA
    # threads can hang it, which kept the process alive after "Shutting down".
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0)


if __name__ == "__main__":
    main()
