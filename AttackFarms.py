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
    farms_positions=[
         (1136, 945), (1049, 969), (1200, 1200), (996, 1123), (1077, 919), (984, 1170), (1020, 935), (988, 951), (964, 1176), (964, 962), (961, 963)        
    ],
    troops_count=4,
    max_cycles=1,
    min_stamina=30,
    user_confirmation_required=False,
    only_explore=True
)

farmer.run()
exit()
