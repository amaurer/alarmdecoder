import yaml


class ZoneMapper(object):



    def __init__(self, pathtofile):

        self.zone_map = {}

        with open(pathtofile) as filestream:

            try:
                self.zone_map = yaml.load(filestream)
            except yaml.YAMLError as exc:
                print(exc)




    def get_zone_name(self, zone):
        found_zone = "Zone Not Found!"
        try:

            found_zone = self.zone_map["Zone" + str(zone)]
        except Exception as e:
            print(e)
            raise

        return found_zone





    def is_zone_whitelist(self, zone):
        return zone in self.zone_map["ZoneAlertWhiteList"]