import datetime
import json
import os.path
import os
import shutil


class Farm:
    strtimeformat = '%Y%m%d%H%M%S'

    def __init__(self, position=(0, 0), level=1, name=None, last_raid=None, alliance = None) -> None:
        self.position = position
        self.level = level
        self.name = name
        self.alliance = alliance
        if last_raid:
            self.last_raid = last_raid
        else:
            self.last_raid = datetime.datetime.min

    @staticmethod
    def from_json_object(jfarm):
        return Farm(
            position=tuple(jfarm['position']),
            level=jfarm['level'],
            name=jfarm['name'],
            last_raid=datetime.datetime.strptime(jfarm['last_raid'], Farm.strtimeformat)
        )

    def to_json_object(self):
        return {
            'position': self.position,
            'level': self.level,
            'name': self.name,
            'last_raid': self.last_raid.strftime(Farm.strtimeformat)
        }


class FarmsDb:

    def __init__(self, farms_file: str, farms_list: list[Farm] = None) -> None:
        self.farms: dict[tuple, Farm] = {}
        self.farms_file = farms_file

        if os.path.isfile(self.farms_file):
            try:
                with open(farms_file, 'r') as fs:
                    jfarms = json.load(fs)
                    for jf in jfarms:
                        fa = Farm.from_json_object(jf)
                        self.farms[fa.position] = fa
            except Exception as ex:
                print("[FarmsDb] error during load db: " + str(ex))
        else:
            print("[FarmsDb] db file not found")

        if farms_list:
            for fa in farms_list:
                self.farms[fa.position] = fa

    def save(self, backup=True):
        if backup and os.path.isfile(self.farms_file):
            fname = os.path.basename(self.farms_file)
            dirname = os.path.dirname(self.farms_file)
            backupsDir = os.path.join(dirname, 'FarmsDbBackups')
            os.makedirs(backupsDir, exist_ok=True)
            backup_file = os.path.join(backupsDir, datetime.datetime.now().strftime('%Y%m%d%H%M%S%f.json'))
            shutil.copyfile(self.farms_file, backup_file)

        with open(self.farms_file, 'w') as fs:
            fli = [fa.to_json_object() for fa in self.farms.values()]
            json.dump(fli, fs, indent=3)

    def add_farm(self, farm: Farm):
        self.farms[farm.position] = farm

    def remove_farm(self, pos: tuple[int]):
        if pos in self.farms:
            return self.farms.pop(pos)

    def get_farm(self, pos: tuple[int]):
        return self.farms[pos]

    def generator(self):
        for x in self.farms.values():
            yield x

    def __iter__(self):
        return self.generator()


if __name__ == '__main__':
    import farms_positions
    farmlist = [Farm(position=x) for x in farms_positions.farms]
    db = FarmsDb('FarmsDb.json', farms_list=farmlist)
    db.save()
  
