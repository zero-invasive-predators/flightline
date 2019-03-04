# Flightline Project

# Author: Nicholas Braaksma
# Date: 07-08-2017

# Description:
# Manages the loading and saving of the projects config file

import json

def dump_to_projectconfig(obj, json_file):
    """
    Saves the attributes of an object to the specified json file

    Parameters
    ----------
    obj : flightline_project.FlightlineProject()
    json_file : str - file location
    """

    _json_file_ = open(json_file, 'w')
    json.dump(obj.__dict__, _json_file_)
    _json_file_.close()

    return

def load_from_projectconfig(obj, json_file):
    """
    Load the attributes saved in a json file into the object

    Parameters
    ----------
    obj : flightline_project.FlightlineProject()
    json_file : str - file location
    """

    _json_file_ = open(json_file, 'r')
    json_dict = json.load(_json_file_)
    _json_file_.close()

    for a in json_dict.keys():
        setattr(obj, a, json_dict[a])

    return obj