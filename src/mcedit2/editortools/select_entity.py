"""
    select
"""
from __future__ import absolute_import, division, print_function, unicode_literals
import logging

from PySide import QtGui
from PySide.QtCore import Qt

from mcedit2.editortools import EditorTool
from mcedit2.ui.editortools.select_entity import Ui_selectEntityWidget
from mcedit2.util.bresenham import bresenham


log = logging.getLogger(__name__)


class SelectEntityCommand(QtGui.QUndoCommand):
    def __init__(self, tool, ray, *args, **kwargs):
        QtGui.QUndoCommand.__init__(self, *args, **kwargs)
        self.setText("Inspect Entity")
        self.ray = ray
        self.tool = tool

    def undo(self):
        self.tool.setSelectionRay(self.ray)

    def redo(self):
        self.previousRay = self.tool.selectionRay
        self.tool.setSelectionRay(self.ray)


class SelectEntityToolWidget(QtGui.QWidget, Ui_selectEntityWidget):
    def __init__(self, *args, **kwargs):
        super(SelectEntityToolWidget, self).__init__(*args, **kwargs)
        self.setupUi(self)


class SelectEntityTool(EditorTool):
    name = "Inspect Entity"
    iconName = "edit_entity"
    selectionRay = None
    currentEntity = None
    def __init__(self, editorSession, *args, **kwargs):
        """
        :type editorSession: EditorSession
        """
        super(SelectEntityTool, self).__init__(editorSession, *args, **kwargs)

        self.toolWidget = SelectEntityToolWidget()
        self.toolWidget.tableWidget.cellClicked.connect(self.cellWasClicked)
        self.toolWidget.tableWidget.setColumnCount(2)
        self.toolWidget.tableWidget.setHorizontalHeaderLabels(["ID", "Position"])
        self.selectedEntities = []

    def mousePress(self, event):
        command = SelectEntityCommand(self, event.ray)
        self.editorSession.pushCommand(command)

    def setSelectionRay(self, ray):
        self.selectionRay = ray
        editorSession = self.editorSession
        entities = entitiesOnRay(editorSession.currentDimension, ray)

        tableWidget = self.toolWidget.tableWidget
        tableWidget.clear()
        self.selectedEntities = list(entities)
        if len(self.selectedEntities):
            tableWidget.setRowCount(len(self.selectedEntities))
            for row, e in enumerate(self.selectedEntities):
                pos = e.Position
                flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled
                idItem = QtGui.QTableWidgetItem(e.id)
                idItem.setFlags(flags)
                posItem = QtGui.QTableWidgetItem("%0.2f, %0.2f, %0.2f" % (pos[0], pos[1], pos[2]))
                posItem.setFlags(flags)

                tableWidget.setItem(row, 0, idItem)
                tableWidget.setItem(row, 1, posItem)

            self.cellWasClicked(0, 0)

    def cellWasClicked(self, row, column):
        if len(self.selectedEntities):
            self.currentEntity = self.selectedEntities[row]
            self.editorSession.inspectEntity(self.currentEntity)
        else:
            self.editorSession.inspectEntity(None)

def entitiesOnRay(dimension, ray, rayWidth=0.75, maxDistance = 1000):
    pos, vec = ray

    endpos = pos + vec.normalize() * maxDistance

    ray_dir = vec.normalize()

    # Visit each chunk along the ray
    def chunks(pos, endpos):
        last_cpos = None
        for x, y, z in bresenham(pos, endpos):
            cpos = int(x) >> 4, int(z) >> 4
            if cpos != last_cpos:
                yield cpos
                last_cpos = cpos

    class RaySelection(object):
        positions = list(chunks(pos, endpos))
        def chunkPositions(self):
            return self.positions

        def __contains__(self, position):
            evec = (position + (0.5, 0.5, 0.5)) - pos
            dist = ray_dir.cross(evec).length()
            return dist < rayWidth

    sr = RaySelection()

    return dimension.getEntities(sr)













