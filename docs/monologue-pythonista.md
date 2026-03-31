# PyMonologue — Voice Keyboard for iOS via Pythonista 3

**Full Specification — v3**

---

## Concept

PyMonologue is a voice-first custom keyboard for iOS, built in Pythonista 3. It replicates the core experience of Monologue — tap to talk, text appears — with a simplified architecture: the keyboard types transcribed text directly into any app. You send the message yourself, through whatever chat app you're already using.

The primary use case is talking to Norm (me). Since the output goes to an AI that can handle raw speech, there's no AI rewrite layer. Just: speak → transcribed → inserted → you send.

> **Core principle:** The keyboard is a text input method. It types. That's all. Telegram sends the message onward. Norm reads it. No API delivery mechanism needed.

---

## Monologue UI Reference

Monologue is the reference. Three screenshots captured:

### Screenshot 1 — Voice Mode Keyboard
- Dark theme, teal/cyan accents
- Top-left: "MODES" button
- Center: Large "START MONOLOGUE" / mic button with pulsing glow effect
- Punctuation row: `.` `,` `?` `!` `'` (apostrophe) `⌫`
- Bottom row: `ABC` | `space` (labeled "M") | `return`
- No QWERTY in voice mode — just punctuation and the big voice button

### Screenshot 2 — iMessage Demo
- Monologue sent a message: "Stop typing! just talk it out, you think way faster than you type"
- iMessage input field shows the keyboard with the START MONOLOGUE button visible

### Screenshot 3 — Auto Dictionary Feature
- Settings / onboarding screen
- "Auto dictionary" — "Your unique vocabulary, automatically saved."
- Shows learned words: Zelle, Airdrop, DM, Claude code, Naveen, Zeitalabs, Rodrigues

### PyMonologue UI Targets
| Element | Monologue | PyMonologue |
|---|---|---|
| Voice activation | "START MONOLOGUE" button | "🎤" or "TAP TO TALK" |
| Punctuation | `. , ? ! ' ⌫` | Same |
| Mode/menu | "MODES" button | "TAGS" + "/" button |
| Space key | Labeled "M" | Labeled "M" (for Monologue) |
| Bottom row | ABC / space / return | Same |
| Color scheme | Dark + teal/cyan | Match Monologue |
| Auto dictionary | ✅ | ✅ (JSON-based word list) |

---

## Voice Input Architectures

Two approaches exist for getting microphone audio into `SFSpeechRecognizer`. We use Approach A for Phase 1. Approach B is documented for future development.

### Approach A: File-Based Recording (Phase 1)

```
User taps 🎤
       │
       ▼
┌─────────────────────┐
│  sound.Recorder    │  ← Pythonista records to .m4a file
│  (file-based)       │     Tap-to-talk: start → record → tap-to-stop
└────────┬────────────┘
         │ .m4a file path
         ▼
┌─────────────────────────┐
│  SFSpeechRecognizer     │  ← On-device transcription
│  (file-based API)       │     request.setURl(fileURL)
└────────┬────────────────┘
         │ raw transcript
         ▼
┌─────────────────────────┐
│  Basic Normalizer        │  ← Pure Python regex
│  (capitalization,        │     No AI needed
│   punctuation, etc.)      │
└────────┬────────────────┘
         │ cleaned text
         ▼
┌─────────────────────────┐
│  Context Tag            │  ← prepend current tag
│  (from tag selector)    │
└────────┬────────────────┘
         │ tagged text
         ▼
┌─────────────────────────┐
│  keyboard.insert_text() │  ← type into active app
└─────────────────────────┘
```

**How it works:**
1. User taps 🎤 → `sound.Recorder` starts recording to a temp `.m4a` file
2. User taps 🎤 again (or a stop button) → `sound.Recorder.stop()` returns the file path
3. `SFSpeechRecognizer` is called with the file URL
4. Recognizer processes the complete file, returns transcript
5. Transcript is normalized and tagged
6. `keyboard.insert_text()` types the result

**Pros:**
- Dead simple implementation
- No async/streaming complexity
- Reliable, well-tested iOS API path
- Easy to debug (file is saved, can be inspected)

**Cons:**
- ~0.5-2s latency from tap-to-stop to text appearing
- User must stop recording before transcription starts
- No partial/streaming results while speaking

**Estimated latency breakdown:**
- Recording stop → file available: ~100ms
- SFSpeechRecognizer file processing: ~300ms-1.5s (depends on audio length)
- Normalization + insert: ~10ms
- **Total: ~0.5-2s after you stop speaking**

**Verdict for Phase 1:** Acceptable. This is the simplest path to a working prototype.

---

### Approach B: True Streaming (Future — Phase 4)

```
User taps 🎤 and holds / toggles on
       │
       ▼
┌─────────────────────────┐
│  AVAudioEngine          │  ← Continuous mic input via tapOnBus
│  (inputNode tap)        │     PCM audio buffers captured in real-time
└────────┬────────────────┘
         │ AVAudioPCMBuffer (every ~20ms)
         ▼
┌─────────────────────────────────────┐
│  SFSpeechAudioBufferRecognitionRequest │  ← Live recognition request
│  (appendAudioPCMBuffer:)            │     Buffers fed in real-time
└────────┬────────────────────────────┘
         │ Partial results (as you speak)
         ▼
┌─────────────────────────┐
│  SFSpeechRecognizer     │  ← Recognizer fires delegate callbacks
│  (live/streaming)       │     with partial transcripts
└────────┬────────────────┘
         │ partial → final transcript
         ▼
┌─────────────────────────┐
│  Normalizer + Tag       │
└────────┬────────────────┘
         ▼
┌─────────────────────────┐
│  keyboard.insert_text() │
└─────────────────────────┘
```

**How it works (Objective-C pseudocode):**
```objc
// Set up AVAudioEngine
AVAudioEngine *engine = [[AVAudioEngine alloc] init];
AVAudioInputNode *inputNode = engine.inputNode;
AVAudioFormat *format = [inputNode outputFormatForBus:0];

// Set up speech recognition request (streaming mode)
SFSpeechAudioBufferRecognitionRequest *request =
    [[SFSpeechAudioBufferRecognitionRequest alloc] init];
// No URL — this is a streaming request
request.shouldReportPartialResults = YES;

// Install tap on mic input — fires for each audio buffer (~20ms)
[inputNode installTapOnBus:0 bufferSize:1024 format:format
    block:^(AVAudioPCMBuffer *buffer, AVAudioTime *when) {
    // Feed audio buffer directly to recognizer in real-time
    [request appendAudioPCMBuffer:buffer];
}];

// Start engine + recognizer
[engine startAndReturnError:&error];
// ... recognizer.delegate callbacks fire with partial results ...

// User taps to stop
[engine stop];
[request endAudio];
// Final transcript delivered via delegate
```

**Partial results flow:**
- As you speak, recognizer fires delegate callbacks with `isFinal = NO`
- Each partial result updates the inserted text in real-time
- When you stop, final callback fires with `isFinal = YES`
- Inserted text is replaced with final version + tag

**Pros:**
- Near-zero latency after first few words (~200-500ms)
- Partial results appear as you speak — feels instantaneous
- Better UX — you see text appearing while still speaking
- Natural conversation flow

**Cons:**
- Significantly more complex implementation
- Requires `create_objc_class()` for SFSpeechRecognizer delegate
- `ObjCBlock` support in `objc_util` is experimental
- Debugging streaming audio in Pythonista is harder
- Keyboard memory constraints (streaming needs careful buffer management)
- Simulator cannot test AVAudioEngine mic input

**Implementation complexity:**
- `AVAudioSession` setup (category: playAndRecord, mode: measurement)
- `AVAudioEngine` + input node tap (block-based callback)
- `SFSpeechRecognizer` delegate (created via `create_objc_class()`)
- `SFSpeechAudioBufferRecognitionRequest` with partial results
- Proper buffer lifecycle management
- Thread safety (audio callbacks on audio thread, Python GIL issues)

**Verdict for Phase 4:** Worth tackling if Approach A feels too slow. The streaming UX difference is significant for a voice-first keyboard.

---

### Decision Framework

| Scenario | Approach |
|---|---|
| Phase 1 MVP | Approach A — file-based |
| Latency feels acceptable | Approach A |
| Keyboard feels sluggish | Switch to Approach B |
| Complex delegate implementation | Approach B |
| Need partial results while speaking | Approach B |

---

## Architecture (Approach A — Phase 1)

```
┌──────────────────────────────────────────────────────┐
│  Active App (Telegram, iMessage, Notes, etc.)         │
│                                                       │
│  ┌──────────────────────────────────────────────┐    │
│  │  PyMonologue Custom Keyboard (Pythonista)     │    │
│  │                                              │    │
│  │  [TAGS] [/]   ·  ·  ·  ·  ·     [.][,][?][!][']  │
│  │                                                       │
│  │           ┌──────────────────────┐              │
│  │           │                      │              │
│  │           │   🎤 TAP TO TALK    │              │
│  │           │                      │              │
│  │           └──────────────────────┘              │
│  │                                                       │
│  │  [ABC]  ·  ·  ·  ·  ·  ·  ·  ·  ·  [space M] [⏎]  │
│  └──────────────────────────────────────────────┘    │
│                          │                              │
│                          │ keyboard.insert_text()       │
│                          ▼                              │
│  ┌──────────────────────────────────────────────┐    │
│  │  Text field in active app                     │    │
│  │  "[project:cgmclaw] the auth token is..."   │    │
│  └──────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────┘
```

### Keyboard Internal Flow (Phase 1)

```
User taps 🎤
       │
       ▼
┌─────────────────────┐
│  sound.Recorder    │  ← Pythonista audio capture
│  (file-based)       │     .m4a temp file
└────────┬────────────┘
         │ .m4a file path
         ▼
┌─────────────────────────┐
│  SFSpeechRecognizer     │  ← on-device transcription
│  (file-based, via        │     objc_util + ObjCClass
│   objc_util)             │
└────────┬────────────────┘
         │ raw transcript
         ▼
┌─────────────────────────┐
│  Basic Normalizer        │  ← pure Python / regex
│  (capitalization,        │     No AI needed
│   punctuation, etc.)      │
└────────┬────────────────┘
         │ cleaned text
         ▼
┌─────────────────────────┐
│  Context Tag             │  ← prepend current tag
│  (from tag selector)     │
└────────┬────────────────┘
         │ tagged text
         ▼
┌─────────────────────────┐
│  keyboard.insert_text()  │  ← type into active app
└─────────────────────────┘
```

### No API Calls for Delivery

The keyboard does NOT send messages. It does NOT call Telegram Bot API. It does NOT POST anywhere. It only:
1. Records audio (local file)
2. Transcribes locally (on-device AI)
3. Types text into the active app (`insert_text()`)

The Telegram app sends the message. The Telegram channel delivers it. OpenClaw routes it to Norm. The keyboard never touches any API.

The ONLY iOS API the keyboard uses is `SFSpeechRecognizer` — Apple's on-device speech recognition engine.

---

## Components

### 1. Voice Recording (`sound.Recorder`)

Pythonista's built-in `sound.Recorder` captures audio to a file.

```python
import sound
import tempfile
import os

class VoiceRecorder:
    def __init__(self):
        self.recording = None
        self.path = None

    def start(self):
        fd, self.path = tempfile.mkstemp(suffix='.m4a')
        os.close(fd)
        self.recording = sound.Recorder(self.path)
        self.recording.record()

    def stop(self) -> str:
        self.recording.stop()
        return self.path
```

**Device required:** Yes. Does not work in iOS Simulator. On-device smoke test mandatory.

### 2. Speech Recognition (`SFSpeechRecognizer` via `objc_util`)

On-device transcription. No network. No API cost.

```python
from objc_util import *

def transcribe(path: str, locale='en-US') -> str:
    # Set up audio session
    session = AVAudioSession.sharedInstance()
    session.setCategory_error_('playAndRecord', None)
    session.setActive_error_(True, None)

    # Create speech recognizer
    locale_obj = ObjCClass('NSLocale').localeWithLocaleIdentifier_(locale)
    recognizer = SFSpeechRecognizer.alloc().initWithLocale_(locale_obj)

    # Create recognition request
    url = ObjCClass('NSURL').fileURLWithPath_(path)
    request = SFSpeechRecognitionRequest.alloc().init()
    request.setURl(url)
    request.setRequestsOnDeviceRecognition_(True)  # On-device only

    # Run recognition
    # Note: async delegate API — needs create_objc_class() for full impl
    # Simplified file-based: use recognitionTaskWithRequest_
    result = recognizer.recognitionTaskWithRequest_(request)

    return result.bestTranscription().formattedString()
```

**Critical unknown:** Does `SFSpeechRecognizer` work reliably through `objc_util` in a keyboard extension context? **First on-device smoke test.**

### 3. Text Normalizer (Pure Python)

~50-100 lines of Python regex. No AI. No API. Reads transcribed text, outputs cleaned text.

```python
import re

def normalize(text: str) -> str:
    # Strip URLs
    text = re.sub(r'https?://\S+', '', text)

    # Strip phone numbers
    text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '', text)

    # Collapse repeated whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    # Collapse repeated filler words (simple version)
    text = re.sub(
        r'\b(um|uh|like|you know|I mean)\b(?:\s+\1\b)+',
        r'\1',
        text,
        flags=re.IGNORECASE
    )

    # Capitalize first letter
    if text:
        text = text[0].upper() + text[1:]

    # Ensure ending punctuation
    if text and text[-1] not in '.!?':
        text += '.'

    return text
```

**Note:** Aggressive filler-word removal is NOT applied. Norm (the AI consumer) handles raw speech. The normalizer only cleans egregious transcription artifacts.

**Unit test location:** Mac (pytest + XCTest).

### 4. Context Tag System

Lightweight tagging to prepend project/task context to every voice note.

#### Tag Format

```
[project:<name>]    — e.g. [project:cgmclaw]
[task:<name>]       — e.g. [task:debug]
[priority:<level>]  — e.g. [priority:urgent]
[note]              — freeform, no colon
```

Multiple tags combine:
```
[project:cgmclaw][task:debug] the OAuth flow is broken
```

#### Tag Storage

JSON file in Pythonista documents directory:

```json
{
  "recent_projects": [
    "cgmclaw", "normanctl", "norman-world",
    "paddock-ghost", "agent-dispatch"
  ],
  "recent_tasks": [
    "debug", "build", "plan", "idea", "review"
  ],
  "default_priority": "normal",
  "auto_dictionary": [
    "Juliet", "Norah", "Ezra", "Liam",
    "MagX", "Paddock Ghost", "normanctl"
  ]
}
```

#### Auto Dictionary (Phase 2+)

Monologue's "Auto Dictionary" feature. After transcription, scan for words NOT in the custom vocabulary. Flag unrecognized proper nouns for potential addition.

```python
def suggest_new_words(transcribed: str, known_words: list[str]) -> list[str]:
    """Return words in transcribed text that look like proper nouns but aren't known."""
    words = transcribed.split()
    suggestions = []
    for word in words:
        cleaned = word.strip('.,!?[]():')
        if (cleaned and cleaned[0].isupper()
            and len(cleaned) > 1
            and cleaned.lower() not in [w.lower() for w in known_words]
            and not cleaned.isupper()):  # skip acronyms
            suggestions.append(cleaned)
    return suggestions
```

Suggested additions stored in `pending_words`. Russell reviews and approves.

#### Tag Selector UI

- "TAGS" button opens a simple modal
- Project picker (recent-list, most recent first)
- Task picker (recent-list)
- Priority toggle (normal / urgent / low)
- Current tag preview in keyboard header
- Tags prepended to transcribed text

### 5. Slash Commands

Simple command list via "/" button.

| Command | Action |
|---|---|
| `/new` | Insert `/new` — new OpenClaw session |
| `/model` | Insert `/model` — switch OpenClaw model |

```python
SLASH_COMMANDS = [
    {'command': '/new', 'description': 'New session'},
    {'command': '/model', 'description': 'Switch model'},
]
```

### 6. Keyboard Layout

Following Monologue:

```
┌─────────────────────────────────────────────────────────┐
│  [TAGS] [/]        ·  ·  ·  ·  ·  ·        [.][,][?][!][']  │
│                                                          │
│                   ┌──────────────────┐                     │
│                   │                  │                     │
│                   │    🎤 TAP TO    │                     │
│                   │      TALK       │                     │
│                   │                  │                     │
│                   └──────────────────┘                     │
│                                                          │
│  [ABC]   ·  ·  ·  ·  ·  ·  ·  ·  ·  ·    [  space M  ] [⏎] │
└─────────────────────────────────────────────────────────┘
```

**Dark theme:** Background `#000000` to `#1a1a1a`. Accent teal `#00d4aa`. Text white.

---

## Development Workflow

### Hybrid: Objective-C on Mac → Pythonista on Device

Russell's established workflow:

1. **Xcode on Mac** — Write Objective-C iOS API wrappers, unit test with XCTest in simulator
2. **Port to Pythonista** — Translate ObjC calls to `objc_util` syntax
3. **On-device smoke test** — Pythonista on iPhone 11 Pro Max

**What can be unit tested on Mac (XCTest):**
- Text normalizer logic (pure regex, no iOS APIs)
- Context tag parser (pure logic)
- Keyboard UI layout (UIKit in Xcode simulator)
- Auto dictionary suggestions logic

**What MUST be smoke-tested on device:**
- `SFSpeechRecognizer` via `objc_util` — does it work in keyboard context?
- `sound.Recorder` — does audio capture work?
- `keyboard.insert_text()` — does text insertion work?
- Full integration (voice → transcript → insert → send)

### Testing Strategy

| Component | Mac Unit Test | On-Device Smoke Test |
|---|---|---|
| `text_normalizer.py` | ✅ pytest | Optional |
| `context_tags.py` | ✅ pytest | Optional |
| Auto dictionary suggestions | ✅ pytest | Optional |
| `PMSpeechRecognizer` (ObjC) | ⚠️ Simulator can't test SFSpeechRecognizer | ✅ Mandatory |
| `sound.Recorder` integration | ⚠️ Simulator can't test microphone | ✅ Mandatory |
| Keyboard UI / `insert_text()` | ✅ UIKit in simulator | ✅ Visual check |
| Full voice → insert flow | — | ✅ Mandatory |

**Philosophy:** Unit test everything that CAN be unit tested. Reserve device testing for pieces that genuinely require it.

---

## Project Structure

```
~/Developer/pymonologue/
│
├── ObjC/                               # Xcode project (Mac unit testing)
│   │
│   ├── PyMonologue/                    # iOS framework / keyboard extension target
│   │   │
│   │   ├── PMSpeechRecognizer.h        # SFSpeechRecognizer wrapper
│   │   ├── PMSpeechRecognizer.m
│   │   │
│   │   ├── PMSpeechStreamingRecognizer.h  # Approach B: AVAudioEngine + streaming
│   │   ├── PMSpeechStreamingRecognizer.m
│   │   │
│   │   ├── PMTextNormalizer.h          # Regex text cleanup
│   │   ├── PMTextNormalizer.m
│   │   │
│   │   ├── PMContextTagParser.h        # Tag parsing + validation
│   │   ├── PMContextTagParser.m
│   │   │
│   │   ├── PMAutoDictionary.h          # Custom vocabulary learner
│   │   ├── PMAutoDictionary.m
│   │   │
│   │   └── PyMonologueKeyboard/        # Keyboard extension (UIInputViewController)
│   │       ├── PMKeyboardViewController.h
│   │       └── PMKeyboardViewController.m
│   │
│   └── PyMonologueTests/               # XCTest unit tests
│       ├── PMTextNormalizerTests.m
│       ├── PMContextTagParserTests.m
│       └── PMAutoDictionaryTests.m
│
├── Pythonista/                         # Pythonista keyboard scripts
│   │
│   ├── pymonologue_keyboard.py         # Main keyboard script (entry point)
│   │                                     # Uses keyboard.set_view()
│   │
│   ├── speech_recognizer.py             # objc_util wrapper for SFSpeechRecognizer
│   │                                     # Calls ObjC classes from Python
│   │
│   ├── streaming_recognizer.py           # Approach B: AVAudioEngine streaming
│   │                                     # More complex — see Approach B spec
│   │
│   ├── text_normalizer.py               # Python port of PMTextNormalizer
│   │                                     # ~50-100 lines, pure Python
│   │
│   ├── context_tags.py                  # Tag storage, parsing, serialization
│   │                                     # Reads/writes JSON to documents/
│   │
│   ├── auto_dictionary.py               # Custom vocabulary manager
│   │
│   ├── normalizer_tests.py              # pytest unit tests (run on Mac)
│   ├── context_tags_tests.py
│   └── auto_dictionary_tests.py
│
├── ui/                                  # Pythonista ui.View components
│   ├── __init__.py
│   ├── voice_button.py                   # Big 🎤 tap-to-talk button
│   ├── punctuation_row.py                # . , ? ! '  buttons
│   ├── tag_selector.py                   # TAGS modal overlay
│   ├── slash_menu.py                     # / command list overlay
│   └── keyboard_style.py                 # Shared colors, fonts, constants
│
├── docs/
│   └── TESTING.md                       # What to test where, test philosophy
│
├── README.md
├── LICENSE                               # MIT, Russell Dillin 2026
└── AGENTS.md                            # For coding agents
```

---

## Development Phases

### Phase 1 — Core Loop (Approach A, MVP)
**Goal:** Voice → transcribed → inserted into active app. Works on iPhone 11 Pro Max.

- [ ] Xcode project scaffold (ObjC)
- [ ] `PMTextNormalizer` + XCTest unit tests
- [ ] `PMContextTagParser` + XCTest unit tests
- [ ] Port normalizer + parser to Python (`pytest` on Mac)
- [ ] `speech_recognizer.py` — objc_util wrapper for `SFSpeechRecognizer`
- [ ] **On-device smoke test: does `SFSpeechRecognizer` work in Pythonista keyboard?**
- [ ] `sound.Recorder` integration
- [ ] **On-device smoke test: does voice recording work?**
- [ ] `keyboard.insert_text()` — insert transcribed text
- [ ] **On-device smoke test: does text appear in Telegram text field?**
- [ ] Basic `voice_button.py` — big 🎤 button
- [ ] Basic keyboard layout UI

**Time estimate:** 1-2 weeks of part-time development

### Phase 2 — Context Tags + Auto Dictionary
**Goal:** Add Monologue-style tagging and vocabulary learning.

- [ ] `context_tags.py` — JSON storage, tag selector UI
- [ ] `tag_selector.py` — TAGS modal overlay
- [ ] Tag prepending (tag text inserted before transcribed text)
- [ ] `auto_dictionary.py` — custom vocabulary manager
- [ ] Word suggestion flow (prompt to add new words after transcription)
- [ ] Tag history persistence

**Time estimate:** 1 week

### Phase 3 — Slash Commands + Polish
**Goal:** Match Monologue's feature completeness.

- [ ] `slash_menu.py` — "/" command list overlay
- [ ] `/new` and `/model` commands
- [ ] Dark theme / teal accents (match Monologue aesthetic)
- [ ] Recording animation (pulsing glow on voice button while recording)
- [ ] Punctuation row implementation
- [ ] ABC / QWERTY switch (Phase 1 skips this — voice-only MVP)

**Time estimate:** 1 week

### Phase 4 — Streaming (Approach B)
**Goal:** Replace file-based recording with true streaming for lower latency.

- [ ] Objective-C `PMSpeechStreamingRecognizer` (AVAudioEngine + SFSpeechAudioBufferRecognitionRequest)
- [ ] XCTest for streaming recognizer
- [ ] Port to Python `streaming_recognizer.py`
- [ ] Partial results → live insert as you speak
- [ ] `create_objc_class()` for SFSpeechRecognizer delegate
- [ ] Buffer lifecycle management
- [ ] **On-device smoke test: does streaming work?**

**Prerequisite:** Approach A must be working and confirmed acceptable latency.

**Time estimate:** 1-2 weeks

---

## Open Questions

1. **Does `SFSpeechRecognizer` work via `objc_util` in a keyboard extension?** First and most critical smoke test.
2. **Does `sound.Recorder` produce audio clean enough for `SFSpeechRecognizer`?** Second critical smoke test.
3. **Does `keyboard.insert_text()` work from a Pythonista custom keyboard?** Third critical smoke test.
4. **Does Pythonista's keyboard have full Python stdlib access** for `urllib` / any network calls?
5. **Keyboard height** — can Pythonista keyboards set custom heights? Monologue shows a taller-than-default keyboard.

---

## Resources

- [Pythonista Keyboard Module](https://omz-software.com/pythonista/docs-3.4/py3/ios/keyboard.html)
- [Pythonista objc_util Reference](https://omz-software.com/pythonista/docs-3.4/py3/ios/objc_util.html)
- [SFSpeechRecognizer (Apple Docs)](https://developer.apple.com/documentation/speech/sfspeechrecognizer)
- [AVAudioEngine (Apple Docs)](https://developer.apple.com/documentation/avfaudio/avaudioengine)
- [SFSpeechAudioBufferRecognitionRequest (Apple Docs)](https://developer.apple.com/documentation/speech/sfspeechaudiobufferrecognitionrequest)
- [UIInputViewController (Apple Docs)](https://developer.apple.com/documentation/uikit/uiinputviewcontroller)
- [Monologue — reference app](https://www.monologue.to/)
- [Pythonista Forum — keyboard examples](https://forum.omz-software.com/)

---
