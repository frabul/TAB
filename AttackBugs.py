from components.AutoFarmer import AutoFarmer
from components.droid import Droid
from components.vision import Vision
from time import sleep
import sys


droid = Droid(Vision('BlueStacks App Player', (1, 35, 1, 1)))
droid.vision.start()
while not droid.vision.is_ready():
    sleep(1)

farmer = AutoFarmer(
    droid,
    troops_count=4,
    max_cycles=1,
    min_stamina=30,
    user_confirmation_required=False,
)

farmer.run()
sys.exit()
