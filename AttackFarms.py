from components.AutoFarmer import AutoFarmer
from components.droid import Droid
from components.vision import Vision
from time import sleep

droid = Droid(Vision('BlueStacks App Player', (1, 35, 1, 1)))
droid.vision.start()
while not droid.vision.is_ready():
    sleep(1)

farmer = AutoFarmer(
    droid,
    # farms_positions=[
    #  (1022, 84), (963, 112), (1168, 114), (1090, 148), (985, 91), (914, 59), (1154, 151), (1037, 93), (914, 110), (1103, 34), (1062, 23)
    # ],
    troops_count=4,
    max_cycles=1,
    min_stamina=30,
    user_confirmation_required=False,
)

farmer.run()
exit()
