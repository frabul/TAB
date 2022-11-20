from droid import Droid
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
import keyboard
import time

class Stages:
    unknown = 'unknown'
    inside = 'inside'
    exit_gump = 'exit_gump'
    outside = 'outside'
    idle = 'idle'
    open_attack = 'open_attack'
    default = 'default'
    pick_troop = 'pick_troop'
    confirm_attack = 'confirm_attack'
    troop_selection = 'troop_selection'
    attack_gump = 'attack_gump'
    bug_search = 'bug_search'


class BugFarmer:
    class OutsideActions:
        OpenSearch = 0

    def __init__(self, droid: Droid) -> None:
        self.droid = droid
        self.rec = droid.recognition
        self.terminate = False
        self.pause = False
        self.actions: dict[str, typing.Callable | dict]
        self.stage = [Stages.unknown, Stages.idle, Stages.unknown, Stages.unknown]
        self.troops_count = 4

        self.stage_decisions = {
            Stages.unknown: self.press_esc,
            Stages.inside: self.droid.go_outside,
            Stages.exit_gump: self.droid.go_outside,
            Stages.outside: {
                Stages.idle: self.search_bug,
                Stages.default: self.esc_and_idle,
            },
            # Stages.bug_search: {
            #    Stages.open_attack: self.open_attack,
            #    Stages.default: self.esc_and_idle
            # },
            Stages.troop_selection: {
                Stages.pick_troop: self.pick_troop,
                Stages.default: self.esc_and_idle,
            },
            Stages.attack_gump: {
                Stages.confirm_attack: self.confirm_attack,
                Stages.default: self.esc_and_idle,
            }
        }

    def step(self):
        act = self.stage_decisions
        depth = 0
        while type(act) is dict:
            if self.stage[depth] in act:
                act = act[self.stage[depth]]
            elif Stages.default in act:
                act = act[Stages.default]
            else:
                act = self.stage_decisions[Stages.unknown]
            depth += 1
        act()
        pass

    def press_esc(self, delay_after=0.1):
        pyautogui.press('esc')
        sleep(delay_after)

    def identify(self):
        if self.rec.is_outside():
            self.stage[0] = Stages.outside
        elif self.rec.is_inside():
            self.stage[0] = Stages.inside
        elif self.rec.is_exit_game_gump():
            self.stage[0] = Stages.exit_gump
        elif self.rec.is_troop_selection_gump():
            self.stage[0] = Stages.troop_selection
        elif self.rec.is_attack_gump():
            self.stage[0] = Stages.attack_gump
        else:
            self.stage[0] = Stages.unknown

    def run(self):  
        def set_stop_requested():
            self.terminate = True

        def toggle_pause():
            self.pause = not self.pause
   
        keyboard.add_hotkey('q', callback=set_stop_requested)
        keyboard.add_hotkey('p', callback=toggle_pause)
        while not self.terminate:
            if self.pause:
                print("Entering pause")
                while self.pause:
                    time.sleep(0.1)
                print("Resuming...")
            self.identify()
            self.step()

    def esc_and_idle(self):
        self.press_esc()
        self.stage[1] = Stages.idle

    def search_bug(self):
        troops_available = self.troops_count - self.rec.get_troops_deployed_count()
        if troops_available > 0:
            # we arre in outside stage
            # click magniglass
            self.droid.click_app((0.075, 0.654), delay_after=1)
            # confirm search
            self.droid.click_app((0.804, 0.865), delay_after=1)
            # click bug found
            self.droid.click_app((0.473, 0.506), delay_after=1)
            self.stage[1] = Stages.confirm_attack
        else:
            sleep(5)

    def confirm_attack(self):
        # click attack
        self.droid.click_app((0.47, 0.66), delay_after=1)
        self.stage[1] = Stages.pick_troop

    def pick_troop(self):
        # click march
        self.droid.click_app((0.71, 0.94), delay_after=1)
        # check if it was accepted
        if self.rec.is_troop_selection_gump():
            # it was not accepted, probably troop stamina depleted
            # decrease available troops and increase it after 5 minutes
            self.troops_count -= 1
            self.esc_and_idle()

            def increase():
                self.troops_count += 1
            time = threading.Timer(60*5, increase)
            time.start()
        else:
            self.stage[1] = Stages.idle


if __name__ == '__main__':
    import threading
    droid = Droid(Vision('BlueStacks App Player', (1, 35, 1, 1)))
    droid.vision.start()
    while not droid.vision.is_ready():
        sleep(1)
    farmer = BugFarmer(droid)

    t = threading.Thread(target=farmer.run)
    t.start()
