import time
from droid import Droid
from vision import Vision
from recognition import Recognition
from FarmsDb import FarmsDb, Farm
import keyboard
import utils
class FarmsFinder:
    def __init__(self) -> None:
        self.vision = Vision('BlueStacks App Player', (1, 35, 1, 1))
        self.vision.start()
        self.droid = Droid(self.vision)
        self.farms = FarmsDb('FarmsDb_new.json')
        self.recognition = self.droid.recognition
        self.x_start = 776
        self.x_step = -4
        self.move_direction = (0, 0.16)

    def move(self):
        map_pos = self.droid.recognition.read_world_position()
        if map_pos:
            print(f'Scanning at {map_pos}')
            if map_pos[0] == 1200 or map_pos[1] == 1200:
                self.x_start += self.x_step
                self.droid.go_to_location((self.x_start, 0))
        else:
            print(f'Scanning at unknown position')
        drag_start = (utils.random_range(0.12, 0.9), utils.random_range(0.60, 0.85))
        direction = (
            self.move_direction[0] * utils.random_range(0.75, 1.25),
            self.move_direction[1] * utils.random_range(0.75, 1.25)   )
        f.droid.move(direction, drag_start)
      
    def run(self):
        self.stop_requested = False
        self.pause = False
        # inizializzazione
        while not f.droid.vision.is_ready():
            time.sleep(0.2)

        #self.droid.go_to_location((self.x_start, 0))
        def set_stop_requested():
            self.stop_requested = True
        def toggle_pause():
            self.pause = not self.pause

        keyboard.add_hotkey('q', callback=set_stop_requested )
        keyboard.add_hotkey('p', callback=toggle_pause )
        while not self.stop_requested: 

            if self.pause:
                print("Entering pause")
                while self.pause:
                    time.sleep(0.1)
                print("Resuming...")

            self.move()
            time.sleep(0.1)
            # search nest
            nests = self.droid.recognition.templates.nest_l16.find_all(self.vision, (0.135, 0.531), (0.917, 0.855))
            #if len(nests)>0:
            #    nests = self.droid.recognition.templates.nest_l16.find_all(self.vision, (0.135, 0.531), (0.917, 0.855))
            for nest in nests:
                print(f'Nest found at {nest.center().x()}, {nest.center().y()}')
                self.droid.click_app((nest.center().x(), nest.center().y()))
                trycnt = 0
                while trycnt < 20:
                    name, ally, location = self.recognition.read_location_info()
                    trycnt += 1
                    if (name is None or location is None):
                        time.sleep(0.25)
                    else:
                        if location[0] >= 0 and location[0] <= 1200 and location[1] >= 0 and location[1] <= 1200:
                            print(f'Adding farm {name} at {location} ')
                            self.farms.add_farm(Farm(location, name=name, alliance=ally))
                            self.farms.save()
                        break


if __name__ == '__main__':
    
    f = FarmsFinder()
    # while not f.droid.vision.is_ready():
    #    time.sleep(0.2)
    # while not keyboard.is_pressed('q'):
    #    f.droid.move((0, 0.2))
    f.run()
    exit()
    pass
