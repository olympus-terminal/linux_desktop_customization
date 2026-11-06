"""
Voxtral transcription module.
Handles real-time speech-to-text via Mistral API.
"""
from __future__ import annotations

import asyncio
import argparse
from typing import AsyncIterator, Optional, Callable, Sequence
from dataclasses import dataclass

try:
    from mistralai import Mistral
    from mistralai.models import AudioFormat
    MISTRAL_AVAILABLE = True
except ImportError:
    MISTRAL_AVAILABLE = False

@dataclass
class TranscriptionResult:
    """Result from transcription."""
    text: str
    is_final: bool
    confidence: Optional[float] = None

class VoxtralTranscriber:
    """
    Real-time speech transcription using Voxtral via Mistral API.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "voxtral-mini-transcribe-realtime-2602",
        sample_rate: int = 16000,
        language: str = "en",
        context_bias: Optional[list[str]] = None,
    ):
        if not MISTRAL_AVAILABLE:
            raise RuntimeError("mistralai package not installed")

        if not api_key:
            raise ValueError("MISTRAL_API_KEY is required")

        self.api_key = api_key
        self.model = model
        self.sample_rate = sample_rate
        self.language = language
        self.context_bias = context_bias or []

        self._client: Optional[Mistral] = None
        self._current_text = ""
        self._text_callback: Optional[Callable[[str, bool], None]] = None

    def _get_client(self) -> Mistral:
        """Get or create Mistral client."""
        if self._client is None:
            self._client = Mistral(api_key=self.api_key)
        return self._client

    def set_text_callback(self, callback: Callable[[str, bool], None]) -> None:
        """
        Set callback for transcription updates.
        Callback receives (text, is_final).
        """
        self._text_callback = callback

    async def transcribe_stream(
        self,
        audio_stream: AsyncIterator[bytes],
    ) -> AsyncIterator[TranscriptionResult]:
        """
        Transcribe audio stream in real-time.

        Args:
            audio_stream: Async iterator yielding PCM audio chunks (16-bit, mono)

        Yields:
            TranscriptionResult objects as text becomes available
        """
        client = self._get_client()

        audio_format = AudioFormat(
            encoding="pcm_s16le",
            sample_rate=self.sample_rate,
        )

        try:
            # Import the event types
            from mistralai.models import (
                TranscriptionStreamTextDelta,
                TranscriptionStreamEnd,
            )

            async for event in client.audio.realtime.transcribe_stream(
                audio_stream=audio_stream,
                model=self.model,
                audio_format=audio_format,
            ):
                if isinstance(event, TranscriptionStreamTextDelta):
                    # Incremental text update
                    self._current_text += event.text
                    result = TranscriptionResult(
                        text=event.text,
                        is_final=False,
                    )

                    if self._text_callback:
                        self._text_callback(event.text, False)

                    yield result

                elif isinstance(event, TranscriptionStreamEnd):
                    # Final result
                    result = TranscriptionResult(
                        text=self._current_text,
                        is_final=True,
                    )

                    if self._text_callback:
                        self._text_callback(self._current_text, True)

                    yield result
                    self._current_text = ""

        except Exception as e:
            print(f"Transcription error: {e}")
            raise

    async def transcribe_audio(self, audio_data: bytes) -> str:
        """
        Transcribe a complete audio buffer (non-streaming).

        Args:
            audio_data: Complete PCM audio data (16-bit, mono)

        Returns:
            Transcribed text
        """

        async def audio_iter():
            yield audio_data

        full_text = ""
        async for result in self.transcribe_stream(audio_iter()):
            if result.is_final:
                full_text = result.text
                break

        return full_text

    def reset(self) -> None:
        """Reset transcription state."""
        self._current_text = ""

class MockTranscriber:
    """
    Explicit test-only mock transcriber for testing without API.
    Simulates transcription with placeholder text.
    """

    def __init__(self):
        self._text_callback: Optional[Callable[[str, bool], None]] = None

    def set_text_callback(self, callback: Callable[[str, bool], None]) -> None:
        self._text_callback = callback

    async def transcribe_stream(
        self,
        audio_stream: AsyncIterator[bytes],
    ) -> AsyncIterator[TranscriptionResult]:
        """Simulate transcription."""
        words = ["This", " is", " a", " test", " of", " voice", " dictation", "."]

        # Consume some audio to simulate processing
        chunk_count = 0
        async for _ in audio_stream:
            chunk_count += 1
            if chunk_count % 5 == 0 and chunk_count // 5 <= len(words):
                word = words[chunk_count // 5 - 1]
                result = TranscriptionResult(text=word, is_final=False)
                if self._text_callback:
                    self._text_callback(word, False)
                yield result

            if chunk_count > 50:
                break

        # Final result
        full_text = "".join(words)
        yield TranscriptionResult(text=full_text, is_final=True)
        if self._text_callback:
            self._text_callback(full_text, True)

    def reset(self) -> None:
        pass

def create_transcriber(
    api_key: Optional[str] = None,
    use_mock: bool = False,
    **kwargs,
):
    """
    Factory function to create appropriate transcriber.

    Args:
        api_key: Mistral API key
        use_mock: If True, explicitly use placeholder mock output for testing
        **kwargs: Additional arguments for VoxtralTranscriber

    Returns:
        Transcriber instance

    Raises:
        RuntimeError: If the Mistral client is unavailable in normal mode
        ValueError: If no API key is available in normal mode
    """
    if use_mock:
        print(
            "TEST/MOCK MODE: placeholder text only; this is not transcription "
            "and audio is not transcribed."
        )
        return MockTranscriber()

    if not MISTRAL_AVAILABLE:
        raise RuntimeError(
            "mistralai package not installed; install 'mistralai[realtime]' "
            "or pass use_mock=True only for explicit test/mock mode"
        )

    if not api_key:
        import os
        api_key = os.environ.get("MISTRAL_API_KEY", "")

    if not api_key:
        raise ValueError(
            "MISTRAL_API_KEY is required unless use_mock=True is explicitly set"
        )

    return VoxtralTranscriber(api_key=api_key, **kwargs)

async def test_transcriber(use_mock: bool = False):
    """Exercise the transcriber; mock output requires explicit opt-in."""
    import os

    print("=== Transcriber Test ===\n")

    api_key = os.environ.get("MISTRAL_API_KEY", "")
    transcriber = create_transcriber(api_key=api_key, use_mock=use_mock)

    # Simulate audio stream
    async def fake_audio():
        for _ in range(60):
            yield b"\x00" * 3200  # 100ms of silence at 16kHz
            await asyncio.sleep(0.05)

    print("Simulating transcription...")
    transcriber.set_text_callback(lambda t, f: print(f"{'[FINAL]' if f else '[...]'} {t}"))

    async for result in transcriber.transcribe_stream(fake_audio()):
        pass

    print("\nTest complete!")

def standalone_main(argv: Optional[Sequence[str]] = None) -> None:
    """Run the standalone transcriber check with explicit mock selection."""
    parser = argparse.ArgumentParser(
        description="Exercise the Voxtral transcriber with a simulated audio stream."
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="TEST ONLY: emit placeholder mock text; no transcription is performed",
    )
    args = parser.parse_args(argv)
    asyncio.run(test_transcriber(use_mock=args.mock))


if __name__ == "__main__":
    standalone_main()
