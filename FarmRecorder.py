import time
from components.droid import Droid
from components.vision import Vision 
from components.FarmsDb import FarmsDb, Farm
from PySide6.QtCore import QRect,QRectF
import keyboard
from components import utils
import pyautogui
import os
import json

farms = FarmsDb('FarmsDb_new.json')
vision = Vision('BlueStacks App Player', (1, 35, 1, 1))
vision.start()
droid = Droid(vision)
recognition = droid.recognition 
stop_requested = False
pause = False
scan_p1 = (0.283, 0.465)
scan_p2 = (0.795, 0.829)

def pause_loop():
    if pause:
        print("Entering pause")
        while pause:
            time.sleep(0.1)
        print("Resuming...")
time.sleep(1)
while True: 
    name, ally, location = recognition.read_location_info() 
    if (name is None or location is None):
        pass
    else:
        if location[0] >= 0 and location[0] <= 1200 and location[1] >= 0 and location[1] <= 1200:
            print(f'Adding farm {name} from {ally} at {location} ')
            farms.add_farm(Farm(location, name=name, alliance=ally))
            farms.save()
     
    time.sleep(1)     