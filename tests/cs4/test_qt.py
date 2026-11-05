import re
from pathlib import Path
from unittest.mock import patch
import pytest
from PySide6.QtCore import Qt,QPoint,QTimer
from PySide6.QtTest import QTest
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication,QAbstractButton,QLabel,QMenu
from qt_window import MainWindow
from qt_backend import EditorCore
from qt_errors import error_text
from preview_demo import synthetic_demo_save


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def window(app,tmp_path,monkeypatch):
    monkeypatch.setenv('APPDATA',str(tmp_path/'profile'))
    core=EditorCore();core.settings['auto_latest']=False
    core.base={20:{'id':20,'name':'Предмет','description':'Описание','category':'consumable','_locale':'ru'},
               60:{'id':60,'name':'Материал','description':'Материал','category':'material','_locale':'ru'}}
    core.english={20:{'id':20,'name':'Item','description':'Description','category':'consumable'},
                  60:{'id':60,'name':'Material','description':'Material','category':'material'}}
    core.rebuild_catalog();source=tmp_path/'save001.dat';source.write_bytes(synthetic_demo_save());core.open_file(source)
    with patch.object(MainWindow,'initial_load',lambda self:None):w=MainWindow(core)
    w.resize(1536,864);w.show();app.processEvents()
    yield w
    core.reset();w._quantity_user_edited=False;w.close();w.deleteLater();app.processEvents()


def test_real_widgets_edit_undo_and_language(window,app):
    w=window;before=w.core.save.bytes();w.show_section('catalog');w.show_item(20)
    w.qty.setValue(7);w.apply_single()
    assert w.core.quantity(20)==7
    w.undo();assert w.core.save.bytes()==before
    w.qty.setValue(25);w.lang.setCurrentIndex(1);app.processEvents()
    assert w.qty.value()==25 and w.core.save.bytes()==before
    assert 'Cold Steel IV' in w.windowTitle() and 'COLD STEEL IV' in w.subtitle.text()
    assert w.item_name.text()=='Item'
    assert w.cat_table.horizontalHeader().sectionsMovable() is False


def test_navigation_sorting_and_search_do_not_modify_save(window,app):
    w=window;before=w.core.save.bytes()
    for section in ('tools','inventory','catalog'):
        w.show_section(section);app.processEvents()
    w.cat_search.setText('Предмет');QTest.qWait(250);app.processEvents()
    assert w.cat_table.rowCount()==1
    w.cat_search.clear();w.cat_table.sortItems(0,Qt.SortOrder.DescendingOrder);app.processEvents()
    assert w.core.save.bytes()==before


def test_table_sorting_is_independent_and_matches_header(window):
    w=window;before=w.core.save.bytes()
    def ids(table):
        return [table.item(row,0).data(Qt.ItemDataRole.UserRole) for row in range(table.rowCount())]
    w.cat_table.horizontalHeader().sectionClicked.emit(1)
    catalog_ids=ids(w.cat_table)
    assert catalog_ids==sorted(catalog_ids,reverse=True)
    w.inv_table.horizontalHeader().sectionClicked.emit(3)
    w.inv_table.horizontalHeader().sectionClicked.emit(3)
    inventory_ids=ids(w.inv_table)
    w.show_section('inventory');w.show_section('catalog')
    assert ids(w.cat_table)==catalog_ids
    assert ids(w.inv_table)==inventory_ids
    assert w.cat_table.horizontalHeader().sortIndicatorOrder()==Qt.SortOrder.DescendingOrder
    assert w.inv_table.horizontalHeader().sortIndicatorOrder()==Qt.SortOrder.DescendingOrder
    w.cat_table.horizontalHeader().sectionClicked.emit(1)
    assert ids(w.cat_table)==sorted(catalog_ids)
    assert ids(w.inv_table)==inventory_ids
    assert w.core.save.bytes()==before


def test_language_keeps_pending_flag_for_default_quantity(window,app):
    w=window
    w.core.base[42]={'id':42,'name':'New item','category':'consumable'}
    w.core.rebuild_catalog();w.update_tables();w.show_item(42)
    before=w.core.save.bytes()
    w.qty.setValue(2);w.qty.setValue(1)
    assert w.has_pending_quantity()
    w.lang.setCurrentIndex(1);app.processEvents()
    assert w.qty.value()==1 and w.has_pending_quantity()
    from qt_changes_dialog import ChangesDialog
    dialog=ChangesDialog(w,'copy')
    assert 'has not been applied' in dialog.note.text()
    dialog.deleteLater()
    assert w.core.save.bytes()==before


def test_quantity_context_menu_opens(window):
    shown=[]
    def choose_quantity():
        menus=window.qty.findChildren(QMenu)
        for menu in menus:
            if menu.isVisible():
                shown.append([x.text() for x in menu.actions()])
                menu.actions()[-1].trigger()
                menu.close()
    QTimer.singleShot(50,choose_quantity)
    window.qty.customContextMenuRequested.emit(QPoint(0,0))
    assert shown==[['1','10','50','99']]
    assert window.qty.value()==99


def test_english_controls_and_crc_error_are_localized(window,app):
    window.lang.setCurrentIndex(1);app.processEvents()
    for obj in window.findChildren(QLabel)+window.findChildren(QAbstractButton)+window.findChildren(QAction):
        if obj in (window.rail_folder,window.save_line):continue
        value=(obj.text() if hasattr(obj,'text') else '')+' '+obj.toolTip()
        assert not re.search('[А-Яа-яЁё]',value),value
    assert 'checksum mismatch' in error_text('Контрольная сумма CS4 не совпадает; файл повреждён или изменён','en')


def test_all_category_icons_have_artwork_instead_of_diamond(window):
    from PySide6.QtWidgets import QTreeWidgetItemIterator
    from qt_hud_widgets import hud_icon
    from categories import CATEGORY_NAMES
    diamond=hud_icon('unknown',25).pixmap(25,25).toImage()
    seen=set()
    for tree in (window.cat_tree,window.inv_tree):
        iterator=QTreeWidgetItemIterator(tree)
        while iterator.value():
            item=iterator.value();seen.add(item.data(0,Qt.ItemDataRole.UserRole))
            assert not item.icon(0).isNull()
            assert item.icon(0).pixmap(25,25).toImage()!=diamond,item.text(0)
            iterator+=1
    assert set(CATEGORY_NAMES)<=seen


def test_master_category_and_items_do_not_use_empty_slot(window):
    from PySide6.QtWidgets import QTreeWidgetItemIterator
    from catalog_core import resource_path
    from PySide6.QtGui import QIcon
    empty=QIcon(str(resource_path('icons/original/Master (Sen III Slot).png'))).pixmap(25,25).toImage()
    iterator=QTreeWidgetItemIterator(window.cat_tree)
    while iterator.value():
        item=iterator.value()
        if item.data(0,Qt.ItemDataRole.UserRole)=='quartz_master':
            assert item.icon(0).pixmap(25,25).toImage()!=empty
            assert item.icon(0).pixmap(25,25).toImage()==window._icon(None,{'category':'quartz_master','name':'Emblem'}).pixmap(25,25).toImage()
            assert window._icon_sources[None].path.name=='Emblem (Sen IV MQ).png'
            assert item.icon(0).pixmap(25,25,QIcon.Mode.Selected).toImage()==item.icon(0).pixmap(25,25,QIcon.Mode.Normal).toImage()
            break
        iterator+=1
    else:pytest.fail('Master category is missing')
    for item_id,name in [(3228,'Эрда'),(3268,'Эрда EX'),(3230,'Воден'),(3270,'Воден EX')]:
        icon=window._icon(item_id,{'category':'quartz_master','name':name})
        rendered=icon.pixmap(90,90).toImage()
        assert not rendered.isNull() and rendered.pixelColor(0,0).alpha()==0
        assert rendered.pixelColor(45,45).alpha()>0
        assert window._icon_sources[item_id].verified


def test_switching_to_english_refreshes_partial_cache(window,app):
    window.core.english={}
    with patch.object(window,'scan_game') as scan:
        window.lang.setCurrentIndex(1);app.processEvents()
        scan.assert_called_once_with(None,silent=True)


def test_idle_refresh_reuses_cells_and_preserves_pending_selection(window):
    from PySide6.QtCore import QItemSelectionModel
    from PySide6.QtTest import QSignalSpy
    w=window;table=w.cat_table
    selection=table.selectionModel()
    flags=QItemSelectionModel.SelectionFlag.Select|QItemSelectionModel.SelectionFlag.Rows
    for row in range(table.rowCount()):selection.select(table.model().index(row,0),flags)
    selection.setCurrentIndex(table.model().index(0,0),QItemSelectionModel.SelectionFlag.NoUpdate)
    w.show_item(20);w.qty.setValue(23)
    cells=[table.item(r,c) for r in range(table.rowCount()) for c in range(4)]
    changed=QSignalSpy(table.model().dataChanged)
    for _ in range(5):w.update_tables()
    assert changed.count()==0
    assert cells==[table.item(r,c) for r in range(table.rowCount()) for c in range(4)]
    assert set(w.selected_ids(table))=={20,60}
    assert table.currentRow()==0 and w.qty.value()==23 and w.has_pending_quantity()


def test_sort_filter_and_language_preserve_selected_ids_and_current(window,app):
    from PySide6.QtCore import QItemSelectionModel
    w=window;table=w.cat_table;sel=table.selectionModel()
    flags=QItemSelectionModel.SelectionFlag.Select|QItemSelectionModel.SelectionFlag.Rows
    for row in range(2):sel.select(table.model().index(row,0),flags)
    sel.setCurrentIndex(table.model().index(0,0),QItemSelectionModel.SelectionFlag.NoUpdate)
    w.show_item(20);w.qty.setValue(23)
    inventory_cells=[w.inv_table.item(r,0) for r in range(w.inv_table.rowCount())]
    for column in (0,1,2,3):
        w.sort_rows('catalog',column)
        assert set(w.selected_ids(table))=={20,60}
        assert table.item(table.currentRow(),0).data(Qt.ItemDataRole.UserRole)==20
    assert inventory_cells==[w.inv_table.item(r,0) for r in range(w.inv_table.rowCount())]
    w.cat_search.setText('Предмет');w.search_debounce.stop();w.update_tables()
    assert w.selected_ids(table)==[20]
    w.cat_search.clear();w.search_debounce.stop();w.update_tables()
    assert w.selected_ids(table)==[20]  # Removed selections do not reappear.
    w.lang.setCurrentIndex(1);app.processEvents()
    assert w.selected_ids(table)==[20] and w.qty.value()==23 and w.has_pending_quantity()


def test_reused_cells_clear_change_markers_after_undo_and_filtering(window):
    w=window;before=w.core.save.bytes()
    w.show_item(20);w.qty.setValue(7);w.apply_single()
    row=next(r for r in range(w.cat_table.rowCount()) if w.cat_table.item(r,0).data(Qt.ItemDataRole.UserRole)==20)
    assert all(w.cat_table.item(row,c).data(Qt.ItemDataRole.UserRole+1) for c in range(4))
    w.undo()
    assert all(w.cat_table.item(row,c).data(Qt.ItemDataRole.UserRole+1) is None for c in range(4))
    w.cat_table.sortItems(0,Qt.SortOrder.DescendingOrder)
    w.cat_search.setText('no match');w.search_debounce.stop();w.update_tables()
    assert w.cat_table.rowCount()==0
    w.cat_search.clear();w.search_debounce.stop();w.update_tables()
    assert w.cat_table.rowCount()==2 and w.core.save.bytes()==before


def test_search_cache_refreshes_after_catalog_and_language_change(window,app):
    w=window
    def search(text):
        w.cat_search.setText(text);w.search_debounce.stop();w.update_tables()
        return w.cat_table.rowCount()
    assert search('Описание')==1
    w.core.base[20]['description']='Новая подсказка'
    w.core.base[20]['name']='Новое название'
    w.core.rebuild_catalog();w.populate_categories()
    assert search('Описание')==0 and search('подсказка')==1
    assert w.cat_table.item(0,0).text()=='Новое название'
    w.core.english={**w.core.english,20:{'name':'Replacement','description':'Updated help'}}
    w.lang.setCurrentIndex(1);app.processEvents()
    assert search('подсказка')==0 and search('updated help')==1
    assert w.cat_table.item(0,0).text()=='Replacement'
    assert len(w._search_details)<=len(w.core.catalog)+w.inv_table.rowCount()


def test_categories_reuse_nodes_and_counts_follow_edits(window):
    from categories import item_in_category
    w=window
    nodes={kind:dict(items) for kind,items in w._category_nodes.items()}
    w.core.change({60:0,65000:1});w.populate_categories();w.update_tables()
    for kind,items in nodes.items():
        assert items==w._category_nodes[kind]
        records=(list(w.core.visible().values()) if kind=='catalog' else
                 [w.core.catalog.get(e.item_id,{'id':e.item_id,'category':'other'}) for e in w.core.save.items()])
        for key,node in items.items():
            if key not in ('favorites','recent'):
                assert int(node.text(1))==sum(item_in_category(record,key) for record in records)
    assert w._category_nodes['inventory']['other'].text(1)!='0'


def test_shared_icons_keep_per_item_provenance_and_refresh(window):
    from original_item_icons import OriginalIcon
    from catalog_core import resource_path
    w=window
    same=resource_path('icons/original/Accessory (Sen III Item).png')
    w._icon_pixmaps.clear();w._artwork_icons.clear()
    with patch('qt_window.original_icon_for_item',side_effect=[OriginalIcon(same,'family',False),OriginalIcon(same,'item',True)]):
        first=w._icon(20,{});second=w._icon(60,{})
    assert first.cacheKey()==second.cacheKey()
    assert w._icon_sources[20].match=='family' and w._icon_sources[60].match=='item'
    w.refresh_catalog()
    assert w._icon_sources[20].path!=same


def test_update_failure_restores_signals_and_painting_and_can_retry(window):
    w=window;w.core.change({20:7})
    with patch.object(w,'_icon',side_effect=RuntimeError('image failure')):
        with pytest.raises(RuntimeError,match='image failure'):w.update_tables()
    assert not w.cat_table.signalsBlocked() and w.cat_table.updatesEnabled()
    w.update_tables()
    row=next(r for r in range(w.cat_table.rowCount()) if w.cat_table.item(r,0).data(Qt.ItemDataRole.UserRole)==20)
    assert w.cat_table.item(row,3).text()=='7'
    w.cat_table.blockSignals(True);w.cat_table.setUpdatesEnabled(False)
    try:
        w.core.change({20:8});w.update_tables()
        assert w.cat_table.signalsBlocked() and not w.cat_table.updatesEnabled()
    finally:
        w.cat_table.blockSignals(False);w.cat_table.setUpdatesEnabled(True)


def test_exclusive_owned_filters_update_once(window):
    w=window;w.present.setChecked(True)
    with patch.object(w,'update_tables',wraps=w.update_tables) as refresh:
        w.missing.setChecked(True)
        assert refresh.call_count==1
    assert w.missing.isChecked() and not w.present.isChecked() and not w.owned_action.isChecked()
    with patch.object(w,'update_tables',wraps=w.update_tables) as refresh:
        w.owned_action.setChecked(True)
        assert refresh.call_count==1
    assert w.present.isChecked() and not w.missing.isChecked()


def test_scan_runs_off_thread_and_applies_on_gui_thread_without_leaking_threads(window,app,tmp_path):
    import time
    from types import SimpleNamespace
    from PySide6.QtCore import QThread,QCoreApplication,QEvent
    w=window;worker_threads=[];apply_threads=[];ticks=[]
    result=SimpleNamespace(root=tmp_path,files=[tmp_path/'t_item_en.tbl'],items=w.core.english,errors=[])
    def scan(root):
        worker_threads.append(QThread.currentThread())
        time.sleep(.06)
        return result
    original_apply=w.core.apply_scan_result
    def apply(value):
        apply_threads.append(QThread.currentThread())
        return original_apply(value)
    timer=QTimer(w);timer.setInterval(5);timer.timeout.connect(lambda:ticks.append(1));timer.start()
    with patch('qt_window.scan_game_tables',side_effect=scan),patch.object(w.core,'apply_scan_result',side_effect=apply):
        for _ in range(3):
            w.scan_game(tmp_path,silent=True)
            deadline=time.monotonic()+5
            while w.scan_thread is not None and time.monotonic()<deadline:QTest.qWait(10)
            assert w.scan_thread is None and w._scan_succeeded
            QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete)
            assert not w.findChildren(QThread)
    timer.stop()
    assert len(worker_threads)==len(apply_threads)==3 and len(ticks)>=3
    assert all(thread!=app.thread() for thread in worker_threads)
    assert all(thread==app.thread() for thread in apply_threads)


def test_scan_worker_snapshots_settings(window):
    from qt_window import ScanWorker
    window.core.settings['game_root']='first'
    worker=ScanWorker(window.core)
    window.core.settings['game_root']='second'
    with patch('qt_window.find_game_install',return_value=None) as find:
        worker.run()
    find.assert_called_once_with('first')


def test_transient_menus_and_review_dialogs_are_deleted(window):
    from PySide6.QtCore import QCoreApplication,QEvent
    from qt_changes_dialog import ChangesDialog
    def close_menu():
        for menu in window.qty.findChildren(QMenu):menu.close()
    def close_review():
        for dialog in window.findChildren(ChangesDialog):dialog.reject()
    for _ in range(8):
        QTimer.singleShot(0,close_menu)
        window.qty.customContextMenuRequested.emit(QPoint(0,0))
        QTimer.singleShot(0,close_review)
        assert not window.show_changes()
        QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete)
        assert not window.qty.findChildren(QMenu)
        assert not window.findChildren(ChangesDialog)


def test_initial_load_is_cancelled_when_window_is_deleted(window):
    from PySide6.QtCore import QCoreApplication,QEvent
    with patch.object(MainWindow,'initial_load') as initial:
        temporary=MainWindow(window.core)
        temporary.close();temporary.deleteLater()
        QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete)
        QTest.qWait(400)
        initial.assert_not_called()
