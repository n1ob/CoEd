import FreeCADGui as Gui
import FreeCAD as App

from co_logger import xp, _ob_a, _ob_g, _ob_s


class AppDocumentObserver(object):

    def slotCreatedDocument(self, doc):
        xp('AppDocumentObserver slotCreatedDocument', doc, **_ob_a)

    def slotDeletedDocument(self, doc):
        xp('AppDocumentObserver slotDeletedDocument', doc, **_ob_a)

    def slotRelabelDocument(self, doc):
        xp('AppDocumentObserver slotRelabelDocument', doc, **_ob_a)

    def slotActivateDocument(self, doc):
        xp('AppDocumentObserver slotActivateDocument', doc, **_ob_a)

    def slotRecomputedDocument(self, doc):
        xp('AppDocumentObserver slotRecomputedDocument', doc, **_ob_a)

    def slotUndoDocument(self, doc):
        xp('AppDocumentObserver slotUndoDocument', doc, **_ob_a)

    def slotRedoDocument(self, doc):
        xp('AppDocumentObserver slotRedoDocument', doc, **_ob_a)

    def slotOpenTransaction(self, doc, name):
        xp('AppDocumentObserver slotOpenTransaction', doc, name, **_ob_a)

    def slotCommitTransaction(self, doc):
        xp('AppDocumentObserver slotCommitTransaction', doc, **_ob_a)

    def slotAbortTransaction(self, doc):
        xp('AppDocumentObserver slotAbortTransaction', doc, **_ob_a)

    def slotBeforeChangeDocument(self, doc, prop):
        xp('AppDocumentObserver slotBeforeChangeDocument', doc, prop, **_ob_a)

    def slotChangedDocument(self, doc, prop):
        xp('AppDocumentObserver slotChangedDocument', doc, prop, **_ob_a)

    def slotCreatedObject(self, obj):
        xp('AppDocumentObserver slotCreatedObject', obj, **_ob_a)

    def slotDeletedObject(self, obj):
        xp('AppDocumentObserver slotDeletedObject', obj, **_ob_a)

    def slotChangedObject(self, obj, prop):
        xp('AppDocumentObserver slotChangedObject', obj, prop, **_ob_a)

    def slotBeforeChangeObject(self, obj, prop):
        xp('AppDocumentObserver slotBeforeChangeObject', obj, prop, **_ob_a)

    def slotRecomputedObject(self, obj):
        xp('AppDocumentObserver slotRecomputedObject', obj, **_ob_a)

    def slotAppendDynamicProperty(self, obj, prop):
        xp('AppDocumentObserver slotAppendDynamicProperty', obj, prop, **_ob_a)

    def slotRemoveDynamicProperty(self, obj, prop):
        xp('AppDocumentObserver slotRemoveDynamicProperty', obj, prop, **_ob_a)

    def slotChangePropertyEditor(self, obj, prop):
        xp('AppDocumentObserver slotChangePropertyEditor', obj, prop, **_ob_a)

    def slotStartSaveDocument(self, obj, name):
        xp('AppDocumentObserver slotStartSaveDocument', obj, name, **_ob_a)

    def slotFinishSaveDocument(self, obj, name):
        xp('AppDocumentObserver slotFinishSaveDocument', obj, name, **_ob_a)

    def slotBeforeAddingDynamicExtension(self, obj, extension):
        xp('AppDocumentObserver slotBeforeAddingDynamicExtension', obj, extension, **_ob_a)

    def slotAddedDynamicExtension(self, obj, extension):
        xp('AppDocumentObserver slotAddedDynamicExtension', obj, extension, **_ob_a)


__app_document_observer = AppDocumentObserver()


class GuiDocumentObserver(object):

    def slotCreatedDocumen(self, doc):
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

    def addSelection(self, doc, obj, sub, pnt):  # Selection object
        xp('SelectionObserver addSelection doc:', str(doc), 'obj:', str(obj), 'sub:', str(sub), 'pnt', str(pnt), **_ob_s)

        for sel_ex in Gui.Selection.getSelectionEx():
            xp('sel_ex:', sel_ex, 'obj:', sel_ex.Object)
            for sub_name in sel_ex.SubElementNames:
                xp('  sub_name', sub_name)
            for sub_obj in sel_ex.SubObjects:
                xp('  sub_obj', sub_obj)

    def removeSelection(self, doc, obj, sub):
        xp('SelectionObserver removeSelection',
           str(doc), 'obj:', str(obj), 'sub:', str(sub), **_ob_s)

    # 15:36:19  C:\Users\red\PycharmProjects\FreeCad\test_co.py(154)<class 'TypeError'>: removeSelection() missing 1 required positional argument: 'pnt'
    # def removeSelection(self, doc, obj, sub, pnt):
    #     xp('SelectionObserver removeSelection',
    #        str(doc), 'obj:', str(obj), 'sub:', str(sub), 'pnt', str(pnt), **_ob_s)

    def setSelection(self, doc, obj, sub, pnt):
        xp('SelectionObserver setSelection',
           str(doc), 'obj:', str(obj), 'sub:', str(sub), 'pnt', str(pnt), **_ob_s)

    def clearSelection(self, doc):
        xp('SelectionObserver clearSelection',
           str(doc))

    # 15:15:52  C:\Users\red\PycharmProjects\FreeCad\test_co.py(154)<class 'TypeError'>: clearSelection() missing 3 required positional arguments: 'obj', 'sub', and 'pnt'
    # def clearSelection(self, doc, obj, sub, pnt):
    #     xp('SelectionObserver clearSelection',
    #        str(doc), 'obj:', str(obj), 'sub:', str(sub), 'pnt', str(pnt), **_ob_s)

    def setPreselection(self, doc, obj, sub):
        xp('SelectionObserver setPreselection',
           str(doc), 'obj:', str(obj), 'sub:', str(sub), **_ob_s)
    # def setPreselection(self, doc, obj, sub, pnt):
    #     xp('SelectionObserver setPreselection', str(doc), 'obj:', str(obj), 'sub:', str(sub), 'pnt', str(pnt))

    def removePreselection(self, doc, obj, sub):
        xp('SelectionObserver removePreselection',
           str(doc), 'obj:', str(obj), 'sub:', str(sub), **_ob_s)
    # def removePreselection(self, doc, obj, sub, pnt):
    #     xp('SelectionObserver removePreselection', str(doc), 'obj:', str(obj), 'sub:', str(sub), 'pnt', str(pnt))

    def onSelectionChanged(self, doc, obj, sub, pnt):
        xp('SelectionObserver onSelectionChanged',
           str(doc), 'obj:', str(obj), 'sub:', str(sub), 'pnt', str(pnt), **_ob_s)

    def pickedListChanged(self):
        xp('SelectionObserver pickedListChanged')


__selection_observer = SelectionObserver()


def register():
    Gui.Selection.addObserver(__selection_observer)
    App.addDocumentObserver(__app_document_observer)
    Gui.addDocumentObserver(__gui_document_observer)


def unregister():
    Gui.Selection.removeObserver(__selection_observer)
    App.removeDocumentObserver(__app_document_observer)
    Gui.removeDocumentObserver(__gui_document_observer)
