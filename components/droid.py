import numpy as np
import pyautogui
from time import sleep
import win32gui
import time
import random

from .recognition import Recognition
from .vision import Vision
from . import utils


class Droid:
    def __init__(self, vision) -> None:
        self.vision: Vision = vision
        self.recognition = Recognition(vision)
        pass

    def activate_win(self, timeout=0.5):
        try:
            if win32gui.GetForegroundWindow() != self.vision.hwnd:
                ret = win32gui.SetForegroundWindow(self.vision.hwnd)
                sleep(0.01)
                ret = win32gui.SetActiveWindow(self.vision.hwnd)
                tstart = time.time()
                while win32gui.GetForegroundWindow() != self.vision.hwnd and time.time() < tstart + timeout:
                    sleep(0.01)
        except Exception as ex:
            print("Exception in Droid.activate_win" + str(ex))

    def click_app(self, pos, dismiss_keyboard=True, delay_after=0.15, radius_px=5):
        self.activate_win()
        if dismiss_keyboard:
            self.assure_keyboard_disabled()
        cx, cy = self.vision.get_screen_position_su(pos)
        cx += random.randint(-radius_px, radius_px)
        cy += random.randint(-radius_px, radius_px)
        pyautogui.leftClick(x=cx, y=cy)
        self.sleep_random(delay_after)

    def click_in_range(self, p1, p2, dismiss_keyboard=True, delay_after=0.15):
        x = utils.random_range(p1[0], p2[0])
        y = utils.random_range(p1[1], p2[1])
        self.click_app((x, y), dismiss_keyboard, delay_after, 0)

    def sleep_random(self, delay, variability=0.2):
        random_delay = (1 + utils.random_range(-variability, +variability)) * delay
        sleep(random_delay)

    def assure_keyboard_disabled(self):
        if self.recognition.is_keybord_enabled():
            self.click_app((0.5, 0.5), False, radius_px=20)

    def open_goto_gum(self):
        # apro gump
        self.click_in_range((0.399, 0.794), (0.471, 0.809))

    def open_search(self):
        self.click_app((0.075, 0.654))

    def go_to_location(self, pos):
        self.activate_win()

        if not self.recognition.is_outside():
            return False
        fx, fy = pos
        # attivo app
        #self.click_app((0.5, 0.5), False)

        # apro gump
        self.open_goto_gum()

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
        self.click_app((0.8, 0.84), delay_after=1)
        return True

    def go_outside(self):
        self.activate_win()
        if self.recognition.is_outside():
            return
        self.click_app((0.86, 0.94), delay_after=8)

    def random_range(self, rangestart, rangend):
        return rangestart + random.random() * (rangend - rangestart)

    def zoom_out(self, pointer_position=(0.466, 0.434)):
        pos = self.vision.get_screen_position_su(pointer_position)
        pyautogui.moveTo(pos)
        sleep(0.1)
        pyautogui.keyDown('ctrl')
        for x in range(10):
            sleep(0.1)
            pyautogui.scroll(-100)
            time.sleep(0.6)
        pyautogui.keyUp('ctrl')

    def move(self, direction_su, drag_start):
        ''' direction is expresses in screen units '''

        drag_start = self.vision.get_screen_position_su(drag_start)

        drag_vector = self.vision.point_su_to_px((-direction_su[0], -direction_su[1]))
        pyautogui.moveTo(x=drag_start[0], y=drag_start[1])
        self.sleep_random(0.1, 0.05)
        pyautogui.mouseDown(button='left')
        self.sleep_random(0.1, 0.05)
        pyautogui.moveRel(
            xOffset=drag_vector[0],
            yOffset=drag_vector[1],
            duration=self.random_range(0.4, .8)
        )
        self.sleep_random(0.1, 0.05)
        pyautogui.mouseUp(button='left')
