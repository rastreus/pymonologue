"""
speech_recognizer.py — SFSpeechRecognizer wrapper for Pythonista.

Phase 1 uses file-based recording:
`sound.Recorder` -> `.m4a` file -> `SFSpeechRecognizer` URL request.
"""

from ctypes import c_long, c_void_p
import os
import tempfile
import threading
import time

import objc_util
import sound


AUTH_STATUS_NOT_DETERMINED = 0
AUTH_STATUS_DENIED = 1
AUTH_STATUS_RESTRICTED = 2
AUTH_STATUS_AUTHORIZED = 3

DEFAULT_AUTH_TIMEOUT = 10.0
DEFAULT_TRANSCRIBE_TIMEOUT = 20.0


class SpeechRecognitionError(RuntimeError):
    pass


def _load_speech_framework():
    objc_util.load_framework("Speech")


def _create_recognizer(locale: str = "en-US"):
    """
    Create and return an SFSpeechRecognizer instance.
    """
    _load_speech_framework()
    SFSpeechRecognizer = objc_util.ObjCClass("SFSpeechRecognizer")
    NSLocale = objc_util.ObjCClass("NSLocale")

    locale_obj = NSLocale.alloc().initWithLocaleIdentifier_(locale)
    return SFSpeechRecognizer.alloc().initWithLocale_(locale_obj)


def _authorization_label(status: int) -> str:
    return {
        AUTH_STATUS_NOT_DETERMINED: "not determined",
        AUTH_STATUS_DENIED: "denied",
        AUTH_STATUS_RESTRICTED: "restricted",
        AUTH_STATUS_AUTHORIZED: "authorized",
    }.get(status, f"unknown({status})")


def request_authorization(timeout: float = DEFAULT_AUTH_TIMEOUT) -> int:
    """
    Request speech recognition authorization and wait for the callback.
    """
    _load_speech_framework()
    SFSpeechRecognizer = objc_util.ObjCClass("SFSpeechRecognizer")

    event = threading.Event()
    result = {"status": AUTH_STATUS_NOT_DETERMINED}

    def _handler(_block, status):
        result["status"] = int(status)
        event.set()

    block = objc_util.ObjCBlock(_handler, restype=None, argtypes=[c_void_p, c_long])
    SFSpeechRecognizer.requestAuthorization_(block)

    if not event.wait(timeout):
        raise SpeechRecognitionError("speech authorization timed out")
    return result["status"]


def transcribe(
    audio_path: str,
    locale: str = "en-US",
    *,
    timeout: float = DEFAULT_TRANSCRIBE_TIMEOUT,
    auth_timeout: float = DEFAULT_AUTH_TIMEOUT,
) -> str:
    """
    Transcribe an audio file using SFSpeechRecognizer.
    """
    if not os.path.exists(audio_path):
        return ""

    status = request_authorization(auth_timeout)
    if status != AUTH_STATUS_AUTHORIZED:
        raise SpeechRecognitionError(
            f"speech recognition authorization is {_authorization_label(status)}"
        )

    recognizer = _create_recognizer(locale)
    if not recognizer or not recognizer.isAvailable():
        raise SpeechRecognitionError("speech recognizer is unavailable")

    SFSpeechURLRecognitionRequest = objc_util.ObjCClass("SFSpeechURLRecognitionRequest")
    request = SFSpeechURLRecognitionRequest.alloc().initWithURL_(objc_util.nsurl(audio_path))

    requires_on_device = objc_util.sel("setRequiresOnDeviceRecognition:")
    if request.respondsToSelector_(requires_on_device):
        request.setRequiresOnDeviceRecognition_(True)

    event = threading.Event()
    result_holder = {"text": "", "error": None}

    def _result_handler(_block, result_ptr, error_ptr):
        if error_ptr:
            error = objc_util.ObjCInstance(error_ptr)
            description = error.localizedDescription()
            result_holder["error"] = str(description or error)
            event.set()
            return

        if not result_ptr:
            return

        result = objc_util.ObjCInstance(result_ptr)
        transcription = result.bestTranscription()
        if transcription:
            result_holder["text"] = str(transcription.formattedString())
        if bool(result.isFinal()):
            event.set()

    result_block = objc_util.ObjCBlock(
        _result_handler,
        restype=None,
        argtypes=[c_void_p, c_void_p, c_void_p],
    )
    task = recognizer.recognitionTaskWithRequest_resultHandler_(request, result_block)

    if not event.wait(timeout):
        if task is not None:
            task.cancel()
        raise SpeechRecognitionError("speech transcription timed out")

    if result_holder["error"]:
        raise SpeechRecognitionError(result_holder["error"])

    return result_holder["text"]


def record_audio(duration: float = 3.0, suffix: str = ".m4a") -> str:
    """
    Record audio to a temp file using sound.Recorder.
    """
    path = tempfile.gettempdir() + "/pymonologue_rec" + suffix
    recorder = sound.Recorder(path)
    recorder.record()
    time.sleep(duration)
    recorder.stop()
    return path


class SpeechRecognizer:
    """
    Convenience wrapper around the module-level transcription helpers.
    """

    def __init__(
        self,
        locale: str = "en-US",
        *,
        timeout: float = DEFAULT_TRANSCRIBE_TIMEOUT,
        auth_timeout: float = DEFAULT_AUTH_TIMEOUT,
    ):
        self.locale = locale
        self.timeout = timeout
        self.auth_timeout = auth_timeout

    def request_authorization(self) -> int:
        return request_authorization(self.auth_timeout)

    def transcribe(self, audio_path: str) -> str:
        return transcribe(
            audio_path,
            self.locale,
            timeout=self.timeout,
            auth_timeout=self.auth_timeout,
        )


if __name__ == "__main__":
    print("Recording 3s...")
    path = record_audio(3.0)
    print(f"Recorded: {path}, exists: {os.path.exists(path)}")

    print("Transcribing...")
    text = transcribe(path)
    print(f"Transcript: {text}")
