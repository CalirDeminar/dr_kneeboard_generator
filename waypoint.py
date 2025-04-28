import math
import haversine
from haversine import Unit


class WayPoint:
    name = None
    index = None
    lat = None
    long = None
    x_pixel = None
    y_pixel = None
    bearing_from_last = None
    bearing_to_next = None
    distance_from_last = None
    time = None
    tags = []
    speed = None
    min_alt=None

    def __init__(self, string_list_to_parse, index):
        if len(string_list_to_parse) < 7:
            raise Exception("Invalid Way Point List Line")
        lat = (
            int(string_list_to_parse[1].strip()),
            int(string_list_to_parse[2].strip()),
            int(string_list_to_parse[3].strip())
        )
        long = (
            int(string_list_to_parse[4].strip()),
            int(string_list_to_parse[5].strip()),
            int(string_list_to_parse[6].strip())
        )
        self.name = string_list_to_parse[0]
        self.lat = lat
        self.long = long
        self.index = index
        taggables = list(map(lambda i: i.strip(), string_list_to_parse[7:]))
        digit_tags = list(
            filter(
                lambda i: i.isdigit(),
                taggables
            )
        )
        if len(digit_tags) > 0:
            self.min_alt = int(digit_tags[0])
        self.tags = list(
            filter(
                lambda i: not i.isdigit(),
                taggables
            )
        )

    def bearing_from(self, previous):
        own_lat = math.radians(self.lat[0] + (self.lat[1]/60) + (self.lat[2]/3600))
        own_long = math.radians(self.long[0] + (self.long[1]/60) + (self.long[2]/3600))

        prev_lat = math.radians(previous.lat[0] + (previous.lat[1]/60) + (previous.lat[2]/3600))
        prev_long = math.radians(previous.long[0] + (previous.long[1]/60) + (previous.long[2]/3600))

        x = math.cos(prev_lat) * math.sin(prev_long-own_long)
        y = math.cos(own_lat) * math.sin(prev_lat) - math.sin(own_lat) * math.cos(prev_lat) * math.cos(prev_long-own_long)
        output_rad = math.atan2(x, y)

        return math.floor((math.degrees(output_rad) + 180) % 360)

    def to_degrees(self):
        return (
            self.lat[0] + (self.lat[1]/60) + (self.lat[2]/3600),
            self.long[0] + (self.long[1]/60) + (self.long[2]/3600)
        )

    def distance_from(self, wp):
        return haversine.haversine(self.to_degrees(), wp.to_degrees(), unit=Unit.NAUTICAL_MILES)
