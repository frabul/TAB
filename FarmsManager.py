import sys
import typing
from threading import Thread
from time import sleep
from types import MethodType
from typing import Optional

import cv2
import numpy as np
from PySide6.QtCore import QObject, QRect, Qt, QThread, Signal,QTimer
from PySide6.QtGui import (QAction, QBrush, QImage, QKeySequence, QMouseEvent, QShortcut, QClipboard, 
                           QPixmap)
from PySide6.QtWidgets import (QApplication, QGraphicsEllipseItem,
                               QGraphicsItem, QGraphicsRectItem, 
                               QGraphicsScene, QGraphicsSceneMouseEvent,
                               QGraphicsView, QLabel, QMainWindow, QWidget,
                               QGridLayout, QPushButton, QVBoxLayout, QSizePolicy, QLineEdit, QHBoxLayout,
                               
                               )

import farms_positions
import QImageViewer
from droid import Droid
from vision import Vision
from FarmsDb import Farm, FarmsDb


class FarmMarker(QGraphicsEllipseItem):

    def setBrushes(self, selected, unselected):
        self.selectedBrush = selected
        self.unselectedBrush = unselected
        self.setBrush(self.unselectedBrush)

    @staticmethod
    def onSelectedChanged(sender, isSelected):
        pass

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            if value == True:
                self.setBrush(self.selectedBrush)
            else:
                self.setBrush(self.unselectedBrush)
            self.onSelectedChanged(self, value)
        return super().itemChange(change, value)


class WidgetFarmsDisplay(QMainWindow):
    mouse_move_handler = None
    mouse_press_handler = None
    mouse_release_handler = None
    farms_map = None
    last_selected_farm: QWidget = None

    def __init__(self) -> None:
        super().__init__()
        win = self
        self.map_size = (1200, 1200)
        self.farm_widgets: dict[tuple, QWidget] = {}
        self.droid = Droid(Vision('BlueStacks App Player', 1, 34))
        self.farms = FarmsDb('FarmsDb.json')
        self.droid.vision.start()

        self.setWindowTitle("Farms display")
        self.setGeometry(0, 0, 800, 800)

        # scene
        self.scene = QGraphicsScene()
        self.scene.setBackgroundBrush(QBrush(Qt.GlobalColor.black))
        self.scene.setSceneRect(0, 0, self.map_size[0], self.map_size[1])
        self.scene.mouseDoubleClickEvent = MethodType(WidgetFarmsDisplay.handle_mouse_double_click_on_scene, self)
        self.scene.mouseMoveEvent = MethodType(WidgetFarmsDisplay.handle_mouse_move_on_scene, self)

        # my marker
        self.my_marker = QGraphicsEllipseItem(QRect(0, 0, 20, 20))
        self.my_marker.setBrush(QBrush(Qt.GlobalColor.green))
        self.my_marker.hide()
        self.scene.addItem(self.my_marker)

        # view
        self.view = QGraphicsView(self.scene, win)
        self.view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.view.setGeometry(0, 0, 600, 600)
        self.view.setSceneRect(0, 0, self.map_size[0], self.map_size[1])
        self.view.scale(0.48, 0.48)
        self.view.setMouseTracking(True)

        widget = QWidget(self)
        self.side_gui = QVBoxLayout()
        # self.layout().addChildLayout(self.side_gui)

        fixedPolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        # label_cursor
        self.label_cursor = QLabel()
        self.label_cursor.setText("Cursor: (0, 0)")
        self.label_cursor.setSizePolicy(fixedPolicy)
        self.side_gui.addWidget(self.label_cursor)

        # label_position
        self.label_position = QLabel()
        self.label_position.setText("Last Selected: (0, 0)")
        self.label_position.setSizePolicy(fixedPolicy)
        self.side_gui.addWidget(self.label_position)

        # button_show_all
        self.button_show_all = QPushButton(text="Show All")
        self.button_show_all.clicked.connect(self.handle_show_all)
        self.side_gui.addWidget(self.button_show_all)

        # button_add and fields
        horiz = QHBoxLayout()
        self.side_gui.addLayout(horiz)
        self.ledit_x = QLineEdit('0')
        horiz.addWidget(QLabel('X:'))
        horiz.addWidget(self.ledit_x)
        self.ledit_y = QLineEdit('0')
        horiz.addWidget(QLabel('Y:'))
        horiz.addWidget(self.ledit_y)

        # button_add
        self.button_add = QPushButton(text='Add')
        self.button_add.clicked.connect(self.handle_add)
        self.side_gui.addWidget(self.button_add)

        # button remove
        self.button_remove = QPushButton(text='Remove')
        self.button_remove.clicked.connect(self.handle_remove)
        self.side_gui.addWidget(self.button_remove)
        # filler
        filler = QWidget()
        filler.sizePolicy().setVerticalStretch(1)
        self.side_gui.addWidget(filler)

        widget.setGeometry(QRect(605, 5, 200, 800))
        widget.setLayout(self.side_gui)

        self.action_goto = QAction()
        self.action_goto.setShortcuts(QKeySequence("Ctrl+G"))
        self.action_goto.setEnabled(True)
        self.action_goto.triggered.connect(self.handle_goto)
        self.addAction(self.action_goto)

        self.action_goto = QShortcut(QKeySequence("Ctrl+C"), self)
        self.action_goto.setEnabled(True)
        self.action_goto.activated.connect(self.handle_ctrl_c)
        # self.addAction(self.action_goto)

        self.update_map()

    def closeEvent(self, event ) -> None:
        exit()
        return super().closeEvent(event)

    def handle_mouse_double_click_on_scene(self, event: QGraphicsSceneMouseEvent):
        self.my_marker.setPos(event.scenePos().toPoint())
        self.my_marker.show()

    def handle_mouse_move_on_scene(self, event: QGraphicsSceneMouseEvent):
        self.label_cursor.setText(f"Cursor: {event.scenePos().toPoint().toTuple()}")

    def handle_add(self):
        try:
            x = int(self.ledit_x.text())
            y = int(self.ledit_y.text())
            self.farms.add_farm(Farm((x, y)))
            self.update_map()
            self.farms.save()
        except:
            pass
       

    def handle_remove(self):
        changed = False
        try:
            for it in self.scene.selectedItems():
                if type(it) is FarmMarker:
                    popped = self.farms.remove_farm(it.farm.position)
                    if not popped:
                        print('not popped')
                    self.scene.removeItem(it)
                    changed = True
                    it.hide()
        except:
            pass 
        if changed:
            self.farms.save()

    def handle_ctrl_c(self):
        positions = []
        for it in self.scene.selectedItems():
            if type(it) is FarmMarker:
                positions.append(it.farm.position)
        clipboard = QApplication.clipboard()
        clipboard.setText(str(positions)[1:-1])

    def handle_show_all(self, checked):
        for it in self.farm_widgets.values:
            it.show()

    def handle_goto(self, checked):
        if self.last_selected_farm:
            self.droid.go_to_location(self.last_selected_farm.farm.position)
            self.last_selected_farm.hide()

    def world_to_map(self, pos):
        mw, mh = self.map_size
        x = (1200 - pos[0]) * mw // 1200
        y = pos[1] * mh // 1200
        return (x, y)

    def map_to_world(self, pos):
        mw, mh = self.map_size
        x, y = pos
        fx = 1200 - x * 1200 / mw
        fy = y * 1200 / mh
        return (int(fx), int(fy))

    def update_map(self) -> QImage:
        mw, mh = self.map_size
        img = np.zeros((mh, mw, 3), dtype=np.uint8)

        for it in self.farm_widgets.values():
            self.scene.removeItem(it)
        self.farm_widgets.clear()
       
        for farm in self.farms:
            x, y = self.world_to_map(farm.position)
            item = FarmMarker(QRect(x, y, 20, 20))
            item.setBrushes(
                QBrush(Qt.GlobalColor.blue),
                QBrush(Qt.GlobalColor.red)
            )
            item.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
            item.farm = farm

            def handleItemSelectedChanged(sender, val):
                if val:
                    self.set_label_position(sender.farm.position)
                    self.last_selected_farm = sender

            item.onSelectedChanged = handleItemSelectedChanged
            self.scene.addItem(item)
            self.farm_widgets[farm.position] = item

        self.scene.invalidate()

    def set_label_position(self, pos):
        self.label_position.setText(f"Last selected: {pos}")


######################################################################################
global win


def main():
    win = WidgetFarmsDisplay()
    win.show()
    return win


QImageViewer.invoke(main)
