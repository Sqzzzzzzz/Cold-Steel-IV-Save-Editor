# Changelog / История изменений

## 1.0.0 — 2026-11-05

**English**

- First stable release following the owner's in-game save/load and inventory verification.
- Preserve the interface while reusing table cells, category nodes, localized search text and shared icon resources.
- Fix update-state recovery after exceptions and duplicate ownership-filter refreshes.
- Release closed change-review dialogs and quantity menus; reject malformed JSON character metadata.
- Tie the deferred startup timer to its window to prevent a confirmed shutdown crash.
- Add a checked Windows x64 build, EXE version metadata, bilingual end-user instructions, dependency notices and archive checksums.
- Add Windows CI for Python 3.10/3.14 and verified tag-based GitHub releases.

**Русский**

- Первый стабильный релиз после подтверждённой владельцем проверки загрузки сохранения и предметов в игре.
- Сохранено оформление; повторно используются ячейки, категории, текст поиска и общие ресурсы иконок.
- Исправлены восстановление таблицы после исключения и двойное обновление фильтров наличия.
- Удаляются закрытые окна просмотра правок и меню количества; отклоняются повреждённые метаданные персонажа в JSON.
- Отложенный таймер запуска принадлежит окну: устранён подтверждённый сбой завершения.
- Добавлены проверенная Windows x64-сборка, версия EXE, инструкции RU/EN, сторонние лицензии и контрольные суммы.
- Добавлены Windows CI для Python 3.10/3.14 и проверяемые релизы по тегам.

## 0.1.2-preview — 2026-11-04

**Русский**

- Добавлены 31 исходное изображение мастер-кварцев CS4. Проверены все 62 обычные/EX-записи на обоих языках.
- Вместо пустого слота в категории мастер-кварцев используется игровая «Эмблема»; выделение сохраняет исходные цвета.
- Исправлено восстановление неполного английского кэша при запуске и переключении языка с сохранением русского каталога.
- Добавлены извлечение исходных текстур с проверкой SHA-256 и регрессионные тесты.

**English**

- Added 31 native CS4 master-quartz images; checked all 62 normal/EX entries in both languages.
- Replaced the empty category slot with the native Emblem image and preserved its colors when selected.
- Restore incomplete English caches at startup/language switch while preserving Russian catalog text.
- Added source-texture extraction with SHA-256 verification and regression coverage.

## 0.1.1-preview — 2026-11-04

**Русский**

- Заменены ромбы в категориях, улучшен выбор оружейных иконок и изображений мастер-кварцев.
- Переведены названия и описания 103 стандартных DLC.
- Исправлено чтение двух стоек оружия с одним ID и распознавание материалов в старом кэше.

**English**

- Replaced category diamonds and improved weapon/master artwork selection.
- Added Russian names and descriptions for 103 stock DLC items.
- Fixed shared-ID weapon stances and refreshed material categories in older caches.

## 0.1.0-preview

**Русский**

- Перенос интерфейса CS3 v7.9.7 на формат сохранений и таблицы CS4 NISA PC.
- Оформление «Багровая сталь», каталог, инвентарь, RU/EN, массовые операции, отмена, CSV и резервные копии.
- Изолированный профиль CS4, CRC и проверка границ редактирования.
- Исправлены независимая сортировка таблиц, состояние неприменённого количества и окружение Windows-сборки.

**English**

- Ported the CS3 v7.9.7 interface to CS4 NISA PC saves and item tables.
- Crimson Steel design, inventory/catalog, RU/EN, batch edits, undo, CSV and backups.
- Isolated CS4 profile, CRC and bounded inventory editing.
- Fixed independent table sorting, pending quantity state and Windows build isolation.
