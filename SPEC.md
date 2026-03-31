# PyMonologue Phase 1 Spec

Primary product reference: [`docs/monologue-pythonista.md`](./docs/monologue-pythonista.md)

## Goal

Ship a reliable Phase 1 voice keyboard in Pythonista 3 on Russell's iPhone 11 Pro Max:

1. Tap to start recording.
2. Tap again to stop.
3. Transcribe the recorded `.m4a` with `SFSpeechRecognizer`.
4. Normalize the transcript.
5. Prepend active context tags.
6. Insert the final text into the active app.

Phase 1 is explicitly file-based. Do not replace it with streaming unless requested.

## Runtime Strategy

- Primary runtime: Pythonista keyboard + `objc_util`
- Native bridge: `SFSpeechRecognizer` via `Pythonista/speech_recognizer.py`
- Testable core: pure Python workflow and text-processing modules
- Secondary harness: ObjC/Xcode project for reference and simulator-friendly UI prototyping

The ObjC project is useful, but it is not the source of truth for shipped behavior. The real runtime that matters is the Pythonista keyboard.

## Phase 1 Scope

### Included

- File-based recording with `sound.Recorder`
- File-based transcription with `SFSpeechRecognizer`
- Transcript normalization
- Context-tag prepending
- Auto-dictionary persistence
- Monologue-inspired voice-mode keyboard shell
- Preview mode for local UI/workflow iteration in Pythonista
- Device smoke tests for insert, recorder, and speech

### Excluded

- Streaming transcription
- AI rewrite layer
- Network delivery APIs
- Rich settings/product surfaces beyond what is needed to support Phase 1

## Current UI Contract

The active Phase 1 keyboard should match the Monologue voice-mode shell as closely as practical:

- `MODES` button
- One dominant voice surface
- Punctuation row: `. , ? ! ' ⌫`
- Bottom row: `ABC / M / return`
- Dark shell, teal voice surface, subdued secondary controls

The main keyboard surface should stay minimal. Secondary flows such as tag selection and slash commands should live behind overlays or mode menus.

## Code Structure

### Pure-Python Core

- `Pythonista/text_normalizer.py`
- `Pythonista/context_tags.py`
- `Pythonista/auto_dictionary.py`
- `Pythonista/voice_workflow.py`
- `Pythonista/keyboard_model.py`

### Pythonista Runtime Layer

- `Pythonista/pymonologue_keyboard.py`
- `Pythonista/speech_recognizer.py`
- `Pythonista/ui/`

### Reference / Secondary Harness

- `ObjC/`

## Verification Strategy

### Local Deterministic Checks

Run on Mac with the repo venv:

```bash
.venv/bin/python -m py_compile Pythonista/*.py Pythonista/ui/*.py smoke_tests/*.py
.venv/bin/pytest Pythonista/normalizer_tests.py Pythonista/context_tags_tests.py Pythonista/auto_dictionary_tests.py Pythonista/voice_workflow_tests.py Pythonista/keyboard_model_tests.py -q
```

### Device-Only Smoke Tests

Run on iPhone 11 Pro Max:

1. `smoke_tests/smoke1_insert.py`
   - Confirms `keyboard.insert_text()` works in the real keyboard context.

2. `smoke_tests/smoke2_recorder.py`
   - Confirms `sound.Recorder` can produce a valid file in the keyboard sandbox.

3. `smoke_tests/smoke3_speech.py`
   - Confirms `SFSpeechRecognizer` authorization and actual file transcription work through `objc_util`.

If speech or recording fails in the real Pythonista keyboard context, stop and reassess architecture before adding more product polish.

## Acceptance Criteria

Phase 1 is successful when all of the following are true:

- The local deterministic checks pass.
- The three device smoke tests pass.
- The Pythonista preview harness is usable for local iteration.
- In the real keyboard, stop-recording always happens before transcription starts.
- A short dictated utterance is inserted into Notes or Telegram as normalized, tagged text.
- The Phase 1 UI feels structurally like Monologue voice mode, even if not pixel-perfect.

## Working Rule

If the codebase or workflow becomes harder for agents or humans to reason about, improve the harness:

- add tests
- tighten docs
- add preview tools
- simplify adapters
- move logic out of platform glue and into the pure-Python core
