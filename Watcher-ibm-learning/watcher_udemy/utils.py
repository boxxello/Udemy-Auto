import json
import os
import random

import validators

def get_app_dir() -> str:
    """
    Gets the app directory where all data related to the script is stored

    :return:
    """

    app_dir = os.path.join(os.path.expanduser("~"), ".watcher_udemy")
    print(app_dir)
    if not os.path.isdir(app_dir):
        # If the app data dir does not exist create it
        os.mkdir(app_dir)
    return app_dir

def read_urls_from_file(file_name):
    with open(file_name, "r") as f:
        lines= f.read().splitlines()
    list_of_urls = []
    for line in lines:
        if validators.url(line):
            list_of_urls.append(line)
    return list_of_urls

def generate_9_digit_random_number()->int:
    n = 9
    return int(''.join(["{}".format(random.randint(0, 9)) for _ in range(0, n)]))

def validateJSON(jsonData: str)->tuple:
    try:
        loaded_json=json.loads(jsonData)
    except ValueError:
        return False, None
    except BaseException:
        return False, None
    return True, loaded_json

