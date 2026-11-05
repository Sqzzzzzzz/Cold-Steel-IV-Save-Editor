# Contributing / Участие в разработке

Small, focused fixes are welcome. Describe the observable problem, preserve the established interface, and include a regression test for nontrivial behavior. Discuss changes to save layouts or editing limits before implementation.

Приветствуются небольшие исправления с описанием воспроизводимой ошибки. Сохраняйте интерфейс и добавляйте регрессионные тесты для существенной логики. Изменения формата сохранений и ограничений редактирования сначала обсудите в issue.

## Development

Use x64 Python 3.10–3.14. Build releases with Python 3.14 on Windows:

```powershell
py -3.14 -m venv .qt-preview-venv
.\.qt-preview-venv\Scripts\python.exe -m pip install -r requirements-release.txt
.\.qt-preview-venv\Scripts\python.exe -m pytest -q
.\.qt-preview-venv\Scripts\python.exe tools\build_release.py
```

Tests use synthetic data and temporary profiles. `CS4_REFERENCE_SAVE` optionally points to a private reference fixture with the documented expected inventory; do not commit it. A skipped optional fixture test does not validate a new game edition.

Тесты используют искусственные данные и временные профили. Не добавляйте реальные сохранения, игровые таблицы, каталоги профиля, токены, окружения и результаты сборки. Для новых игровых форматов отдельно требуется проверка в игре на резервной копии.

## Pull requests

- Explain the trigger, resulting behavior and tests actually run.
- Keep names, translations, icon provenance, file protections and undo behavior intact.
- Use synthetic reproduction data; never attach personal saves or game archives publicly.
- Preserve existing copyright and license notices. Dependency/artwork rights differ from the project's MIT license.

## Maintainer release procedure

1. Update `app_info.VERSION` and `VERSION.txt` together; use `MAJOR.MINOR.PATCH`.
2. Add English `docs/releases/vVERSION.md` notes, update both READMEs and changelog.
3. Run local checks and the checked build. Confirm in-game compatibility for any save-engine change.
4. Commit and push; wait for Windows checks on `main`.
5. Create a new `vVERSION` tag at the reviewed commit and push it. Never reuse a published version.
6. The tag workflow tests, builds and verifies the ZIP, creates a draft with exactly the ZIP and checksum, verifies the uploaded checksum, then publishes it.

If publishing fails, inspect the failed job and any existing draft before retrying. The workflow refuses to overwrite an existing release. Repair deliberately; do not bypass failed tests or move a published tag.

GitHub Actions uses pinned official actions and a read-only token for test/build jobs. Only the tag publishing job receives `contents: write`; pull requests never receive that permission.
