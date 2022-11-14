import sys
import typing
from threading import Thread
from time import sleep
from types import MethodType
from typing import Optional

import cv2
import farms_positions
import numpy as np
import QImageViewer
from droid import Droid
from PySide6.QtCore import QObject, QRect, Qt, QThread, Signal
from PySide6.QtGui import QKeySequence, QAction, QBrush, QImage, QMouseEvent, QPixmap
from PySide6.QtWidgets import (QApplication, QGraphicsEllipseItem,
                               QGraphicsItem, QGraphicsRectItem,
                               QGraphicsScene, QGraphicsSceneMouseEvent,
                               QGraphicsView, QLabel, QMainWindow, QWidget)
from vision import Vision


class Farm:
    def __init__(self, position=(0, 0), level=1, name=None) -> None:
        self.position = position
        self.level = level
        self.name = name


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
    last_selected_farm = None
    def __init__(self, farms: list[Farm]) -> None:
        super().__init__()
        win = self
        self.map_size = (1200, 1200)
        self.farms = farms

        self.droid = Droid(Vision('BlueStacks App Player', 1, 34))
        self.droid.vision.start()

        self.setWindowTitle("Farms display")
        self.setGeometry(0, 0, 800, 800)

        self.scene = QGraphicsScene()
        self.scene.setBackgroundBrush(QBrush(Qt.GlobalColor.black))
        self.scene.setSceneRect(0, 0, self.map_size[0], self.map_size[1])

        self.view = QGraphicsView(self.scene, win)
        self.view.setGeometry(0, 0, 600, 600)
        self.view.setSceneRect(0, 0, self.map_size[0], self.map_size[1])
        self.view.scale(0.48, 0.48)
        self.view.changeEvent = MethodType(WidgetFarmsDisplay.changeEventw, self.view)

        self.label_position = QLabel(self)
        self.label_position.setGeometry(605, 5, 195, 15)
        self.label_position.setText("Position: (0, 0)")
        self.update_map()

        self.action_goto = QAction( )
        self.action_goto.setShortcuts( QKeySequence("Ctrl+G"))
        self.action_goto.setEnabled = True
        self.action_goto.triggered.connect(self.handle_goto)
        self.addAction(self.action_goto)

   
    def handle_goto(self, checked):
        if self.last_selected_farm:
            self.droid.go_to_location(self.last_selected_farm.position)
        print('goto')

    def changeEventw(self, event) -> None:
        # return super().changeEvent(event)
        print(event.__dict__)
        pass

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
                    self.last_selected_farm = sender.farm

            item.onSelectedChanged = handleItemSelectedChanged
            self.scene.addItem(item)
        self.scene.invalidate()

    def set_label_position(self, pos):
        self.label_position.setText(f"Position: {pos}")


######################################################################################
global win


def main():
    all_farms = [Farm(fp) for fp in farms_positions.farms]
    for f in farms_positions.dai_figli:
        if not f in farms_positions.farms:
            all_farms.append(Farm(f))

    #app = QApplication(sys.argv)
    win = WidgetFarmsDisplay(all_farms)
    win.show()
    return win


QImageViewer.invoke(main)

while True:
    sleep(1)
