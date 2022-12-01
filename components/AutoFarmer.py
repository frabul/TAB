
import typing 
import numpy as np
import pyautogui
from time import sleep
from PySide6.QtWidgets import QMessageBox 
import keyboard
import time
import threading
from . import QDispatcher  
from . import utils
from .vision import Vision 
from .droid import Droid

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


class AutoFarmer:

    def __init__(self, droid: Droid, farms_positions: list = None, troops_count=4, min_stamina=40, user_confirmation_required=False, max_cycles=2) -> None:
        self.min_stamina = min_stamina
        self.initial_troops = troops_count
        self.troops_count = troops_count
        self.farms_positions = farms_positions
        self.need_user_confirmation = user_confirmation_required
        self.max_cycles = max_cycles

        self.farms_attacked = 0
        self.troops_available_confirmation = 0
        self.droid = droid
        self.rec = droid.recognition
        self.actions: dict[str, typing.Callable | dict]
        self.stage = [Stages.unknown, Stages.idle, Stages.unknown, Stages.unknown]
        self.pause = False
        self.terminate = False
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

        # if farms_positions is not None then attack farms instead of bugs
        if not farms_positions is None:
            self.farms_attacked = 0
            self.stage_decisions[Stages.outside][Stages.idle] = self.search_farm

    def next_farm(self):
        if self.farms_attacked > len(self.farms_positions) * self.max_cycles:
            self.terminate = True
            return None

        farmindex = self.farms_attacked % len(self.farms_positions)
        print(f'Trying to attack farm {farmindex+1} of {len(self.farms_positions)}')
        return self.farms_positions[farmindex]

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

    def press_esc(self, delay_after=0.35):
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

    ########### RUN ###############
    def run(self):
        print("Running autofarmer")
        self.farms_attacked = 0

        def set_stop_requested():
            self.terminate = True 
        def toggle_pause():
            self.pause = not self.pause 
        def toggle_confirm_required():
            self.need_user_confirmation = not self.need_user_confirmation
            print(f'need_user_confirmation is now {self.need_user_confirmation}')

        keyboard.add_hotkey('alt+q', callback=set_stop_requested)
        keyboard.add_hotkey('alt+s', callback=toggle_pause)
        keyboard.add_hotkey('alt+w', callback=toggle_confirm_required)

        while not self.terminate:
            self.pause_loop()
            self.identify()
            self.pause_loop()
            self.step()

        keyboard.remove_hotkey(set_stop_requested)
        keyboard.remove_hotkey(toggle_pause)
        keyboard.remove_hotkey(toggle_confirm_required)
        print('Autofarmer terminated')

    def pause_loop(self):
        if self.pause:
            print("Entering pause")
            while self.pause:
                time.sleep(0.1)
            print("Resuming...")

    def esc_and_idle(self):
        self.droid.activate_win()
        self.press_esc()
        self.stage[1] = Stages.idle

    def wait_for_user_confirmation(self):
        self.can_go = False

        def show_box():
            msgBox = QMessageBox()
            msgBox.setText("Can go?")
            msgBox.exec()
            self.can_go = True
        QDispatcher.enqueue_job(show_box)
        while not self.can_go:
            sleep(0.1)

    def confirm_troop(self):
        # wait for troop availabe
        troops_available = self.troops_count - self.rec.get_troops_deployed_count()
        # sometimes a message can interfer with get_troops_deployed_count() so confirm it
        if troops_available > 0:
            self.troops_available_confirmation += 1
        else:
            self.troops_available_confirmation = 0

        if self.troops_available_confirmation > 2:
            self.troops_available_confirmation = 0
            return True
        return False

    def search_bug(self):
        if self.confirm_troop():
            if self.need_user_confirmation:
                self.wait_for_user_confirmation()

            # we arre in outside stage
            # click magniglass
            self.droid.click_app((0.075, 0.654), delay_after=0.75)
            # confirm search
            self.droid.click_app((0.804, 0.865), delay_after=0.75)
            # click bug found
            self.droid.click_app((0.473, 0.506), delay_after=0.75)
            self.stage[1] = Stages.confirm_attack
        else:
            sleep(1.5)

    def search_farm(self):
        if self.confirm_troop():
            if self.need_user_confirmation:
                self.wait_for_user_confirmation()
            sleep(0.5)
            fpos = self.next_farm()
            if(not fpos is None):
                self.droid.activate_win()
                self.droid.go_to_location(fpos)
                sleep(0.5)
                # click farm
                self.droid.click_in_range((0.42, 0.431), (0.516, 0.464), delay_after=0.6)
                # click attack
                self.droid.click_in_range((0.556, 0.607), (0.614, 0.638), delay_after=0.6)

                if self.droid.recognition.is_troop_selection_gump():
                    self.stage[1] = Stages.pick_troop
                else:
                    # if no gump go to next farm
                    self.farms_attacked += 1
        else:
            sleep(1.5)

    def confirm_attack(self):
        # click attack
        self.droid.click_app((0.47, 0.66), delay_after=0.6)
        self.stage[1] = Stages.pick_troop

    def pick_troop(self):
        done = self.try_pick_troop()
        if done:
            self.farms_attacked += 1

    def try_pick_troop(self) -> bool:
        def try_confirm():
            # check staminas
            staminas = self.rec.read_staminas()
            print(f'Staminas found {[x[0] for x in staminas]}')
            stamok = [x for x in staminas if x[0] >= self.min_stamina]
            # check if the selected
            for troop in stamok:
                # click the position
                self.droid.click_app(troop[1], delay_after=1)
                if self.rec.is_march_button():
                    # click march
                    self.droid.click_app((0.71, 0.94), delay_after=0.6)
                    if self.rec.is_outside():
                        return True
                    elif self.rec.is_troop_selection_gump():
                        # probably the troop is not available
                        self.decrease_available_troops()
                        pass
                    if not self.rec.is_outside() and not self.rec.is_troop_selection_gump():
                        # we have some kind of gump probably
                        self.droid.activate_win()
                        self.press_esc()
            return False

        ok = try_confirm()
        if not ok and self.initial_troops > 2:
            # scroll down and second try again
            sx = utils.random_range(0.4, 0.43)
            sy = utils.random_range(0.74, 0.77)
            self.droid.move((0, 0.5), (sx, sy))
            #self.droid.move((0, 0.5), (sx, sy))
            sleep(1)
            ok = try_confirm()

        if not ok:
            self.decrease_available_troops()
            self.droid.activate_win()
            self.press_esc()

        self.stage[1] = Stages.idle
        return ok

    def decrease_available_troops(self):
        # it was not accepted, probably troop stamina depleted
        # decrease available troops and increase it after 5 minutes
        self.troops_count -= 1

        def increase():
            self.troops_count += 1
        time = threading.Timer(60 * 5, increase)
        time.start()

 
