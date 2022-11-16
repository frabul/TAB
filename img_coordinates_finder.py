
import time
import cv2
import numpy as np
from vision import Vision
import QImageViewer

vision = Vision('BlueStacks App Player', 1, 34)

# creo mappa
farms_img = np.zeros((600, 600, 3), dtype=np.uint8)


def update_image(x, y):
    global farms_img
    screen = vision.get_last()
    if screen is None:
        return
    font = cv2.FONT_HERSHEY_SIMPLEX
    org = (10, 30)
    fontScale = 0.5
    color = (200, 200, 200)
    thickness = 1

    farms_img = np.copy(screen)
    xrel = round(x / screen.shape[1], 2)
    yrel = round(y / screen.shape[0], 2)
    str = f"X: {x} ({xrel})    Y: {y} ({yrel})"
    farms_img = cv2.putText(farms_img, str, org, font, fontScale, color, thickness, cv2.LINE_AA)

# cv2.namedWindow("farms")
#cv2.setMouseCallback("farms", handle_mouse)
last_x =0
last_y = 0
def handle_mouse_move(x,y):
    global last_x, last_y
    last_x = x
    last_y = y

QImageViewer.create_window('farms' )
time.sleep(0.2)
QImageViewer.set_mouse_move_handler("farms", handle_mouse_move) 

vision.start()

import keyboard
import os
while True:  
    update_image(last_x, last_y)
    QImageViewer.show_image('farms', farms_img) 
    time.sleep(0.1)
    if keyboard.is_pressed('ctrl+q'):
        QImageViewer.WINMAN.app.exit()
        os._exit(0)
 