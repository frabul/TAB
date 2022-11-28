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

rect = QRect(0,0,100,100)  
print(rect.contains(0,100, False))