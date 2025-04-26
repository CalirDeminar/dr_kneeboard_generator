import csv
import math
from waypoint import WayPoint
from map_file import MapFile
from tot_planner import get_waypoint_times
import PIL
from PIL import ImageDraw
PIL.Image.MAX_IMAGE_PIXELS = 10000000000

aspect_ratio = 6 / 4
# ratio of leg length we want the board height to be
margin_ratio = 1.25

waypoint_circle_radius_ratio = 0.06
waypoint_circle_width_ratio = 0.008
waypoint_circle_max_rad = 100
waypoint_circle_max_width = 20


class Route:
    name = None
    map = None
    waypoints = []
    start_time = None
    time_on_target = None
    cruise_speed = None
    dash_speed = 500

    def __init__(self, route_name, dcs_map_name, start_time=(0, 0, 0), time_on_target=None):
        route_filename = "./data/routes/%s.csv" % route_name

        with open(route_filename, newline='') as csv_file:
            reader = csv.reader(csv_file, delimiter=',', quotechar='|')
            for i, record in enumerate(reader):
                if i > 0:
                    self.waypoints.append(WayPoint(record, i-1))
        self.name = route_name
        self.map = MapFile(dcs_map_name)
        self.start_time = start_time
        self.time_on_target = time_on_target
        for wp in self.waypoints:
            if wp.index > 0:
                prev = self.waypoints[wp.index-1]
                wp.bearing_from_last = wp.bearing_from(prev)
                wp.distance_from_last = wp.distance_from(prev)
            if wp.index < len(self.waypoints)-1:
                next_wp = self.waypoints[wp.index + 1]
                wp.bearing_to_next = next_wp.bearing_from(wp)
        # tot
        [target_wp] = [x for x in self.waypoints if "TGT" in x.tags]
        timed_route = self.waypoints[0:target_wp.index+1]

        distances = list(map(lambda wp: wp.distance_from_last, timed_route))
        (times, speed) = get_waypoint_times(distances, self.start_time, self.time_on_target, self.dash_speed)
        self.cruise_speed = speed
        for i, time in enumerate(times):
            if i <= len(self.waypoints):
                self.waypoints[i].time = time
                self.waypoints[i].speed = speed
                if i == len(self.waypoints)-1:
                    self.waypoints[i].speed = self.dash_speed

    def kneeboard_width_for_wp_index(self, i, min_width=800, min_height=1200):
        if i < 1:
            return min_width, min_height
        current = self.waypoints[i]
        prev = self.waypoints[i-1]

        (x_cur, y_cur) = self.map.get_pixels_for(current.lat, current.long)
        (x_prev, y_prev) = self.map.get_pixels_for(prev.lat, prev.long)

        height = math.sqrt((x_prev - x_cur) ** 2 + (y_prev - y_cur) ** 2) * margin_ratio
        width = height * (1 / aspect_ratio)

        if height < min_height:
            return 800, 1200

        return width * margin_ratio, height * margin_ratio

    def draw_for_wp_index(self, index, draw, circle_radius, line_width):
        wp = self.waypoints[index]
        (x, y) = self.map.get_pixels_for(wp.lat, wp.long)
        draw.ellipse(
            (
                (x - circle_radius, y - circle_radius),
                (x + circle_radius, y + circle_radius)
            ),
            (0, 0, 0, 0),
            (0, 0, 0, 255),
            line_width
        )

    def draw_route_for_wp_from_prev(self, index, draw, circle_radius, line_width):
        if index > 0:
            wp = self.waypoints[index]
            prev = self.waypoints[index-1]

            (x, y) = self.map.get_pixels_for(wp.lat, wp.long)
            (x_prev, y_prev) = self.map.get_pixels_for(prev.lat, prev.long)

            angle = math.atan2(y_prev - y, x_prev - x)

            draw.line(
                (
                    (x_prev - (circle_radius * math.cos(angle)), y_prev - (circle_radius * math.sin(angle))),
                    (x + (circle_radius * math.cos(angle)), y + (circle_radius * math.sin(angle)))
                ),
                (0, 0, 0),
                line_width
            )

    def crop_board_for_wp(self, index, img):
        wp = self.waypoints[index]
        (x, y) = self.map.get_pixels_for(wp.lat, wp.long)
        (board_width, board_height) = self.kneeboard_width_for_wp_index(index)
        local_img = img
        if index > 0:
            prev = self.waypoints[index - 1]
            (x_prev, y_prev) = self.map.get_pixels_for(prev.lat, prev.long)

            x_centre = math.floor((x + x_prev) / 2)
            y_centre = math.floor((y + y_prev) / 2)

            bearing_from_prev = math.degrees(math.atan2(y - y_prev, x - x_prev)) + 90

            local_img = img.rotate(bearing_from_prev, center=(x_centre, y_centre))

            return local_img.crop((
                x_centre - board_width / 2,
                y_centre - board_height / 2,
                x_centre + board_width / 2,
                y_centre + board_height / 2
            ))

        return img.crop((
            x - (board_width / 2),
            y - (board_height / 2),
            x + (board_width / 2),
            y + (board_height / 2)
        ))

    def add_doghouse_for_wp(self, index, img):
        wp = self.waypoints[index]
        draw = ImageDraw.Draw(img, 'RGBA')
        font_height = get_font_size(img)

        margin = math.floor(font_height * 0.5)

        heading = "N/A"
        if index > 0:
            prev = self.waypoints[index-1]
            heading = "%s°" % (wp.bearing_from(prev)-self.map.mag_var)
        next_heading = "N/A"

        if index < len(self.waypoints)-1:
            next_wp = self.waypoints[index+1]
            next_heading = "%s°" % (next_wp.bearing_from(wp)-self.map.mag_var)

        distance = "N/A"
        if wp.distance_from_last is not None:
            distance = "%snm" % round(wp.distance_from_last, 1)

        time = "N/A"
        if wp.time is not None:
            hours = ("%s" % wp.time[0]).zfill(2)
            minutes = ("%s" % wp.time[1]).zfill(2)
            seconds = ("%s" % wp.time[2]).zfill(2)
            time = f"{hours}:{minutes}:{seconds}"

        speed = "N/A"
        if wp.speed is not None:
            speed = "%skts" % wp.speed

        lines = [
            ("WP:", wp.name),
            ("MC:", heading),
            ("DIST:", distance),
            ("ETE:", time),
            ("TAS:", speed),
            ("NMC:", next_heading)
        ]

        headings_width = max(map(lambda j: draw.textlength(j[0], font_size=font_height), lines))
        values_width = max(map(lambda j: draw.textlength(j[1], font_size=font_height), lines))
        column_space = img.width * 0.005

        # background_x_min = math.floor(img.width*0.66)
        background_x_min = 0
        # background_base = (img.height*0.33)
        background_base = img.height - (len(lines) * (font_height + margin))
        background_width = math.floor(headings_width + values_width + column_space + margin*2)
        line_width = math.floor(img.width*0.004)

        draw.polygon(
            [
                (background_x_min, background_base),
                (background_x_min + background_width, background_base),
                (background_x_min + background_width, background_base + (font_height+margin)*len(lines)),
                (background_x_min, background_base + (font_height+margin)*len(lines)),
            ],
            (0, 0, 0, 255),
            (255, 255, 255, 200),
            width=line_width
        )

        for i, (heading, value) in enumerate(lines):
            height = background_base + ((margin + font_height) * i)
            draw.line(
                [
                    (background_x_min, height),
                    (background_x_min + background_width, height)
                ],
                (255, 255, 255, 200),
                width=line_width
            )
            draw.text(
                (background_x_min + margin, height + margin/3),
                heading,
                # font=font,
                align="left",
                fill="white",
                font_size=font_height
            )
            draw.text(
                (background_x_min + margin + headings_width + column_space, height + margin/3),
                value,
                # font=font,
                align="left",
                fill="white",
                font_size=font_height
            )
        return img

    def create_board_for_wp(self, index):
        img = self.map.get_map_image()
        draw = ImageDraw.Draw(img, "RGBA")
        (board_height, board_width) = self.kneeboard_width_for_wp_index(index)
        circle_radius = min(math.floor(board_width * waypoint_circle_radius_ratio), waypoint_circle_max_rad)
        line_width = min(math.floor(board_width * waypoint_circle_width_ratio), waypoint_circle_max_width)
        for i, wp in enumerate(self.waypoints):
            self.draw_for_wp_index(i, draw, circle_radius, line_width)
            self.draw_route_for_wp_from_prev(i, draw, circle_radius, line_width)
        return img

    def save_boards(self):
        for i, wp in enumerate(self.waypoints):
            board = self.create_board_for_wp(i)
            cropped_board = self.crop_board_for_wp(i, board)
            annotated_board = self.add_doghouse_for_wp(i, cropped_board)
            annotated_board.save("./%s/%s-wp%s.jpg" % (self.name, self.map.name, i+1))

        full_board = self.create_board_for_wp(i)
        full_board.save("./%s/%s-Overview.jpg" % (self.name, self.map.name))


def get_font_size(img):
    line_height_ratio = 0.02
    return math.floor(line_height_ratio * img.height)


if __name__ == "__main__":
    Route("example", "caucasus", (0, 0, 0), (0, 30, 0)).save_boards()
