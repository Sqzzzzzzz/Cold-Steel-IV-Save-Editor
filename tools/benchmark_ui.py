"""Repeatable Qt timings with a disposable save and an optional read-only catalog.

Run the same script with --source-root pointing at each source snapshot.
Catalogs and results stay local; this tool never opens a player's save.
"""
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import platform
import statistics
import sys
import time


def memory():
    if os.name != 'nt':
        return {}
    from ctypes import wintypes
    class Counters(ctypes.Structure):
        _fields_ = [('cb', wintypes.DWORD), ('PageFaultCount', wintypes.DWORD)] + [
            (key, ctypes.c_size_t) for key in ('PeakWorkingSetSize', 'WorkingSetSize',
            'QuotaPeakPagedPoolUsage', 'QuotaPagedPoolUsage', 'QuotaPeakNonPagedPoolUsage',
            'QuotaNonPagedPoolUsage', 'PagefileUsage', 'PeakPagefileUsage', 'PrivateUsage')]
    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    ctypes.windll.kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    ctypes.windll.psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
    handle = ctypes.windll.kernel32.GetCurrentProcess()
    if not ctypes.windll.psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
        raise ctypes.WinError()
    return {key: round(getattr(counters, field) / 1024**2, 2) for key, field in
            [('working_set_mb', 'WorkingSetSize'), ('private_mb', 'PrivateUsage')]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--catalog-dir', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--repeats', type=int, default=7)
    parser.add_argument('--cycles', type=int, default=30)
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error('--repeats must be positive')
    if args.cycles < 0:
        parser.error('--cycles cannot be negative')
    sys.path.insert(0, str(args.source_root.resolve()))
    from PySide6.QtCore import QPoint,QObject,QCoreApplication,QEvent,qInstallMessageHandler,QtMsgType
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication
    from preview_demo import DemoCore
    from qt_window import MainWindow
    from cs4_save import CS4Save, NON_INVENTORY_ITEM_IDS
    from catalog_core import load_catalog_json
    from unittest.mock import patch

    messages=[]
    def message_handler(kind,context,message):
        if kind in (QtMsgType.QtWarningMsg,QtMsgType.QtCriticalMsg,QtMsgType.QtFatalMsg):
            messages.append(message)
    previous_handler=qInstallMessageHandler(message_handler)
    app = QApplication.instance() or QApplication([])
    app.setStyle('Fusion')
    def events():
        app.processEvents()
        # A manual processEvents loop must also deliver deferred animation cleanup.
        QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete)
    timings = {}
    def measure(name, action):
        samples = []
        for _ in range(args.repeats):
            start = time.perf_counter()
            action()
            events()
            samples.append((time.perf_counter() - start) * 1000)
        timings[name] = {'median_ms': round(statistics.median(samples), 3),
                         'min_ms': round(min(samples), 3), 'max_ms': round(max(samples), 3)}

    start = time.perf_counter()
    core = DemoCore()
    window = None
    try:
        if args.catalog_dir:
            core.base = load_catalog_json(args.catalog_dir / 'catalog_scanned.json')
            core.english = load_catalog_json(args.catalog_dir / 'catalog_english.json')
            core.rebuild_catalog()
        ids = sorted(i for i in core.visible() if i not in NON_INVENTORY_ITEM_IDS)[:900]
        core.save.set_quantities({entry.item_id: 0 for entry in core.save.items()})
        core.save.set_quantities({i: 1 + i % 15 for i in ids})
        core.save = CS4Save(core.save.bytes())
        core.source.write_bytes(core.save.bytes())
        os.utime(core.source, (1700000000, 1700000000))
        with patch.object(MainWindow, 'initial_load', lambda self: None):
            window = MainWindow(core)
        window.show()
        events()
        startup_ms = (time.perf_counter() - start) * 1000
        original = core.save.bytes()
        catalog_digest = hashlib.sha256(json.dumps([core.base, core.english], sort_keys=True,
                                                    ensure_ascii=False).encode()).hexdigest()
        initial_memory = memory()
        initial_objects=len(window.findChildren(QObject))
        measure('refresh_unchanged', window.update_tables)
        measure('categories', window.populate_categories)
        def search():
            needle = 'кварц' if not window.cat_search.text() else ''
            window.cat_search.setText(needle)
            window.search_debounce.stop()
            window.update_tables()
        measure('search', search)
        window.cat_search.clear();window.search_debounce.stop();window.update_tables()
        measure('sort_name', lambda: window.sort_rows('catalog', 0))
        def category():
            window.filter_group = 'quartz' if window.filter_group == 'all' else 'all'
            window.update_tables()
        measure('category_switch', category)
        window.filter_group = 'all';window.update_tables()
        measure('select_details', lambda: window.show_item(ids[-1]))
        scroll_samples = []
        bar = window.cat_table.verticalScrollBar()
        for step in range(40):
            start = time.perf_counter()
            bar.setValue(round(bar.maximum() * (step % 20) / 19))
            events()
            scroll_samples.append((time.perf_counter() - start) * 1000)
        timings['scroll_step'] = {'median_ms': round(statistics.median(scroll_samples), 3),
                                 'max_ms': round(max(scroll_samples), 3)}
        # Exercise warm caches repeatedly and measure retained process memory.
        memory_samples=[]
        for cycle in range(args.cycles):
            search();window.sort_rows('catalog', 0)
            events()
            if (cycle+1)%50==0:
                memory_samples.append({'cycle':cycle+1,**memory(),'qt_objects':len(window.findChildren(QObject))})
        window.cat_search.clear();window.search_debounce.stop()
        window.filter_group = 'quartz_master';window.sort_keys['catalog'] = (1, False)
        window.populate_categories();window.update_tables()
        window.show_item(3228 if 3228 in core.catalog else ids[0])
        bar.setValue(0)
        QTest.mouseMove(window,QPoint(10,10))
        QTest.qWait(250)  # Let the native clear-button fade finish before pixel comparison.
        events()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        window.grab().save(str(args.output.with_suffix('.ru.png')))
        window.lang.setCurrentIndex(1);QTest.qWait(250);events()
        window.grab().save(str(args.output.with_suffix('.en.png')))
        assert core.save.bytes() == original, 'UI operations modified the save'
        result = {'python': platform.python_version(), 'platform': platform.platform(),
                  'qt': __import__('PySide6').__version__, 'repeats': args.repeats,
                  'catalog_count': len(core.visible()), 'inventory_count': len(ids),
                  'catalog_sha256': catalog_digest, 'startup_ms': round(startup_ms, 3),
                  'memory_initial': initial_memory, 'memory_after_cycles': memory(),
                  'cycles':args.cycles,'memory_samples':memory_samples,
                  'qt_objects_initial':initial_objects,'qt_objects_final':len(window.findChildren(QObject)),
                  'icon_cache_entries': len(window._icon_pixmaps),
                  'unique_icons': len({icon.cacheKey() for icon in window._icon_pixmaps.values()}),
                  'timings': timings, 'save_unchanged': True,'qt_warnings':messages}
        args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(result, indent=2))
    finally:
        if window:
            core.reset();window._quantity_user_edited = False
            window.close();window.deleteLater();events()
        core.cleanup()
        qInstallMessageHandler(previous_handler)


if __name__ == '__main__':
    main()
