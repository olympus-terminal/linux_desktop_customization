"""Offline tests for explicit mock selection and fail-closed API startup.

These tests use only monkeypatched availability flags and stand-in application
objects. They do not provide an API key, capture audio, contact a service, or
produce transcription data.
"""

from __future__ import annotations

import importlib.util
import io
import os
import sys
import types
import unittest
from contextlib import redirect_stdout
from enum import Enum
from pathlib import Path
from unittest.mock import patch


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

import transcriber  # noqa: E402  (repository path is inserted above)


class FailClosedFactoryTests(unittest.TestCase):
    def test_mock_requires_explicit_opt_in_and_is_clearly_labeled(self) -> None:
        output = io.StringIO()
        with patch.object(transcriber, "MISTRAL_AVAILABLE", False):
            with patch.dict(os.environ, {}, clear=True):
                with redirect_stdout(output):
                    result = transcriber.create_transcriber(use_mock=True)

        self.assertIsInstance(result, transcriber.MockTranscriber)
        message = output.getvalue().lower()
        self.assertIn("test/mock mode", message)
        self.assertIn("placeholder", message)
        self.assertIn("not", message)
        self.assertIn("transcription", message)

    def test_missing_mistralai_raises_in_normal_mode(self) -> None:
        with patch.object(transcriber, "MISTRAL_AVAILABLE", False):
            with patch.dict(os.environ, {}, clear=True):
                with self.assertRaisesRegex(RuntimeError, "mistralai"):
                    transcriber.create_transcriber(use_mock=False)

    def test_missing_api_key_raises_in_normal_mode(self) -> None:
        with patch.object(transcriber, "MISTRAL_AVAILABLE", True):
            with patch.dict(os.environ, {}, clear=True):
                with self.assertRaisesRegex(ValueError, "MISTRAL_API_KEY"):
                    transcriber.create_transcriber(api_key=None, use_mock=False)


class OutputMode(Enum):
    TYPE = "type"
    CLIPBOARD = "clipboard"
    BOTH = "both"


class StubKeyboard:
    class Listener:
        pass

    class Key:
        pass


def load_dictate_module():
    """Load dictate.py with offline stand-ins for optional desktop modules."""
    config_module = types.ModuleType("config")
    config_module.get_config = lambda: None
    config_module.OutputConfig = object

    audio_capture_module = types.ModuleType("audio_capture")
    audio_capture_module.AudioCapture = type("AudioCapture", (), {})

    local_module = types.ModuleType("transcriber_local")
    local_module.create_local_transcriber = lambda **kwargs: None
    local_module.WHISPER_AVAILABLE = False

    text_output_module = types.ModuleType("text_output")
    text_output_module.TextOutput = type("TextOutput", (), {})
    text_output_module.TextProcessor = type("TextProcessor", (), {})
    text_output_module.OutputMode = OutputMode

    tray_module = types.ModuleType("tray_icon")
    tray_module.create_indicator = lambda **kwargs: None
    tray_module.TrayStatus = type("TrayStatus", (), {})

    pynput_module = types.ModuleType("pynput")
    pynput_module.keyboard = StubKeyboard

    module_name = "dictate_fail_closed_test_target"
    spec = importlib.util.spec_from_file_location(
        module_name, REPOSITORY_ROOT / "dictate.py"
    )
    if spec is None or spec.loader is None:  # pragma: no cover - import guard
        raise RuntimeError("Could not load dictate.py")
    module = importlib.util.module_from_spec(spec)

    stubs = {
        "config": config_module,
        "audio_capture": audio_capture_module,
        "transcriber_local": local_module,
        "text_output": text_output_module,
        "tray_icon": tray_module,
        "pynput": pynput_module,
    }
    with patch.dict(sys.modules, stubs):
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
    return module


class MockStartupLabelTests(unittest.TestCase):
    def test_explicit_mock_startup_cannot_be_mistaken_for_transcription(self) -> None:
        dictate = load_dictate_module()

        class FakeApp:
            received_kwargs = None

            def __init__(self, **kwargs):
                type(self).received_kwargs = kwargs

            async def run(self):
                return None

        dictate.DictationApp = FakeApp
        output = io.StringIO()
        with patch.object(
            dictate.sys,
            "argv",
            ["dictate.py", "--mock", "--no-tray"],
        ):
            with redirect_stdout(output):
                dictate.main()

        self.assertTrue(FakeApp.received_kwargs["use_mock"])
        message = output.getvalue().lower()
        self.assertIn("test/mock mode", message)
        self.assertIn("placeholder", message)
        self.assertIn("not transcribed", message)


if __name__ == "__main__":
    unittest.main()
