# ***************************************************************************
# *   Copyright (c) 2021 n1ob <niob@gmx.com>                                *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# ***************************************************************************
from contextlib import contextmanager

import FreeCAD as App
import FreeCADGui as Gui
from PySide2.QtCore import Signal, QObject

from .co_cmn import ObjType
from .co_logger import xp, _ob_a, _ob_g, _ob_s, flow, xps, seq_gen


class EventProvider(QObject):
    add_selection = Signal(object, object, object, object)
    add_selection_ex = Signal(object, object)
    clear_selection = Signal(object)
    doc_recomputed = Signal(object)
    obj_recomputed = Signal(object)
    open_transact = Signal(object, str)
    commit_transact = Signal(object, str)
    in_edit = Signal(object)
    reset_edit = Signal(object)
    undo_doc = Signal(object)


__evo = EventProvider()


# need a single instance
def observer_event_provider_get() -> EventProvider:
    return __evo


@contextmanager
def observer_block():
    observer_event_provider_get().blockSignals(True)
    try:
        yield
    finally:
        observer_event_provider_get().blockSignals(False)


# noinspection PyPep8Naming,PyMethodMayBeStatic
class AppDocumentObserver(object):

    def slotCreatedDocument(self, doc):
        xp(f'{next(AppDocumentObserver.seq):>3}', 'AppDocumentObserver slotCreatedDocument', doc, **_ob_a)

    def slotDeletedDocument(self, doc):
        xp(f'{next(AppDocumentObserver.seq):>3}', 'AppDocumentObserver slotDeletedDocument', doc, **_ob_a)

    def slotRelabelDocument(self, doc):
        xp(f'{next(AppDocumentObserver.seq):>3}', 'AppDocumentObserver slotRelabelDocument', doc, **_ob_a)

    def slotActivateDocument(self, doc):
        xp(f'{next(AppDocumentObserver.seq):>3}', 'AppDocumentObserver slotActivateDocument', doc, **_ob_a)

    def slotRecomputedDocument(self, doc):
        xp(f'{next(AppDocumentObserver.seq):>3}', 'AppDocumentObserver slotRecomputedDocument', doc, **_ob_a)
        doc: App.Document
        xp('TypeId', doc.TypeId, **_ob_a)
        observer_event_provider_get().doc_recomputed.emit(doc)

    def slotUndoDocument(self, doc):
        xp(f'{next(AppDocumentObserver.seq):>3}', 'AppDocumentObserver slotUndoDocument', doc, **_ob_a)
        xp('TypeId', doc.TypeId, **_ob_a)
        if doc.TypeId == 'App::Document':
            doc: App.Document
            xp(f'Objects {doc.Objects}', **_ob_a)
            xp(f'ActiveObject {doc.ActiveObject}', **_ob_a)
            if doc.ActiveObject is None:
                xp('ActiveObject is None')
                return
            if doc.ActiveObject.TypeId == ObjType.SKETCH_OBJECT:
                observer_event_provider_get().undo_doc.emit(doc)

    def slotRedoDocument(self, doc):
        xp(f'{next(AppDocumentObserver.seq):>3}', 'AppDocumentObserver slotRedoDocument', doc, **_ob_a)

    __trans_name = ''

    def slotOpenTransaction(self, doc, name):
        xp(f'{next(AppDocumentObserver.seq):>3}', 'AppDocumentObserver slotOpenTransaction', doc, name, **_ob_a)
        AppDocumentObserver.__trans_name = name
        if name.startswith('Create a new sketch'):
            xp('ignore Create a new sketch', **_ob_a)
            return
        xp('TypeId', doc.TypeId, **_ob_a)
        if doc.TypeId == 'App::Document':
            xp(f'Objects: {doc.Objects} ActiveObject: {doc.ActiveObject}', **_ob_a)
            if doc.ActiveObject and (doc.ActiveObject.TypeId == ObjType.SKETCH_OBJECT):
                observer_event_provider_get().open_transact.emit(doc, name)
                pass

    def slotCommitTransaction(self, doc):
        xp(f'{next(AppDocumentObserver.seq):>3}', 'AppDocumentObserver slotCommitTransaction', doc, **_ob_a)
        name = AppDocumentObserver.__trans_name
        xp('received name:', name)
        if name.startswith('Create a new sketch'):
            xp('ignore Create a new sketch', **_ob_a)
            return
        doc: App.Document
        xp('TypeId', doc.TypeId, **_ob_a)
        if doc.TypeId == 'App::Document':
            xp(f'Objects: {doc.Objects} ActiveObject: {doc.ActiveObject}:{id(doc.ActiveObject)}', **_ob_a)
            if doc.ActiveObject and (doc.ActiveObject.TypeId == ObjType.SKETCH_OBJECT):
                observer_event_provider_get().commit_transact.emit(doc, name)
                pass

    def slotAbortTransaction(self, doc):
        xp(f'{next(AppDocumentObserver.seq):>3}', 'AppDocumentObserver slotAbortTransaction', doc, **_ob_a)

    def slotBeforeChangeDocument(self, doc, prop):
        xp(f'{next(AppDocumentObserver.seq):>3}', 'AppDocumentObserver slotBeforeChangeDocument', doc, prop, **_ob_a)

    def slotChangedDocument(self, doc, prop):
        xp(f'{next(AppDocumentObserver.seq):>3}', 'AppDocumentObserver slotChangedDocument', doc, prop, **_ob_a)

    def slotCreatedObject(self, obj):
        xp(f'{next(AppDocumentObserver.seq):>3}', 'AppDocumentObserver slotCreatedObject', obj, **_ob_a)

    def slotDeletedObject(self, obj):
        xp(f'{next(AppDocumentObserver.seq):>3}', 'AppDocumentObserver slotDeletedObject', obj, **_ob_a)

    def slotChangedObject(self, obj, prop):
        xp(f'{next(AppDocumentObserver.seq):>3}', 'AppDocumentObserver slotChangedObject', obj, prop, **_ob_a)
        # log_some_stuff(obj, prop)

    def slotBeforeChangeObject(self, obj, prop):
        xp(f'{next(AppDocumentObserver.seq):>3}', 'AppDocumentObserver slotBeforeChangeObject', obj, prop, **_ob_a)
        # log_some_stuff(obj, prop)

    def slotRecomputedObject(self, obj):
        xp(f'{next(AppDocumentObserver.seq):>3}', 'AppDocumentObserver slotRecomputedObject', obj, **_ob_a)
        if obj.TypeId == ObjType.SKETCH_OBJECT:
            if 'coed' in obj.PropertiesList:
                xp('own source', obj.getPropertyByName('coed'), **_ob_a)
                obj.removeProperty('coed')
            else:
                observer_event_provider_get().obj_recomputed.emit(obj)

    def slotAppendDynamicProperty(self, obj, prop):
        xp(f'{next(AppDocumentObserver.seq):>3}', 'AppDocumentObserver slotAppendDynamicProperty', obj, prop, **_ob_a)

    def slotRemoveDynamicProperty(self, obj, prop):
        xp(f'{next(AppDocumentObserver.seq):>3}', 'AppDocumentObserver slotRemoveDynamicProperty', obj, prop, **_ob_a)

    def slotChangePropertyEditor(self, obj, prop):
        xp(f'{next(AppDocumentObserver.seq):>3}', 'AppDocumentObserver slotChangePropertyEditor', obj, prop, **_ob_a)

    def slotStartSaveDocument(self, obj, name):
        xp(f'{next(AppDocumentObserver.seq):>3}', 'AppDocumentObserver slotStartSaveDocument', obj, name, **_ob_a)

    def slotFinishSaveDocument(self, obj, name):
        xp(f'{next(AppDocumentObserver.seq):>3}', 'AppDocumentObserver slotFinishSaveDocument', obj, name, **_ob_a)

    def slotBeforeAddingDynamicExtension(self, obj, extension):
        xp(f'{next(AppDocumentObserver.seq):>3}', 'AppDocumentObserver slotBeforeAddingDynamicExtension', obj,
           extension, **_ob_a)

    def slotAddedDynamicExtension(self, obj, extension):
        xp(f'{next(AppDocumentObserver.seq):>3}', 'AppDocumentObserver slotAddedDynamicExtension', obj, extension,
           **_ob_a)

    seq = seq_gen(reset=1000)


# noinspection PyPep8Naming,PyMethodMayBeStatic
class GuiDocumentObserver(object):

    def slotCreatedDocument(self, doc):
        xp(f'{next(GuiDocumentObserver.seq):>3}', 'GuiDocumentObserver slotCreatedDocument', doc, **_ob_g)

    def slotDeletedDocument(self, doc):
        xp(f'{next(GuiDocumentObserver.seq):>3}', 'GuiDocumentObserver slotDeletedDocument', doc, **_ob_g)

    def slotRelabelDocument(self, doc):
        xp(f'{next(GuiDocumentObserver.seq):>3}', 'GuiDocumentObserver slotRelabelDocument', doc, **_ob_g)

    def slotRenameDocument(self, doc):
        xp(f'{next(GuiDocumentObserver.seq):>3}', 'GuiDocumentObserver slotRenameDocument', doc, **_ob_g)

    def slotActivateDocument(self, doc):
        xp(f'{next(GuiDocumentObserver.seq):>3}', 'GuiDocumentObserver slotActivateDocument', doc, **_ob_g)

    def slotCreatedObject(self, obj):
        xp(f'{next(GuiDocumentObserver.seq):>3}', 'GuiDocumentObserver slotCreatedObject', obj, **_ob_g)

    def slotDeletedObject(self, obj):
        xp(f'{next(GuiDocumentObserver.seq):>3}', 'GuiDocumentObserver slotDeletedObject', obj, **_ob_g)

    def slotChangedObject(self, obj, prop):
        xp(f'{next(GuiDocumentObserver.seq):>3}', 'GuiDocumentObserver slotChangedObject', obj, prop, **_ob_g)

    def slotInEdit(self, obj):
        xp(f'{next(GuiDocumentObserver.seq):>3}', 'GuiDocumentObserver slotInEdit', obj, **_ob_g)
        obj: Gui.ViewProvider
        xp(f'slotInEdit {obj.TypeId}')
        xp(f'{obj.Object}')
        if obj.TypeId == ObjType.VIEW_PROVIDER_SKETCH:
            observer_event_provider_get().blockSignals(False)
        observer_event_provider_get().in_edit.emit(obj)

    '''
        if obj.TypeId == 'SketcherGui::ViewProviderSketch':
            ed_info = Gui.ActiveDocument.InEditInfo
            if ed_info is not None:
                if ed_info[0].TypeId == 'Sketcher::SketchObject':
                    if self.sketch is not ed_info[0]:
                        self.base.sketch_set(ed_info[0])
                        self.up_cur_table()
                # self.show()
                self.showNormal()
    '''

    def slotResetEdit(self, obj):
        xp(f'{next(GuiDocumentObserver.seq):>3}', 'GuiDocumentObserver slotResetEdit', obj, **_ob_g)
        obj: Gui.ViewProvider
        xp(f'slotResetEdit {obj.TypeId}')
        xp(f'{obj.Object}')
        observer_event_provider_get().reset_edit.emit(obj)
        if obj.TypeId == ObjType.VIEW_PROVIDER_SKETCH:
            observer_event_provider_get().blockSignals(True)

    seq = seq_gen(reset=1000)


# noinspection PyPep8Naming,PyMethodMayBeStatic
class SelectionObserver:
    # *  The selection consists mainly out of following information per selected object:
    # *  - document (pointer)
    # *  - Object   (pointer)
    # *  - list of subelements (list of strings)
    # *  - 3D coordinates where the user clicks to select (Vector3d)

    @flow
    def addSelection(self, doc, obj, sub, pnt):  # Selection object
        xp(f'{next(SelectionObserver.seq):>3}', 'SelectionObserver addSelection doc:', str(doc), 'obj:', str(obj),
           'sub:', str(sub), 'pnt', str(pnt), **_ob_s)
        if sub == '':
            xp('sub empty, nothing to do')
            return
        sel_ex_lst = Gui.Selection.getSelectionEx()
        for sel_ex in sel_ex_lst:
            xp('  sel_ex:', sel_ex, 'obj:', sel_ex.Object, **_ob_s)
            for sub_name in sel_ex.SubElementNames:
                xp('    sub_name', sub_name, **_ob_s)
            for sub_obj in sel_ex.SubObjects:
                xp('    sub_obj', repr(sub_obj), **_ob_s)
        observer_event_provider_get().add_selection.emit(doc, obj, sub, pnt)
        observer_event_provider_get().add_selection_ex.emit(sel_ex_lst, pnt)

    @flow
    def removeSelection(self, doc, obj, sub):
        xp(f'{next(SelectionObserver.seq):>3}', 'SelectionObserver removeSelection',
           str(doc), 'obj:', str(obj), 'sub:', str(sub), **_ob_s)

    @flow
    def setSelection(self, doc, obj, sub, pnt):
        xp(f'{next(SelectionObserver.seq):>3}', 'SelectionObserver setSelection',
           str(doc), 'obj:', str(obj), 'sub:', str(sub), 'pnt', str(pnt), **_ob_s)

    @flow
    def clearSelection(self, doc):
        xp(f'{next(SelectionObserver.seq):>3}', 'SelectionObserver clearSelection', str(doc), **_ob_s)
        observer_event_provider_get().clear_selection.emit(doc)

    # don't want spam
    # def setPreselection(self, doc, obj, sub):
    #     xp(f'{next(SelectionObserver.seq):>3}', 'SelectionObserver setPreselection',
    #        str(doc), 'obj:', str(obj), 'sub:', str(sub), **_ob_s)

    # def removePreselection(self, doc, obj, sub):
    #     xp(f'{next(SelectionObserver.seq):>3}', 'SelectionObserver removePreselection',
    #        str(doc), 'obj:', str(obj), 'sub:', str(sub), **_ob_s)

    @flow
    def onSelectionChanged(self, doc, obj, sub, pnt):
        xp(f'{next(SelectionObserver.seq):>3}', 'SelectionObserver onSelectionChanged',
           str(doc), 'obj:', str(obj), 'sub:', str(sub), 'pnt', str(pnt), **_ob_s)

    @flow
    def pickedListChanged(self):
        xp(f'{next(SelectionObserver.seq):>3}', 'SelectionObserver pickedListChanged', **_ob_s)

    seq = seq_gen(reset=1000)


__app_document_observer = AppDocumentObserver()
__gui_document_observer = GuiDocumentObserver()
__selection_observer = SelectionObserver()


def register_selection_observer():
    Gui.Selection.addObserver(__selection_observer)


def unregister_selection_observer():
    Gui.Selection.removeObserver(__selection_observer)


def register_gui_document_observer():
    Gui.addDocumentObserver(__gui_document_observer)


def unregister_gui_document_observer():
    Gui.removeDocumentObserver(__gui_document_observer)


def register_app_document_observer():
    App.addDocumentObserver(__app_document_observer)


def unregister_app_document_observer():
    App.removeDocumentObserver(__app_document_observer)


def register():
    register_selection_observer()
    register_gui_document_observer()
    register_app_document_observer()


def unregister():
    unregister_selection_observer()
    unregister_gui_document_observer()
    unregister_app_document_observer()


xps(__name__)
