import farms_positions
from threading import Thread
import sys
import numpy as np
import cv2
from types import MethodType
from time import sleep
from typing import Optional
import typing
from vision import Vision
import QImageViewer
from droid import Droid
from PySide6.QtCore import QObject, Qt, QThread, Signal, QRect
from PySide6.QtGui import QImage, QMouseEvent, QPixmap, QBrush
from PySide6.QtWidgets import (QApplication, QGraphicsScene, QLabel, QGraphicsView, QGraphicsRectItem, QGraphicsSceneMouseEvent,
                               QMainWindow, QWidget, QGraphicsItem, QGraphicsEllipseItem)




class Farm:
    def __init__(self, position=(0, 0), level=1, name=None) -> None:
        self.position = position
        self.level = level
        self.name = name


class WidgetFarmsDisplay(QMainWindow):
    mouse_move_handler = None
    mouse_press_handler = None
    mouse_release_handler = None
    farms_map = None

    def __init__(self, farms: list[Farm]) -> None:
        super().__init__()
        self.map_size = (600, 600)
        self.farms = farms

        self.droid = Droid(Vision('BlueStacks App Player', 1, 34))
        self.droid.vision.start()


        self.setWindowTitle("Farms display")
        self.setGeometry(0, 0, 800, 800)

        self.label_map = QLabel(self)
        self.label_map.mousePressEvent = MethodType(WidgetFarmsDisplay.mousePressEvent_wrapper, self)
        self.label_map.mouseReleaseEvent = MethodType(WidgetFarmsDisplay.mouseReleaseEvent_wrapper, self)
        self.label_map.mouseMoveEvent = MethodType(WidgetFarmsDisplay.mouseMoveEvent_wrapper, self)
        self.label_map.setMouseTracking(True)
        self.label_map.setGeometry(0, 0, self.map_size[0], self.map_size[1])

        self.label_position = QLabel(self)
        self.label_position.setGeometry(605, 5, 195, 15)
        self.label_position.setText("Position: (0, 0)")
        self.update_map()
     
    def mousePressEvent_wrapper(self, event):
        pos = event.position().toTuple()
        world_pos = self.map_to_world(pos)
        self.droid.go_to_location(world_pos)
        if not self.mouse_press_handler is None:
            self.mouse_press_handler(event)
        # return super().mousePressEvent(event)

    def mouseReleaseEvent_wrapper(self, event):
        if not self.mouse_release_handler is None:
            self.mouse_release_handler(event)
        # return super().mouseReleaseEvent(event)

    def mouseMoveEvent_wrapper(self, event: QMouseEvent) -> None:
        pos = event.position().toTuple()
        world_pos = self.map_to_world(pos)
        self.label_position.setText(f"Position: {world_pos}")
        if not self.mouse_move_handler is None:
            self.mouse_move_handler(pos[0], pos[1])
        # return super().mouseMoveEvent(event)

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
            cv2.drawMarker(img,
                           self.world_to_map(farm.position),
                           color=(0, 0, 255),
                           markerType=cv2.MARKER_CROSS,
                           thickness=2, )

        # disegno la mia posizione
        cv2.drawMarker(img,
                       self.world_to_map((364, 541)),
                       color=(0, 255, 0),
                       markerType=cv2.MARKER_CROSS,
                       thickness=2)
        cv2.imwrite('test.png', img)
        # trasformo in QPixMap
        h, w, c = img.shape
        self.farms_map = QImage(img.data, w, h, c * w, QImage.Format.Format_BGR888)
        #height, width, channel = img.shape
        #self.qImg = QImage(img.data, width, height, channel * width, QImage.Format.Format_BGR888)

        self.label_map.setPixmap(QPixmap.fromImageInPlace(self.farms_map))
        self.label_map.repaint()


######################################################################################
def main():
    all_farms = [Farm(fp) for fp in farms_positions.farms]
    for f in farms_positions.dai_figli:
        if not f in farms_positions.farms:
            all_farms.append(Farm(f))
  
    #app = QApplication(sys.argv)
    win = WidgetFarmsDisplay(all_farms)
    win.show()

QImageViewer.invoke(main)

while True:
    sleep(100)
 

