from droid import Droid
import typing
import cv2 as cv
import cv2
import numpy as np
from vision import Vision
import pyautogui
from time import sleep
import QImageViewer
from PySide6.QtWidgets import QMessageBox
from vision import Vision
from recognition import Recognition
import keyboard
import time
import QDispatcher
import utils

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

    min_stamina = 40
    troops_count = 4
    need_user_confirmation = False

    def __init__(self, droid: Droid) -> None:
        self.droid = droid
        self.rec = droid.recognition
        self.terminate = False
        self.pause = False
        self.actions: dict[str, typing.Callable | dict]
        self.stage = [Stages.unknown, Stages.idle, Stages.unknown, Stages.unknown]
    
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

        keyboard.add_hotkey('alt+q', callback=set_stop_requested)
        keyboard.add_hotkey('alt+p', callback=toggle_pause)

        while not self.terminate:
            if self.pause:
                print("Entering pause")
                while self.pause:
                    time.sleep(0.1)
                print("Resuming...")
            self.identify()
            self.step()

    def esc_and_idle(self):
        self.droid.activate_win()
        self.press_esc()
        self.stage[1] = Stages.idle

    def wait_for_user_confirmation(self):
        self.can_go = False
        def show_box(): 
            msgBox  = QMessageBox()
            msgBox.setText("Can go?") 
            msgBox.exec()
            self.can_go = True
        QDispatcher.enqueue_job(show_box)  
        while not self.can_go:
            sleep(0.1) 

    def search_bug(self):
        troops_available = self.troops_count - self.rec.get_troops_deployed_count()
        if troops_available > 0: 
            if self.need_user_confirmation: 
                self.wait_for_user_confirmation()        
            # we arre in outside stage
            # click magniglass
            self.droid.click_app((0.075, 0.654), delay_after=0.4)
            # confirm search
            self.droid.click_app((0.804, 0.865), delay_after=0.4)
            # click bug found
            self.droid.click_app((0.473, 0.506), delay_after=0.4)
            self.stage[1] = Stages.confirm_attack
        else:
            sleep(5)

    def confirm_attack(self):
        # click attack
        self.droid.click_app((0.47, 0.66), delay_after=0.4)
        self.stage[1] = Stages.pick_troop

    def pick_troop(self):

        def try_confirm():
            # check staminas
            staminas = self.rec.read_staminas()
            print(f'Staminas found {[x[0] for x in staminas]}')
            stamok = [x for x in staminas if x[0] >= self.min_stamina]

            # check if the selected
            for troop in stamok:
                # click the position
                self.droid.click_app(troop[1], delay_after=0.4)
                if self.rec.is_march_button():
                    # click march
                    self.droid.click_app((0.71, 0.94), delay_after=0.4)
                    if self.rec.is_outside():
                        return True
                    elif self.rec.is_troop_selection_gump():
                        # probably the troop is not available
                        self.decrease_available_troops()
                        pass
                    if not self.rec.is_outside() and not self.rec.is_troop_selection_gump():
                        # we have some kind of gump probably
                        self.droid.activate_win()
                        pyautogui.press('esc')

            return False
        ok = try_confirm()
        if not ok:
            # scroll down and second try again
            sx = utils.random_range(0.4, 0.43)
            sy = utils.random_range(0.74, 0.77) 
            self.droid.move((0, 0.5), (sx, sy))
            self.droid.move((0, 0.5), (sx, sy))
            sleep(1)
            ok = try_confirm()
        if not ok:
            self.decrease_available_troops()

        self.stage[1] = Stages.idle
        if not self.rec.is_outside():
            self.droid.activate_win()
            pyautogui.press('esc')

    def decrease_available_troops(self):
        # it was not accepted, probably troop stamina depleted
        # decrease available troops and increase it after 5 minutes
        self.troops_count -= 1
        self.esc_and_idle()

        def increase():
            self.troops_count += 1
        time = threading.Timer(60 * 5, increase)
        time.start()


if __name__ == '__main__':
    import threading
    droid = Droid(Vision('BlueStacks App Player', (1, 35, 1, 1)))
    droid.vision.start()
    while not droid.vision.is_ready():
        sleep(1)
    farmer = BugFarmer(droid)

    t = threading.Thread(target=farmer.run)
    t.start()
