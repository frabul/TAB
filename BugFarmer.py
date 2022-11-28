from AutoFarmer import AutoFarmer
from droid import Droid
from vision import Vision
from time import sleep

droid = Droid(Vision('BlueStacks App Player', (1, 35, 1, 1)))
droid.vision.start()
while not droid.vision.is_ready():
    sleep(1)

farmer = AutoFarmer(
    droid, 
    troops_count=4,
    max_cycles=1,
    min_stamina=50,
    user_confirmation_required=True,
)

farmer.run()
exit()