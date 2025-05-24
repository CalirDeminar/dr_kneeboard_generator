import math


# returns shape (Speed, hold_time_hrs) or None
def find_speed_and_hold(distances, dash_speed, time_hrs, min_cruise_speed=360):
    if time_hrs is None:
        return 420, 0
    distances = list(map(lambda i:  0 if i is None else i, distances))
    cruise = distances[0:-1]
    dash_distance = distances[-1]
    cruise_distance = sum(cruise)

    dash_duration = (dash_distance/dash_speed)
    cruise_time = time_hrs-dash_duration
    speed_options = [240, 300, 360, 420, 490, 560]
    available_speeds = list(filter(lambda s: s >= min_cruise_speed, speed_options))
    speed_times = list(filter(
        lambda t: t < cruise_time,
        list(map(lambda s: cruise_distance/s, available_speeds))
    ))
    best_time = speed_times[0]
    hold = time_hrs - best_time - dash_duration
    return math.floor(cruise_distance/best_time), hold


def get_waypoint_times(distances, start_time, time_on_target, dash_speed=500, min_cruise_speed=300):
    print("Start: %s", start_time)
    print("TOT: %s", time_on_target)

    duration_hrs = None
    if time_on_target is not None:
        duration_hrs = (time_on_target[0] - start_time[0]) +\
                       ((time_on_target[1] - start_time[1])/60) +\
                       ((time_on_target[2] - start_time[2])/3600)

    speed_attempt = find_speed_and_hold(distances, dash_speed, duration_hrs, min_cruise_speed)
    if speed_attempt is None:
        raise Exception("No valid speed for this route")
    (speed, hold) = speed_attempt
    output = []
    total_time = hold
    for i, distance in enumerate(distances):
        if i == 0:
            output.append(hours_to_time(total_time))
        elif i == (len(distances)-1):
            total_time += (distance / dash_speed)
            output.append(hours_to_time(total_time))
        elif distance is not None:
            total_time += (distance/speed)
            output.append(hours_to_time(total_time))
        else:
            output.append(None)
    return output, speed


def parse_time(time):
    splits = time.split(":")
    if len(splits) != 3:
        raise Exception("%s is not a valid time")
    return int(splits[0].strip()), int(splits[1].strip()), int(splits[2].strip())


def hours_to_time(t):
    hours = math.floor(t)
    minutes = math.floor((t-hours)*60)
    seconds = math.floor(((t*60)-(hours*60)-minutes)*60)
    return hours, minutes, seconds


def time_to_minutes(t):
    seconds = t[2]/60
    minutes = t[1]
    hours = t[0]*60
    return seconds + minutes + hours


if __name__ == '__main__':
    print(hours_to_time(1.504))