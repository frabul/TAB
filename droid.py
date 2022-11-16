import typing
import cv2 as cv
import cv2
import numpy as np
from vision import Vision
import pyautogui
from time import sleep
import QImageViewer
from vision import Vision
from recognition import Recognition


class Droid:
    def __init__(self, vision: Vision) -> None:
        self.vision = vision
        self.recognition = Recognition(vision)
        pass

    def click_app(self, pos, dismiss_keyboard=True, delay_after=0.15):
        if dismiss_keyboard:
            self.assure_keyboard_disabled()
        cx, cy = self.vision.get_screen_position_rel(pos)
        pyautogui.leftClick(x=cx, y=cy)
        sleep(delay_after)

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

    def go_outside(self):
        if self.vision.is_outside():
            return
        self.click_app((0.86, 0.94))

    def attack_insect(self):
        self.go_outside()
        # controllo se ho una truppa free
        troops_deployed = self.recognition.get_troops_deployed()
        # click lente
        self.click_app((0.39, 0.88))
        # conferma ricerca
        self.click_app((0.81, 0.87))
        # click bug
        self.click_app((0.46, 0.5))
        # click attack
        self.click_app((0.47, 0.66))
        # click march
        self.click_app((0.71, 0.94))


