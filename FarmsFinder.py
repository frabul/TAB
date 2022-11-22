import time
from droid import Droid
from vision import Vision
from recognition import Recognition
from FarmsDb import FarmsDb, Farm
from PySide6.QtCore import QRect, QRectF
import keyboard
import utils
import pyautogui
import os
import json
import logging



class FarmsFinder:
    def __init__(self, db_file) -> None:
        self.stop_requested = False
        self.pause = False
        self.farms = FarmsDb(db_file)
        self.sessions_file = 'FarmsFinderSession.json'
        self.vision = Vision('BlueStacks App Player', (1, 35, 1, 1))
        self.vision.start()
        self.droid = Droid(self.vision)
        self.recognition = self.droid.recognition
        self.column_step = 5
        self.skip_zone = QRect(350, 350, 500, 500)

        self.scan_p1 = (0.283, 0.465)
        self.scan_p2 = (0.795, 0.829)
        self.scan_size = utils.point_sub(self.scan_p2, self.scan_p1)
        self.move_direction = (0, self.scan_size[1] * 0.65)
        self.session = {
            'last_x': 1200,
            'last_y': 0
        }
        self.load_session()

        def set_stop_requested():
            self.stop_requested = True

        def toggle_pause():
            self.pause = not self.pause

        keyboard.add_hotkey('alt+q', callback=set_stop_requested)
        keyboard.add_hotkey('alt+p', callback=toggle_pause)

    def load_session(self):
        try:
            if os.path.exists(self.sessions_file):
                with open(self.sessions_file, 'r') as fs:
                    self.session = json.load(fs)
        except:
            logging.warning('FarmsFinder: session file not found!')

    def save_session(self):
        with open(self.sessions_file, 'w') as fs:
            json.dump(self.session, fs)

    def assure_stage(self):
        if self.recognition.is_attack_gump() or self.recognition.is_lizard_rally_gump():
            x = utils.random_range(0.259, 0.785)
            y = utils.random_range(0.1, 0.22)
            self.droid.click_app((x, y))
        self.dismiss_tile_info()

    def dismiss_tile_info(self):
        marker_pos = self.recognition.templates.location_marker.find_max(self.vision, (0.006, 0.082), (0.917, 0.849))
        if not marker_pos is None:
            # open goto position gump
            self.droid.open_search()
            if not self.recognition.is_outside():
                pyautogui.press('esc')

    def move(self):
        self.droid.activate_win()
        self.assure_stage()
        map_pos = self.droid.recognition.read_world_position()
        if map_pos:
            logging.info(f'Scanned at {map_pos}')

            if map_pos[0] == 1200 or map_pos[1] == 1200:
                
                self.save_session()
                if self.session['last_x'] >= 0:
                    self.session['last_x'] -= self.column_step
                    self.session['last_x'] = max(self.session['last_x'], 0)
                else:
                    self.session['last_y'] += self.column_step
                    self.session['last_y'] = min(self.session['last_y'], 1200)
                nextposition = (self.session['last_x'], self.session['last_y'])
                logging.info('Map limit reached. Pass to next column: {nextposition}')
                
                self.droid.go_to_location(nextposition)

            elif self.skip_zone.contains(map_pos[0], map_pos[1]):
                logging.info('Move out of skip zone')
                cursor = map_pos
                while self.skip_zone.contains(*cursor):
                    cursor = utils.point_sum(cursor, (1, 1))
                self.droid.go_to_location(cursor)

        else:
            logging.warning(f'Scanned at unknown position')
        drag_start = utils.random_point_in_rectangle((0.128, 0.523), (0.823, 0.776))
        #drag_start = (utils.random_range(0.12, 0.9), utils.random_range(0.60, 0.85))
        direction = (
            self.move_direction[0] * utils.random_range(0.85, 1.15),
            self.move_direction[1] * utils.random_range(0.85, 1.15))
        f.droid.move(direction, drag_start)

    def pause_loop(self):
        if self.pause:
            print("Entering pause")
            while self.pause:
                time.sleep(0.1)
            print("Resuming...")

    def run(self):

        self.stop_requested = False
        self.pause = False
        # inizializzazione
        while not f.droid.vision.is_ready():
            time.sleep(0.2)

        while not self.stop_requested:
            self.pause_loop()
            if self.stop_requested:
                return
            # move
            self.move()
            self.pause_loop()
            if self.stop_requested:
                return
            time.sleep(0.1)

            # search nest
            nests = self.droid.recognition.templates.nest_l16_mini.find_all(self.vision, self.scan_p1, self.scan_p2)
            for nest in nests:
                if self.stop_requested:
                    return
                self.pause_loop()
                logging.info(f'Nest found at {nest.center().x()}, {nest.center().y()}')
                self.droid.click_app((nest.center().x(), nest.center().y()))
                trycnt = 0
                while trycnt < 20:
                    name, ally, location = self.recognition.read_location_info()
                    trycnt += 1
                    if (name is None or location is None):
                        time.sleep(0.25)
                    else:
                        if location[0] >= 0 and location[0] <= 1200 and location[1] >= 0 and location[1] <= 1200:
                            logging.info(f'Adding farm {name} from {ally} at {location} ')
                            logging.info(f'Now we have {len(self.farms.farms)} farms.')
                            self.farms.add_farm(Farm(location, name=name, alliance=ally))
                            self.farms.save()
                        break
                self.dismiss_tile_info()
            
            farms_count = self.farms.farms
            

if __name__ == '__main__':
    logging.basicConfig(
        filename='FarmsFinderLog.log', 
        format='%(asctime)s %(message)s',
        encoding='utf-8', 
        level=logging.DEBUG
    )
    f = FarmsFinder('FarmsDb_new.json')
    # while not f.droid.vision.is_ready():
    #    time.sleep(0.2)
    # while not keyboard.is_pressed('q'):
    #    f.droid.move((0, 0.2))
    f.run()
    exit()
