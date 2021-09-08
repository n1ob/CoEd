from typing import Set

import FreeCADGui as Gui
import FreeCAD as App
import Part

from co_cmn import fmt_vec, seq_gen
from co_flag import ObserverEvent
from co_logger import xp, _ob_a, _ob_g, _ob_s, flow, xps


def log_some_stuff(obj, prop):
    if obj.TypeId == 'Sketcher::SketchObject':
        if prop == 'Geometry':
            xps('Geometry', **_ob_a)
            for idx, item in enumerate(obj.Geometry):
                if item.TypeId == 'Part::GeomLineSegment':
                    line: Part.LineSegment = item
                    xp('idx:', idx, 'type_id:', item.TypeId, 'start:',
                       fmt_vec(App.Vector(line.StartPoint)), 'end:', fmt_vec(App.Vector(line.EndPoint)), **_ob_a)
                elif item.TypeId == 'Part::GeomCircle':
                    cir: Part.Circle = item
                    xp(f'idx: {idx} type_id: {cir.TypeId} center: {fmt_vec(App.Vector(cir.Center))} '
                       f'radius: {cir.Radius}', **_ob_a)
                else:
                    xp('idx:', idx, 'type_id:', item.TypeId, 'item:', item, **_ob_a)
        if prop == 'Constraints':
            xps('Constraints', **_ob_a)
            for idx, item in enumerate(obj.Constraints):
                xp('idx:', idx, 'type_id:', item.TypeId, 'item:', item, **_ob_a)
        if prop == 'FullyConstrained':
            xps('FullyConstrained', **_ob_a)
            xp('bool:', obj.FullyConstrained, **_ob_a)
        if prop == 'Shape':
            xps('Shape', **_ob_a)
            xp(obj.Shape, **_ob_a)


class EventProvider:
    ev = ObserverEvent()


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
        EventProvider.ev.doc_recomputed.emit(doc)

    # |35 AppDocumentObserver slotRecomputedDocument <Document object at 0000024EF043D020>

    def slotUndoDocument(self, doc):
        xp(f'{next(AppDocumentObserver.seq):>3}', 'AppDocumentObserver slotUndoDocument', doc, **_ob_a)

    def slotRedoDocument(self, doc):
        xp(f'{next(AppDocumentObserver.seq):>3}', 'AppDocumentObserver slotRedoDocument', doc, **_ob_a)

    def slotOpenTransaction(self, doc, name):
        xp(f'{next(AppDocumentObserver.seq):>3}', 'AppDocumentObserver slotOpenTransaction', doc, name, **_ob_a)
        xp('TypeId', doc.TypeId, **_ob_a)
        if doc.TypeId == 'App::Document':
            doc: App.Document
            xp(f'Objects {doc.Objects}')
            xp(f'ActiveObject {doc.ActiveObject}')
            if doc.ActiveObject.TypeId == 'Sketcher::SketchObject':
                EventProvider.ev.open_transact.emit(doc, name)


    # | ActiveObject <Sketcher::SketchObject>
    # | Objects [<Sketcher::SketchObject>]

    # |   2 AppDocumentObserver slotOpenTransaction <Document object at 0000024EF043D020> Delete sketch geometry
    # |   2 AppDocumentObserver slotOpenTransaction <Document object at 0000027808F67E40> Drag Curve
    # |   2 AppDocumentObserver slotOpenTransaction <Document object at 00000240DEE24840> Drag Point
    # |   2 AppDocumentObserver slotOpenTransaction <Document object at 0000016F22E3FC90> Add sketch line
    # |   2 AppDocumentObserver slotOpenTransaction <Document object at 0000022F48C6E920> Add line to sketch wire
    # |  24 AppDocumentObserver slotOpenTransaction <Document object at 0000024EF043D020> Sketch recompute

    def slotCommitTransaction(self, doc):
        xp(f'{next(AppDocumentObserver.seq):>3}', 'AppDocumentObserver slotCommitTransaction', doc, **_ob_a)
        doc: App.Document
        xp(doc.TypeId)

    # |21 AppDocumentObserver slotCommitTransaction <Document object at 0000024EF043D020>
    # |36 AppDocumentObserver slotCommitTransaction <Document object at 0000024EF043D020>

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
        if obj.TypeId == 'Sketcher::SketchObject':
            if 'coed' in obj.PropertiesList:
                xp('own source', obj.getPropertyByName('coed'), **_ob_a)
                obj.removeProperty('coed')
            else:
                EventProvider.ev.obj_recomputed.emit(obj)

    # |34 AppDocumentObserver slotRecomputedObject <Sketcher::SketchObject>

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

    seq = seq_gen()


__app_document_observer = AppDocumentObserver()


class GuiDocumentObserver(object):

    def slotCreatedDocument(self, doc):
        xp('GuiDocumentObserver slotCreatedDocument', doc, **_ob_g)

    def slotDeletedDocument(self, doc):
        xp('GuiDocumentObserver slotDeletedDocument', doc, **_ob_g)

    def slotRelabelDocument(self, doc):
        xp('GuiDocumentObserver slotRelabelDocument', doc, **_ob_g)

    def slotRenameDocument(self, doc):
        xp('GuiDocumentObserver slotRenameDocument', doc, **_ob_g)

    def slotActivateDocument(self, doc):
        xp('GuiDocumentObserver slotActivateDocument', doc, **_ob_g)

    def slotCreatedObject(self, obj):
        xp('GuiDocumentObserver slotCreatedObject', obj, **_ob_g)

    def slotDeletedObject(self, obj):
        xp('GuiDocumentObserver slotDeletedObject', obj, **_ob_g)

    def slotChangedObject(self, obj, prop):
        xp('GuiDocumentObserver slotChangedObject', obj, prop, **_ob_g)

    def slotInEdit(self, obj):
        xp('GuiDocumentObserver slotInEdit', obj, **_ob_g)

    def slotResetEdit(self, obj):
        xp('GuiDocumentObserver slotResetEdit', obj, **_ob_g)


__gui_document_observer = GuiDocumentObserver()


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

        for sel_ex in Gui.Selection.getSelectionEx():
            xp('  sel_ex:', sel_ex, 'obj:', sel_ex.Object, **_ob_s)
            for sub_name in sel_ex.SubElementNames:
                xp('    sub_name', sub_name, **_ob_s)
            for sub_obj in sel_ex.SubObjects:
                xp('    sub_obj', repr(sub_obj), **_ob_s)

        EventProvider.ev.add_selection.emit(doc, obj, sub, pnt)

    @flow
    def removeSelection(self, doc, obj, sub):
        xp(f'{next(SelectionObserver.seq):>3}', 'SelectionObserver removeSelection',
           str(doc), 'obj:', str(obj), 'sub:', str(sub), **_ob_s)

    # 15:36:19  C:\Users\red\PycharmProjects\FreeCad\test_co.py(154)<class 'TypeError'>: removeSelection() missing 1 required positional argument: 'pnt'
    # def removeSelection(self, doc, obj, sub, pnt):

    @flow
    def setSelection(self, doc, obj, sub, pnt):
        xp(f'{next(SelectionObserver.seq):>3}', 'SelectionObserver setSelection',
           str(doc), 'obj:', str(obj), 'sub:', str(sub), 'pnt', str(pnt), **_ob_s)

    @flow
    def clearSelection(self, doc):
        xp(f'{next(SelectionObserver.seq):>3}', 'SelectionObserver clearSelection',
           str(doc), **_ob_s)

    # 15:15:52  C:\Users\red\PycharmProjects\FreeCad\test_co.py(154)<class 'TypeError'>: clearSelection() missing 3 required positional arguments: 'obj', 'sub', and 'pnt'
    # def clearSelection(self, doc, obj, sub, pnt):

    # def setPreselection(self, doc, obj, sub):
    #     xp(f'{next(SelectionObserver.seq):>3}', 'SelectionObserver setPreselection',
    #        str(doc), 'obj:', str(obj), 'sub:', str(sub), **_ob_s)

    # def setPreselection(self, doc, obj, sub, pnt):

    # def removePreselection(self, doc, obj, sub):
    #     xp(f'{next(SelectionObserver.seq):>3}', 'SelectionObserver removePreselection',
    #        str(doc), 'obj:', str(obj), 'sub:', str(sub), **_ob_s)

    # def removePreselection(self, doc, obj, sub, pnt):

    @flow
    def onSelectionChanged(self, doc, obj, sub, pnt):
        xp(f'{next(SelectionObserver.seq):>3}', 'SelectionObserver onSelectionChanged',
           str(doc), 'obj:', str(obj), 'sub:', str(sub), 'pnt', str(pnt), **_ob_s)

    @flow
    def pickedListChanged(self):
        xp(f'{next(SelectionObserver.seq):>3}', 'SelectionObserver pickedListChanged', **_ob_s)

    seq = seq_gen()


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
    # register_gui_document_observer()
    register_app_document_observer()


def unregister():
    unregister_selection_observer()
    # unregister_gui_document_observer()
    unregister_app_document_observer()
