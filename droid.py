import cv2 as cv
import cv2
import numpy as np
from vision import Vision
import pyautogui
from time import sleep
import QImageViewer
from vision import Vision 

class Droid:
    def __init__(self, vision: Vision) -> None:
        self.vision = vision
        pass

    def click_app(self, pos, dismiss_keyboard=True):
        if dismiss_keyboard:
            self.assure_keyboard_disabled()
        cx, cy = self.vision.get_screen_position_rel(pos)
        pyautogui.leftClick(x=cx, y=cy)
        sleep(0.15)

    def assure_keyboard_disabled(self):
        if self.vision.is_keybord_enabled():
            self.click_app((0.5, 0.5), False)

    def go_to_location(self, pos):
        fx, fy = pos
        # todo check that we are outside

        # attivo app
        #self.click_app((0.5, 0.5), False)

        # apro gump
        self.click_app((0.5, 0.81))

        # insert x
        self.click_app((0.22, 0.84))
        with pyautogui.hold('ctrl'):
            sleep(0.1)
            pyautogui.press('a',)
            sleep(0.1)
        pyautogui.press([n for n in str(fx)])
        sleep(0.1)

        # insert y
        self.click_app((0.59, 0.84))
        with pyautogui.hold('ctrl'):
            sleep(0.1)
            pyautogui.press('a',)
            sleep(0.1)
        pyautogui.press([n for n in str(fy)])
        sleep(0.1)

        # click go
        self.click_app((0.8, 0.84))
