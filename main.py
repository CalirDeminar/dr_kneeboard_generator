import sys
import os
from route import Route
from map_file import find_map_from_wp
from tot_planner import parse_time


def main():
    route_name = sys.argv[1]
    route_file = "./data/routes/%s.csv" % route_name
    # Args 2 and 3 are either ToT and blank or Start Time and ToT
    start_time = (0, 0, 0)
    time_on_target = None
    if len(sys.argv) > 3:
        start_time = parse_time(sys.argv[2])
        time_on_target = parse_time(sys.argv[3])
    if len(sys.argv) > 2:
        time_on_target = parse_time(sys.argv[2])
    if not os.path.exists(route_file):
        raise Exception("%s route file not found" % route_name)

    route = Route(route_name, start_time, time_on_target)
    if not os.path.exists("./" + route_name):
        os.mkdir("./" + route_name)
    route.save_boards()


if __name__ == '__main__':
    main()
