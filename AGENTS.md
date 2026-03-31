# AGENTS.md — PyMonologue

PyMonologue is a voice-first custom keyboard for iOS built in Pythonista 3. The primary user is Russell Dillin.

## Start Here

- Product and implementation reference: [`docs/monologue-pythonista.md`](./docs/monologue-pythonista.md)
- Device and smoke-test workflow: [`docs/TESTING.md`](./docs/TESTING.md)
- Legacy phase-1 skeleton notes: [`SPEC.md`](./SPEC.md)
- Pythonista APIs:
  - `keyboard`: https://omz-software.com/pythonista/docs-3.4/py3/ios/keyboard.html
  - `ui`: https://omz-software.com/pythonista/docs-3.4/py3/ios/ui.html
  - `objc_util`: https://omz-software.com/pythonista/docs-3.4/py3/ios/objc_util.html
- Visual reference: `images/Monologue-Screenshot-1.png`, `images/Monologue-Screenshot-2.png`, `images/Monologue-Screenshot-3.png`

## Harness Principles

- `AGENTS.md` is the map, not the encyclopedia. Repo-local docs are the system of record.
- If a decision matters to future agents, write it into the repository. Do not leave critical context only in chat.
- When an agent struggles, improve the harness: add tests, smoke scripts, preview tools, docs, or guardrails. Do not compensate with prompt sprawl.
- Prefer deterministic checks over prose whenever possible.
- Keep change sets small, mechanically verifiable, and easy for a later agent to inspect.

## Architecture Guardrails

- Keep the pure-Python core testable on Mac:
  - `Pythonista/text_normalizer.py`
  - `Pythonista/context_tags.py`
  - `Pythonista/auto_dictionary.py`
  - `Pythonista/voice_workflow.py`
  - `Pythonista/keyboard_model.py`
- Keep Pythonista-specific code thin:
  - `Pythonista/pymonologue_keyboard.py`
  - `Pythonista/speech_recognizer.py`
  - `Pythonista/ui/`
- The shipped runtime is Pythonista + `objc_util`. The ObjC Xcode project is a reference/prototyping surface, not the primary runtime.
- Phase 1 remains file-based recording. Do not introduce streaming unless explicitly asked.

## Product Constraints

- The keyboard types text. It does not POST messages or call delivery APIs.
- Current UI target is the Monologue voice-mode shell:
  - `MODES`
  - dominant voice surface
  - punctuation row `. , ? ! ' ⌫`
  - bottom row `ABC / M / return`
- Use the preview mode in `Pythonista/pymonologue_keyboard.py` for rapid iteration before switching to the real keyboard extension.

## Verification

- Local deterministic checks:
  - `.venv/bin/python -m py_compile Pythonista/*.py Pythonista/ui/*.py smoke_tests/*.py`
  - `.venv/bin/pytest Pythonista/normalizer_tests.py Pythonista/context_tags_tests.py Pythonista/auto_dictionary_tests.py Pythonista/voice_workflow_tests.py Pythonista/keyboard_model_tests.py -q`
- Device-only smoke tests:
  - `smoke_tests/smoke1_insert.py`
  - `smoke_tests/smoke2_recorder.py`
  - `smoke_tests/smoke3_speech.py`
- Use red/green/refactor where practical. For pure-Python behavior changes, add or tighten tests first.

## Working Rule

If you discover missing context, missing checks, or drift between docs and code, fix the repository so the next agent starts from a better harness.
