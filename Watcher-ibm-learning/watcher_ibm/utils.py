import os
import validators

def get_app_dir() -> str:
    """
    Gets the app directory where all data related to the script is stored

    :return:
    """

    app_dir = os.path.join(os.path.expanduser("~"), ".watcher_ibm")
    print(app_dir)
    if not os.path.isdir(app_dir):
        # If the app data dir does not exist create it
        os.mkdir(app_dir)
    return app_dir

def read_file(file_name):
    with open(file_name, "r") as f:
        lines= f.read().splitlines()
    list_of_urls = []
    for line in lines:

        if validators.url(line):
            list_of_urls.append(line)
    return list_of_urls


