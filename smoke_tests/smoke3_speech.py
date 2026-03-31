import os
import tempfile
import time
from pathlib import Path
import sys

import sound

THIS_DIR = Path(__file__).resolve().parent
PYTHONISTA_DIR = THIS_DIR.parent / 'Pythonista'
if str(PYTHONISTA_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHONISTA_DIR))

from speech_recognizer import SpeechRecognitionError, SpeechRecognizer, authorization_status


path = tempfile.gettempdir() + '/smoke_test.m4a'

r = sound.Recorder(path)
print('Recording 3s...')
r.record()
time.sleep(3)
r.stop()
print(f'Recorded: {os.path.exists(path)}, size: {os.path.getsize(path)}')

recognizer = SpeechRecognizer()

try:
    print(f'Authorization status before transcribe: {authorization_status()}')
    transcript = recognizer.transcribe(path)
    print(f'Transcript: {transcript!r}')
except SpeechRecognitionError as e:
    print(f'SPEECH ERROR: {e}')
except Exception as e:
    print(f'FAILED: {type(e).__name__}: {e}')
