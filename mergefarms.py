from components import FarmsDb
db1 = FarmsDb.FarmsDb('FarmsDb.json')
db2 = FarmsDb.FarmsDb('FarmsDb_new.json')

for farm in db1:
    db2.add_farm(farm)

db2.save()
