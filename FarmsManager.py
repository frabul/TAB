import QDispatcher
QDispatcher.create(True)  

from types import MethodType 
import numpy as np
from PySide6.QtCore import QObject, QRect, Qt, QThread, Signal,QTimer 
from PySide6.QtGui import (QAction, QBrush, QImage, QKeySequence, QMouseEvent, QShortcut, QClipboard, 
                           QPixmap)
from PySide6.QtWidgets import (QApplication, QGraphicsEllipseItem,
                               QGraphicsItem, QGraphicsRectItem, 
                               QGraphicsScene, QGraphicsSceneMouseEvent,
                               QGraphicsView, QLabel, QMainWindow, QWidget,
                               QGridLayout, QPushButton, QVBoxLayout, QSizePolicy, QLineEdit, QHBoxLayout,QSlider
                               )
from droid import Droid
from vision import Vision
from FarmsDb import Farm, FarmsDb
import utils

class FarmMarker(QGraphicsEllipseItem):
    def __init__( self, farm:Farm, pos_in_map) -> None: 
        super().__init__( )
        self.set_position(pos_in_map)
        self.farm : Farm = farm
        self.set_explored(False)
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)

    def set_position(self, pos_in_map):
        rect = QRect(pos_in_map[0] - 8, pos_in_map[1] - 8, 16, 16)
        self.setRect(rect)

    def _setBrushes(self, selected, unselected):
        self.selectedBrush = selected
        self.unselectedBrush = unselected
        if self.isSelected():
            self.setBrush(self.selectedBrush)
        else:
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

    def set_explored(self, was_explored: bool):
        if was_explored:
            self._setBrushes( 
                    QBrush(Qt.GlobalColor.blue),
                    QBrush(Qt.GlobalColor.cyan) 
                )
        else:
            self._setBrushes( 
                    QBrush(Qt.GlobalColor.blue),
                    QBrush(Qt.GlobalColor.red) 
                )

class FixedSizeLabel(QLabel):
    fixedPolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    def __init__(self, txt = None, parent =None  ):
        super().__init__( )
        self.setText(txt)
        self.setSizePolicy(self.fixedPolicy)

class WidgetFarmsDisplay(QMainWindow):
    mouse_move_handler = None
    mouse_press_handler = None
    mouse_release_handler = None
    farms_map = None
    last_selected_marker: FarmMarker = None
    fixedPolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)


    def __init__(self, farmsdb) -> None: 
        super().__init__()
        win = self
        self.map_size = (1200, 1200)
        self.farm_widgets: dict[tuple, FarmMarker] = {}
        self.droid = Droid(Vision('BlueStacks App Player', (1, 35, 1, 1))) 
        self.farms = farmsdb
        self.droid.vision.start()

        self.setWindowTitle("Farms display")
        self.setGeometry(0, 0, 800, 800)
        
        # scene
        self.scene = QGraphicsScene()
        self.scene.setBackgroundBrush(QBrush(Qt.GlobalColor.black))
        self.scene.setSceneRect(-5, -5, self.map_size[0] + 10, self.map_size[1]+10)
        self.scene.mouseDoubleClickEvent = MethodType(WidgetFarmsDisplay.handle_mouse_double_click_on_scene, self)
        self.scene.mouseMoveEvent = MethodType(WidgetFarmsDisplay.handle_mouse_move_on_scene, self)
        self.scene.selectionChanged.connect(self.handle_scene_selectionChanged)

        # my marker
        self.my_position = (600,600)
        self.my_marker = FarmMarker(Farm(self.my_position, name='Me'), self.world_to_map(self.my_position))
        self.my_marker.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.my_marker._setBrushes(QBrush(Qt.GlobalColor.green),QBrush(Qt.GlobalColor.green))
        self.scene.addItem(self.my_marker)

        # view
        self.view = QGraphicsView(self.scene, win)
        self.view.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.view.setContentsMargins(0,0,0,0)
        self.view.setGeometry(0, 0, self.scene.width()/2 + 2 , self.scene.height()/2 + 2 ) 
        self.view.setSceneRect(self.scene.sceneRect())
        self.view.scale(0.5, 0.5)
        self.view.setMouseTracking(True)

        # layout 
        widget = QWidget(self)
        self.side_gui = QVBoxLayout() 

        # label_cursor
        self.label_cursor = FixedSizeLabel("Cursor: (0, 0)") 
        self.side_gui.addWidget(self.label_cursor)

        # label_farms_selected
        self.label_farms_selected = FixedSizeLabel('Farms selected: 0')
        self.side_gui.addWidget(self.label_farms_selected)

        # label_last_selected
        self.label_last_selected = FixedSizeLabel("Last Selected: (0, 0)") 
        self.side_gui.addWidget(self.label_last_selected)

        # button_attack_selected
        self.button_attack_selected = QPushButton(text="Attack selected")
        self.button_attack_selected.clicked.connect(self.handle_attack_selected)
        self.side_gui.addWidget(self.button_attack_selected)

        # button_refresh_info
        self.button_refresh_info = QPushButton(text="Refresh info on selected")
        self.button_refresh_info.clicked.connect(self.handle_refresh_info)
        self.side_gui.addWidget(self.button_refresh_info)

        # button_unmark
        self.button_unmark_explored = QPushButton(text="Unmark explored")
        self.button_unmark_explored.clicked.connect(self.handle_unmark_explored)
        self.side_gui.addWidget(self.button_unmark_explored)

        # button mark explored
        self.button_mark_explored = QPushButton(text='Mark Explored')
        self.button_mark_explored.clicked.connect(self.handle_mark_explored)
        self.side_gui.addWidget(self.button_mark_explored)
         
        # X Y to add
        horiz = QHBoxLayout()
        self.side_gui.addLayout(horiz)
        self.ledit_x = QLineEdit('0')
        horiz.addWidget(FixedSizeLabel('X:'))
        horiz.addWidget(self.ledit_x)
        self.ledit_y = QLineEdit('0')
        horiz.addWidget(FixedSizeLabel('Y:'))
        horiz.addWidget(self.ledit_y)
         
        # button_add
        self.button_add = QPushButton(text='Add')
        self.button_add.clicked.connect(self.handle_add)
        self.side_gui.addWidget(self.button_add)

        # button remove
        self.button_remove = QPushButton(text='Remove')
        self.button_remove.clicked.connect(self.handle_remove)
        self.side_gui.addWidget(self.button_remove)

        # filter by level   
        self.slider_filter_level = QSlider(Qt.Orientation.Horizontal) 
        self.slider_filter_level.label = FixedSizeLabel()
        self.slider_filter_level.valueChanged.connect(self.handle_filters_change)
        self.slider_filter_level.setRange(-1,25)
        self.slider_filter_level.setValue(-1) 
        self.side_gui.addWidget(self.slider_filter_level.label)
        self.side_gui.addWidget(self.slider_filter_level)
        

        # filter by distance
        self.slider_filter_distance = QSlider(Qt.Orientation.Horizontal) 
        self.slider_filter_distance.label = FixedSizeLabel()
        self.slider_filter_distance.valueChanged.connect(self.handle_filters_change)
        self.slider_filter_distance.setRange(0,2000)
        self.slider_filter_distance.setValue(2000)
        self.side_gui.addWidget(self.slider_filter_distance.label)
        self.side_gui.addWidget(self.slider_filter_distance)
        
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

        self.action_copy = QShortcut(QKeySequence("Ctrl+C"), self)
        self.action_copy.setEnabled(True)
        self.action_copy.activated.connect(self.handle_ctrl_c)
        self.update_map()
        self.handle_filters_change()

    def handle_filters_change(self, arg1=None, arg2=None): 
        min_level = self.slider_filter_level.value()
        max_d = self.slider_filter_distance.value()
        for pos, marker in self.farm_widgets.items():
            d = utils.point_distance(self.my_position, pos )  
            if d > max_d or  marker.farm.level < min_level:
                marker.hide()
            else:
                marker.show()

        self.slider_filter_distance.label.setText(f"Filter by distance: {max_d}")
        self.slider_filter_level.label.setText(f"Filter by level: {min_level}")
    
    def closeEvent(self, event ) -> None:
        exit()
        return super().closeEvent(event)

    def handle_mouse_double_click_on_scene(self, event: QGraphicsSceneMouseEvent):
        self.set_my_position(self.map_to_world(event.scenePos().toTuple()))

    def set_my_position(self, pos):
        self.my_position = pos
        self.my_marker.farm.position = pos
        mpos = self.world_to_map(pos)
        self.my_marker.set_position(mpos)

     
      

    def handle_mouse_move_on_scene(self, event: QGraphicsSceneMouseEvent): 
        pos = self.map_to_world(event.scenePos().toTuple() )
        self.label_cursor.setText(f"Cursor: {pos}")

    def handle_add(self):
        try:
            x = int(self.ledit_x.text())
            y = int(self.ledit_y.text())
            newfarm = Farm((x, y))
            self.farms.add_farm(newfarm)
            if not newfarm.position in self.farm_widgets:
                self.add_marker(newfarm) 
            else:
                self.farm_widgets[newfarm.position].farm = newfarm
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

    def handle_unmark_explored(self, checked):
        for it in self.scene.selectedItems():
            if type(it) is FarmMarker:
                it.set_explored(False)

    def handle_mark_explored(self, checked):
        for it in self.scene.selectedItems():
            if type(it) is FarmMarker:
                it.set_explored(True)

    def handle_goto(self, checked):
        if self.last_selected_marker:
            ok = self.droid.go_to_location(self.last_selected_marker.farm.position)
            if ok: 
                self.last_selected_marker.set_explored(True)

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

    def add_marker(self, farm):
        x, y = self.world_to_map(farm.position)
        item = FarmMarker(farm, (x,y))  

        def handleItemSelectedChanged(sender : FarmMarker, val):
            if val:
                self.set_label_position(sender.farm.position)
                self.last_selected_marker = sender

        item.onSelectedChanged = handleItemSelectedChanged
        self.scene.addItem(item)
        self.farm_widgets[farm.position] = item

    def update_map(self) -> QImage:
        mw, mh = self.map_size
        img = np.zeros((mh, mw, 3), dtype=np.uint8)

        for it in self.farm_widgets.values():
            self.scene.removeItem(it)
        self.farm_widgets.clear()
       
        for farm in self.farms:
            self.add_marker(farm) 

        self.scene.invalidate()

    def set_label_position(self, pos):
        self.label_last_selected.setText(f"Last selected: {pos}")

    def handle_scene_selectionChanged(self):
        self.label_farms_selected.setText(f"Farms selected: {len(self.scene.selectedItems())}")

    def handle_attack_selected(self):
        pass

    def handle_refresh_info(self):
        pass
######################################################################################

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Manage farms')
    parser.add_argument('farms_db', nargs='?', default='FarmsDb.json') 
    ns = parser.parse_args() 

    QApplication.setDoubleClickInterval(250)
    win = WidgetFarmsDisplay(FarmsDb(ns.farms_db))
    win.show()
    QDispatcher.exec()
    exit()

 