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

try:
    import objc_util
except ImportError:  # pragma: no cover - exercised on device, not on Mac
    objc_util = None

try:
    import sound
except ImportError:  # pragma: no cover - exercised on device, not on Mac
    sound = None


AUTH_STATUS_NOT_DETERMINED = 0
AUTH_STATUS_DENIED = 1
AUTH_STATUS_RESTRICTED = 2
AUTH_STATUS_AUTHORIZED = 3

DEFAULT_AUTH_TIMEOUT = 10.0
DEFAULT_TRANSCRIBE_TIMEOUT = 20.0

_DELEGATE_REGISTRY = {}
_SPEECH_TASK_DELEGATE_CLASS = None


class SpeechRecognitionError(RuntimeError):
    pass


class _RecognitionResultCollector:
    def __init__(self):
        self._event = threading.Event()
        self._text = ""
        self._error_message = ""

    def record_transcription(self, text: str):
        if text:
            self._text = text

    def finish(self, success: bool, error_message: str = ""):
        if not success and error_message:
            self._error_message = error_message
        self._event.set()

    def wait_for_result(self, timeout: float) -> str:
        if not self._event.wait(timeout):
            raise SpeechRecognitionError("speech transcription timed out")
        if self._error_message:
            raise SpeechRecognitionError(self._error_message)
        return self._text


def _require_objc_util():
    if objc_util is None:
        raise SpeechRecognitionError("objc_util is unavailable outside Pythonista on iOS")


def _require_sound():
    if sound is None:
        raise SpeechRecognitionError("sound module is unavailable outside Pythonista on iOS")


def _load_speech_framework():
    _require_objc_util()
    objc_util.load_framework("Speech")


def _objc_ptr_value(obj) -> int:
    ptr = getattr(obj, "ptr", obj)
    value = getattr(ptr, "value", None)
    if value is not None:
        return int(value)
    return int(ptr)


def _task_error_message(task) -> str:
    error = task.error()
    if not error:
        return "speech recognition failed"
    description = error.localizedDescription()
    domain = error.domain() or "unknown-domain"
    code = int(error.code())
    return f"{description or error} [{domain} code={code}]"


def _supports_on_device_recognition(recognizer) -> bool:
    selector = objc_util.sel("supportsOnDeviceRecognition")
    if recognizer.respondsToSelector_(selector):
        return bool(recognizer.supportsOnDeviceRecognition())
    return False


def _should_require_on_device(prefer_on_device: bool, supports_on_device: bool) -> bool:
    return bool(prefer_on_device and supports_on_device)


def _speech_task_delegate_class():
    global _SPEECH_TASK_DELEGATE_CLASS

    if _SPEECH_TASK_DELEGATE_CLASS is not None:
        return _SPEECH_TASK_DELEGATE_CLASS

    _load_speech_framework()
    NSObject = objc_util.ObjCClass("NSObject")

    def speechRecognitionTask_didHypothesizeTranscription_(_self, _cmd, task, transcription):
        collector = _DELEGATE_REGISTRY.get(int(_self))
        if collector is None or not transcription:
            return
        transcription_obj = objc_util.ObjCInstance(transcription)
        collector.record_transcription(str(transcription_obj.formattedString()))

    def speechRecognitionTask_didFinishRecognition_(_self, _cmd, task, result):
        collector = _DELEGATE_REGISTRY.get(int(_self))
        if collector is None or not result:
            return
        result_obj = objc_util.ObjCInstance(result)
        transcription = result_obj.bestTranscription()
        if transcription:
            collector.record_transcription(str(transcription.formattedString()))

    def speechRecognitionTask_didFinishSuccessfully_(_self, _cmd, task, successfully):
        key = int(_self)
        collector = _DELEGATE_REGISTRY.pop(key, None)
        if collector is None:
            return

        success = bool(successfully)
        error_message = ""
        if not success:
            task_obj = objc_util.ObjCInstance(task)
            error_message = _task_error_message(task_obj)
        collector.finish(success=success, error_message=error_message)

    methods = [
        speechRecognitionTask_didHypothesizeTranscription_,
        speechRecognitionTask_didFinishRecognition_,
        speechRecognitionTask_didFinishSuccessfully_,
    ]

    _SPEECH_TASK_DELEGATE_CLASS = objc_util.create_objc_class(
        "PyMonologueSpeechTaskDelegate",
        NSObject,
        methods=methods,
        protocols=["SFSpeechRecognitionTaskDelegate"],
    )
    return _SPEECH_TASK_DELEGATE_CLASS


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


def authorization_status() -> int:
    """
    Return the current speech-recognition authorization status without
    requesting permission.
    """
    _load_speech_framework()
    SFSpeechRecognizer = objc_util.ObjCClass("SFSpeechRecognizer")
    return int(SFSpeechRecognizer.authorizationStatus())


def _request_authorization_via_block(timeout: float = DEFAULT_AUTH_TIMEOUT) -> int:
    """
    Request speech recognition authorization using the block-based API.
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


def request_authorization(timeout: float = DEFAULT_AUTH_TIMEOUT) -> int:
    """
    Request speech recognition authorization and wait for the callback.

    Avoid the block path when the status is already resolved because
    Pythonista's block bridge is experimental.
    """
    status = authorization_status()
    if status != AUTH_STATUS_NOT_DETERMINED:
        return status
    return _request_authorization_via_block(timeout)


def transcribe(
    audio_path: str,
    locale: str = "en-US",
    *,
    timeout: float = DEFAULT_TRANSCRIBE_TIMEOUT,
    auth_timeout: float = DEFAULT_AUTH_TIMEOUT,
    prefer_on_device: bool = False,
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
    supports_on_device = _supports_on_device_recognition(recognizer)

    SFSpeechURLRecognitionRequest = objc_util.ObjCClass("SFSpeechURLRecognitionRequest")
    request = SFSpeechURLRecognitionRequest.alloc().initWithURL_(objc_util.nsurl(audio_path))

    requires_on_device = objc_util.sel("setRequiresOnDeviceRecognition:")
    if request.respondsToSelector_(requires_on_device) and _should_require_on_device(
        prefer_on_device,
        supports_on_device,
    ):
        request.setRequiresOnDeviceRecognition_(True)

    should_report_partial = objc_util.sel("setShouldReportPartialResults:")
    if request.respondsToSelector_(should_report_partial):
        request.setShouldReportPartialResults_(False)

    collector = _RecognitionResultCollector()
    delegate_class = _speech_task_delegate_class()
    delegate = delegate_class.alloc().init()
    _DELEGATE_REGISTRY[_objc_ptr_value(delegate)] = collector

    task = recognizer.recognitionTaskWithRequest_delegate_(request, delegate)

    try:
        return collector.wait_for_result(timeout)
    except SpeechRecognitionError:
        if task is not None:
            task.cancel()
        raise


def record_audio(duration: float = 3.0, suffix: str = ".m4a") -> str:
    """
    Record audio to a temp file using sound.Recorder.
    """
    _require_sound()
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
        prefer_on_device: bool = False,
    ):
        self.locale = locale
        self.timeout = timeout
        self.auth_timeout = auth_timeout
        self.prefer_on_device = prefer_on_device

    def request_authorization(self) -> int:
        return request_authorization(self.auth_timeout)

    def transcribe(self, audio_path: str) -> str:
        return transcribe(
            audio_path,
            self.locale,
            timeout=self.timeout,
            auth_timeout=self.auth_timeout,
            prefer_on_device=self.prefer_on_device,
        )


if __name__ == "__main__":
    print("Recording 3s...")
    path = record_audio(3.0)
    print(f"Recorded: {path}, exists: {os.path.exists(path)}")

    print("Transcribing...")
    text = transcribe(path)
    print(f"Transcript: {text}")
