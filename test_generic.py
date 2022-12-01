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
from components import recognition 

recognition.debug = True

rect = QRect(0,0,100,100)  
print(rect.contains(0,100, False))

 
import keyboard
import os

vision = Vision('BlueStacks App Player', (1, 35, 1, 1))
vision.start()
while not vision.is_ready():
    time.sleep(0.1)
rec = Recognition(vision)
# rec.templates.magniglass.save(vision)
# rec.templates.nest_l16.save(vision)
debug = True
while not keyboard.is_pressed('alt+q'):
    
    #print(f'is_outside: {rec.is_outside()}')
    #print(f'is_inside: {rec.is_inside()}')

    # test read_world_position
    #pos = rec.read_world_position()
    #print(f'Pos read: {pos}')

    # test get_troops_deployed_count
    # print(rec.get_troops_deployed_count())
    #print(f"is attack = {rec.is_attack_gump()}")

    # test read tile info
    #rint(rec.read_nest_info())

    staminas = rec.read_staminas()
    print(f'Squads found: {staminas}')
    for s in staminas:
        print(s)

    #print(f'is_march_button() -> {rec.is_march_button()}')

    #print(f'read_nest_level() -> {rec.read_nest_level()}')

    time.sleep(1)
os._exit(0)