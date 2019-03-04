import arcpy
from flightline import flightline_project
import os

global_flightline = flightline_project.FlightlineProject('')

mxd_path = r'E:\\temp\\afl7\\MasterMap.mxd'
v_new_gdb_name = "DebugGDB"
global_flightline.__load_project_folder__(os.path.dirname(mxd_path))
if global_flightline.valid_project_folder:
    if global_flightline.projectconfig_json_exists:
        global_flightline.load_from_projectconfig()

def setup_parameters():
    # parameter 0
    project_directory = arcpy.Parameter(
        displayName = 'Directory of the aerial project',
        name = 'project_directory',
        datatype = 'DEFolder',
        parameterType = 'Required',
        direction = 'Input')

    if global_flightline.valid_project_folder:
        project_directory.value = global_flightline.project_folder

    # parameter 1
    new_gdb_name = arcpy.Parameter(
        displayName = 'Name of the new file geodatabase',
        name = 'new_gdb_name',
        datatype = 'GPString',
        parameterType = 'Required',
        direction = 'Input')

    parameters = []
    parameters.append(project_directory)
    parameters.append(new_gdb_name)
    return parameters

parameters = setup_parameters()
parameters[1].value = v_new_gdb_name


project_directory = parameters[0].valueAsText
new_gdb_name = parameters[1].valueAsText + '.gdb'

# Delete out GDB if it already exists
try:
    arcpy.Delete_management(in_data=os.path.join(project_directory,new_gdb_name))
except Exception:
    print("No GDB to delete")

global_flightline.add_new_flight_data_gdb_name(new_gdb_name)

# Create new gdb and generate required tables/featureclasses
global_flightline.create_flight_data_gdb(new_gdb_name)

# Any time a field is changed, update the projectconfig.json
global_flightline.dump_to_projectconfig()