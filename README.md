# PyMonologue

PyMonologue is a voice-first custom keyboard for iOS, built in Pythonista 3. Tap to talk, transcribe, and insert text directly into any app. The primary use case is talking to Norm via Telegram.

**Reference app:** [Monologue](https://www.monologue.to/)

The current product and implementation reference lives in [`docs/monologue-pythonista.md`](./docs/monologue-pythonista.md).

![Norm using PyMonologue](./images/norm_pymonologue.png)

## Active Architecture

Two voice input approaches exist:

- **Phase 1:** File-based recording via `sound.Recorder` -> `.m4a` -> `SFSpeechRecognizer` -> `keyboard.insert_text()`
- **Phase 4:** True streaming via `AVAudioEngine` -> `SFSpeechAudioBufferRecognitionRequest`

Phase 1 is the active path. Streaming is future work unless explicitly called for.

## Project Structure

```text
pymonologue/
├── ObjC/                         # Xcode reference / simulator prototyping
├── Pythonista/
│   ├── pymonologue_keyboard.py   # Keyboard runtime + preview harness
│   ├── speech_recognizer.py      # SFSpeechRecognizer bridge via objc_util
│   ├── voice_workflow.py         # Pure-python workflow core
│   ├── keyboard_model.py         # Phase-1 keyboard view model
│   ├── text_normalizer.py
│   ├── context_tags.py
│   ├── auto_dictionary.py
│   └── ui/                       # Thin Pythonista UI layer
├── smoke_tests/                  # Device-only smoke tests
├── docs/                         # Product and testing system of record
├── SPEC.md                       # Legacy phase-1 skeleton notes
├── AGENTS.md                     # Agent-facing map into the repo
└── README.md                     # Human-facing overview
```

## Harness

This repo uses a lightweight harness-oriented workflow:

- Repo-local docs are the system of record.
- The pure-Python core is where most behavior should be tested first.
- The Pythonista UI layer should stay thin and adapter-like.
- Device-only concerns are isolated behind smoke tests and preview tooling.
- If the workflow struggles, improve the harness with tests, docs, scripts, or guardrails instead of relying on tribal knowledge.

## Setup

1. Install Pythonista 3 on iPhone 11 Pro Max.
2. Ensure the repo uses Python 3.10.20 via `.python-version`.
3. Create the local venv and install tooling:

```bash
python -m venv .venv
.venv/bin/pip install --upgrade pip pytest
```

4. Copy the `Pythonista/` scripts to Pythonista’s scripts directory on device.
5. Add the Pythonista keyboard in iOS Settings.
6. Enable Full Access.

For automated or agent-driven use, call the venv binaries directly, e.g. `.venv/bin/pytest`.

## Verification

Local deterministic checks:

```bash
.venv/bin/python -m py_compile Pythonista/*.py Pythonista/ui/*.py smoke_tests/*.py
.venv/bin/pytest Pythonista/normalizer_tests.py Pythonista/context_tags_tests.py Pythonista/auto_dictionary_tests.py Pythonista/voice_workflow_tests.py Pythonista/keyboard_model_tests.py -q
```

Device-only smoke tests:

1. `smoke_tests/smoke1_insert.py`
2. `smoke_tests/smoke2_recorder.py`
3. `smoke_tests/smoke3_speech.py`

Use the preview mode in `Pythonista/pymonologue_keyboard.py` to iterate on the UI and workflow in Pythonista before testing the actual keyboard extension.

## Current UI Target

The current Phase 1 UI target is the Monologue voice keyboard shell:

- `MODES`
- one dominant voice surface
- punctuation row `. , ? ! ' ⌫`
- bottom row `ABC / M / return`

## License

MIT — Russell Dillin, 2026.
