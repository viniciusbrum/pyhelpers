# sensors.py - helpers for monitoring sensors temperature on Linux

import datetime
import json
import subprocess
import time


def get_sensor_temp(sensor_desc: str) -> float:
    """
    Get sensor temperature.

    :param sensor_desc: sensor's description
    :raise ValueError: if sensor or temperature data was not found
    :return: sensor temperature
    """
    cp = subprocess.run(['sensors', '-Aj'], capture_output=True)
    sensors2data = json.loads(cp.stdout)
    try:
        data = sensors2data[sensor_desc]
    except KeyError:
        raise ValueError(f'sensor "{sensor_desc}" not found')
    try:
        return data['edge']['temp1_input']
    except KeyError:
        raise ValueError('temperature data not found for sensor "{sensor_desc}"')


def monitor_sensor_temp(sensor_desc: str, max_temp: float, secs: int,
                        num_measures: int) -> None:
    """
    Periodically check sensor temperature.

    :param sensor_desc: sensor's description
    :param max_temp: maximum temperature allowed
    :param secs: seconds between measurements
    :param num_measures: number of measurements
    :raise ValueError: if sensor or temperature data was not found
    """
    max_temp = float(max_temp)
    secs = int(secs)
    num_measures = int(num_measures)
    cont = 1
    while cont <= num_measures:
        temp = get_sensor_temp(sensor_desc)
        pref = (f'{datetime.datetime.now().strftime("%y-%m-%d %H:%M:%S")}'
                f' [{cont}/{num_measures}] sensor "{sensor_desc}"')
        if temp > max_temp:
            print(f'{pref} is up to {max_temp}° ({temp})')
        else:
            print(f'{pref} is ok')
        cont += 1
        time.sleep(secs)


if __name__ == '__main__':
    import sys
    main(*sys.argv[1:])
