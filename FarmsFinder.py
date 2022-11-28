import time
from components.droid import Droid
from components.vision import Vision
from components.recognition import Recognition
from components.FarmsDb import FarmsDb, Farm
from PySide6.QtCore import QRect, QRectF
import keyboard
from components import utils
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
        self.scan_p1 = (0.283, 0.465)
        self.scan_p2 = (0.795, 0.829)
        self.scan_size = utils.point_sub(self.scan_p2, self.scan_p1)
        self.move_direction = (0, self.scan_size[1] * 0.65)
        self.session = {
            'search_area': (0, 0, 1200, 1200),
            'skip_area': (350, 350, 500, 500),
            'sweep_start': (1200, 0)
        }

        # prepare templates
        self.templates   = []
        for k, v in self.recognition.templates.items.items():
            if k.startswith('nest') and k.endswith('mini'):
                self.templates.append(v)
        
        # load session
        self.load_session()
 
        def set_stop_requested():
            self.stop_requested = True

        def toggle_pause():
            self.pause = not self.pause

        keyboard.add_hotkey('alt+q', callback=set_stop_requested)
        keyboard.add_hotkey('alt+s', callback=toggle_pause)

    @property
    def skip_zone(self):
        if 'skip_area' in self.session:
            return QRect(*self.session['skip_area'])
        else:
            return QRect(0, 0, 0, 0)
    # @skip_zone.setter
    # def skip_zone(self, val:tuple):
    #    self.session['skip_area'] = val

    @property
    def search_area(self):
        if 'search_area' in self.session:
            return self.session['search_area']
        else:
            return (0, 0, 1200, 1200)

    @search_area.setter
    def search_area(self, val: tuple):
        self.session['search_area'] = val

    @property
    def sweep_start(self):
        if 'sweep_start' in self.session:
            return self.session['sweep_start']
        else:
            x1, y1, w, h = self.search_area
            return ( x1 + w, y1)

    @sweep_start.setter
    def sweep_start(self, val: tuple):
        self.session['sweep_start'] = val

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
        # check if the game is open
        app_icon_pos = self.recognition.templates.app_icon.find_max(self.vision, (0, 0), (1, 1))
        if not app_icon_pos is None:
            logging.info('App closed, trying to launch')
            self.droid.click_app(app_icon_pos[1], False, delay_after=40)

        # dismiss attacks gumps eventually
        if self.recognition.is_attack_gump() or self.recognition.is_lizard_rally_gump():
            x = utils.random_range(0.259, 0.785)
            y = utils.random_range(0.1, 0.22)
            self.droid.click_app((x, y))

        # check if we are inside or outside
        is_inside = self.recognition.is_inside()
        is_outside = self.recognition.is_outside()
        if not is_inside and not is_outside:
            logging.debug('[assure_stage] not inside or outspide -> try esc')
            pyautogui.press('esc')
            time.sleep(0.5)

        is_inside = self.recognition.is_inside()
        is_outside = self.recognition.is_outside()
        if is_inside:
            logging.info('We are inside. Trying to go out and reduce zoom')
            # todo - go outside and reduce zoom
            self.droid.go_outside()
            is_outside = self.recognition.is_outside()
            if is_outside:
                self.droid.go_to_location(self.sweep_start)
                self.droid.activate_win()
                self.droid.zoom_out()
                self.droid.move((0, 0.1), (0.5, 0.5))
                time.sleep(0.5)
                self.droid.zoom_out()

        # dismissi tile info if it exists
        if is_outside:
            self.dismiss_tile_info()
        return is_outside

    def dismiss_tile_info(self):
        marker_pos = self.recognition.templates.location_marker.find_max(self.vision, (0.006, 0.082), (0.917, 0.849))
        if not marker_pos is None:
            # open goto position gump
            self.droid.open_search()
            time.sleep(0.5)
            if not self.recognition.is_outside():
                pyautogui.press('esc')

    def get_next_sweep_start(self):
        lx, ly = self.sweep_start
        x1, y1, w, h = self.search_area
        x2 = x1 + w
        y2 = y1 + h
        area = QRect(*self.search_area)
        # check that start point is on the edges of the area
        ok = (lx >= x1 and lx <= x2 and ly == 0) or (ly >= y1 and ly <= y2 and lx == 0)
        if not ok:
            return (x2, y1)
        if lx > x1:
            lx -= self.column_step
            lx = max(lx, x1)
        else:
            ly += self.column_step
            ly = min(ly, y2)
        return (lx, ly)

    def move(self):
        self.droid.activate_win()
        stage_ok = self.assure_stage()
        if not stage_ok:
            logging.error(f'assure_stage() returned False')
            time.sleep(60)
            return False

        map_pos = self.droid.recognition.read_world_position()
        if map_pos:
            logging.info(f'Scanned at {map_pos}')
            if not QRect(*self.search_area).contains(*map_pos):
                self.save_session()
                nextposition = self.get_next_sweep_start()
                self.droid.go_to_location(nextposition)
                self.sweep_start = nextposition
                logging.info(f'Search area limit reached. Pass to next sweep: {nextposition}')
            else:
                if self.skip_zone.contains(map_pos[0], map_pos[1]):
                    self.steps_in_skip_zone += 1
                else:
                    self.steps_in_skip_zone = 0

                if self.steps_in_skip_zone > 2:
                    self.steps_in_skip_zone = 0
                    logging.info('Moving out of skip zone')
                    cursor = self.sweep_start
                    # cursor start at the colum origin and then moves to skip zone
                    while not self.skip_zone.contains(*cursor):
                        cursor = utils.point_sum(cursor, (1, 1))
                    # exit out of skip zone
                    while self.skip_zone.contains(*cursor):
                        cursor = utils.point_sum(cursor, (1, 1))
                    x, y = cursor
                    if x > 1200:
                        logging.warning('Cursor.x > 1200 out of skip zone')
                        x = 1200
                    if y > 1200:
                        logging.warning('Cursor.y > 1200 out of skip zone')
                        y = 1200
                    # exit
                    self.droid.go_to_location((x, y))
        else:
            logging.warning(f'Scanned at unknown position')
        drag_start = utils.random_point_in_rectangle((0.128, 0.523), (0.823, 0.776))
        #drag_start = (utils.random_range(0.12, 0.9), utils.random_range(0.60, 0.85))
        direction = (
            self.move_direction[0] * utils.random_range(0.85, 1.15),
            self.move_direction[1] * utils.random_range(0.85, 1.15))
        f.droid.move(direction, drag_start)
        return True

    def pause_loop(self):
        if self.pause:
            print("Entering pause")
            while self.pause:
                time.sleep(0.1)
            print("Resuming...")

    def run(self):
        self.steps_in_skip_zone = 0
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
            ok = self.move()
            self.pause_loop()
            if self.stop_requested:
                return
            time.sleep(0.1)
            if not ok:
                continue
            # search nest
            nests : list[QRectF]= [] 
            for t   in self.templates   :  
                rects =  t.find_all(self.vision, self.scan_p1, self.scan_p2) + \
                [nests.append(x) for x in rects]
                
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




if __name__ == '__main__':
    import sys
    logging.basicConfig(
        filename='FarmsFinderLog.log',
        format='%(asctime)s %(message)s',
        encoding='utf-8',
        level=logging.DEBUG
    )
    root = logging.getLogger()
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    root.addHandler(handler)

    f = FarmsFinder('FarmsDb_new.json')
    # while not f.droid.vision.is_ready():
    #    time.sleep(0.2)
    # while not keyboard.is_pressed('q'):
    #    f.droid.move((0, 0.2))
    f.run()
    exit()
