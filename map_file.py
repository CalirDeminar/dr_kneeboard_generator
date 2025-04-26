import csv
import math
from PIL import Image


class MapFile:
    # string
    name = None
    # string
    filename = None
    # dict - (number, number) - (number, number)
    # (lat, long), (x, y)
    coordinate_map = None
    mag_var = 0

    def __init__(self, dcs_map_name):
        self.name = dcs_map_name
        self.filename = "./data/%s/map.jpg" % dcs_map_name
        self.coordinate_map = import_pixel_map(dcs_map_name)

    def get_map_image(self):
        return Image.open("./data/%s/map.jpg" % self.name)

    def get_pixels_for(self, lat, long):
        (lat_d, lat_m, lat_s) = lat
        (long_d, long_m, long_s) = long
        (start_x, start_y) = self.coordinate_map[(lat[0], long[0])]
        (lat_multipliers, long_multipliers) = self.get_translation_multipliers_for(lat, long)

        y_offset = (lat_m * lat_multipliers[1] / 60) + \
                   (long_m * long_multipliers[1] / 60) + \
                   (lat_s * lat_multipliers[1] / 3600) + \
                   (long_s * long_multipliers[1] / 3600)

        x_offset = (lat_m * lat_multipliers[0] / 60) + \
                   (long_m * long_multipliers[0] / 60) + \
                   (lat_s * lat_multipliers[0] / 3600) + \
                   (long_s * long_multipliers[0] / 3600)

        return math.floor(start_x + x_offset), math.floor(start_y + y_offset)

    def get_nearest_lat_long(self, lat, long, inclusive=True, inverted=False):
        available_lats = list(set(map(lambda k: k[0], self.coordinate_map.keys())))
        available_longs = list(set(map(lambda k: k[1], self.coordinate_map.keys())))
        if not inclusive:
            available_lats = list(filter(lambda i: i != lat[0], available_lats))
            available_longs = list(filter(lambda i: i != long[0], available_longs))

        if inverted:
            available_lats.reverse()
            available_longs.reverse()

        available_lats.sort(key=lambda i: abs(lat[0]-i))
        available_longs.sort(key=lambda i: abs(long[0] - i))

        return available_lats[0], available_longs[0]

    def get_translation_multipliers_for(self, lat, long, debug=False):
        (lat_1, long_1) = self.get_nearest_lat_long(lat, long)
        (lat_2, long_2) = self.get_nearest_lat_long(lat, long, inclusive=False, inverted=True)

        delta_lat = lat_2 - lat_1
        delta_long = long_2 - long_1

        pixels_1 = self.coordinate_map[(lat_1, long_1)]
        pixels_2_lat = self.coordinate_map[(lat_2, long_1)]
        pixels_2_long = self.coordinate_map[(lat_1, long_2)]

        pixel_delta_per_lat_d = (
            math.floor((pixels_2_lat[0] - pixels_1[0])/delta_lat),
            math.floor((pixels_2_lat[1] - pixels_1[1])/delta_lat),
        )
        pixels_delta_per_long_d = (
            math.floor((pixels_2_long[0] - pixels_1[0]) / delta_long),
            math.floor((pixels_2_long[1] - pixels_1[1]) / delta_long),
        )
        return pixel_delta_per_lat_d, pixels_delta_per_long_d


def import_pixel_map(dcs_map_name):
    output = {}
    filename = "./data/%s/map.csv" % dcs_map_name
    with open(filename, newline='') as csv_file:
        reader = csv.reader(csv_file, delimiter=',', quotechar='|')
        for i, row in enumerate(reader):
            if i > 0:
                if len(row) < 4:
                    raise Exception("Invalid Coordinate Map")
                output[(int(row[0].strip()), int(row[1].strip()))] =\
                    (int(row[2].strip()), int(row[3].strip()))
    return output


if __name__ == '__main__':
    test_map = MapFile("caucasus")
    test_map.get_nearest_lat_long((44, 0, 0), (39, 0, 0))
    test_map.get_nearest_lat_long((41, 0, 0), (39, 0, 0))
    test_map.get_nearest_lat_long((41, 0, 0), (39, 0, 0), False)
    print(test_map.get_pixels_for((41, 0, 0), (39, 0, 0)))
