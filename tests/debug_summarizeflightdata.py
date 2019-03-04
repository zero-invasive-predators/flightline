import arcpy
from flightline import flightline_project
import os
import datetime
import time

global_flightline = flightline_project.FlightlineProject('')


mxd_path = r'E:\\temp\\afl7\\MasterMap.mxd'
helicopter_rego = 'YYY'
tracmap_data = r"C:\Users\braaksman\Downloads\DOC\Baitapplicationtoxic\ISK\0951\Broardcast"
mxd = arcpy.mapping.MapDocument(mxd_path)
df = arcpy.mapping.ListDataFrames(mxd, "*")[0]

global_flightline.__load_project_folder__(os.path.dirname(mxd_path))
if global_flightline.valid_project_folder:
    if global_flightline.projectconfig_json_exists:
        global_flightline.load_from_projectconfig()


def setup_parameters():
    # parameter 0
    flightline_gdb = arcpy.Parameter(
                displayName="Flightline Data Gdb",
            name="in_workspace",
            datatype="DEWorkspace",
            parameterType="Optional",
            direction="Input")

    flightline_gdb.value = global_flightline.flight_data_gdb_location
    # Set the filter to accept only local (personal or file) geodatabases
    flightline_gdb.filter.list = ["Local Database"]

    parameters = []
    parameters.append(flightline_gdb)
    return parameters

parameters = setup_parameters()
parameters[0].value = None