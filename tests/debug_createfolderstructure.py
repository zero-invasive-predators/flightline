import arcpy
from flightline import flightline_project

global_flightline = flightline_project.FlightlineProject('')

v_directory_workspace = r"E:\Temp\afl7"
v_json_file = r"C:\Users\braaksman\Documents\GitHub\flightline\data\ProjectSetup.json"
v_overwrite = True

def getParameterInfo():
    """Defin parameter definitions"""

    # Parameter 0
    directory_workspace = arcpy.Parameter(name='directory_workspace',
                                              displayName='Directory Workspace',
                                             direction='Input',
                                             datatype='DEFolder',
                                             parameterType='Required',
                                             enabled=True)

    # Parameter 1
    json_file = arcpy.Parameter(name='json_file', displayName='Project Setup json file ',
                                    direction='Input',
                                   datatype='DEFile',
                                   parameterType='Required',
                                   enabled='True')

    # Parameter 2
    overwrite = arcpy.Parameter(name='overwrite',
                                    displayName="Overwrite Existing Project",
                                    direction="Input",
                                   datatype="GPBoolean",
                                   parameterType="Optional")

    overwrite.value = False
    params = []
    params.append(directory_workspace) # 0
    params.append(json_file) # 1
    params.append(overwrite) # 2
    return params


parameters = getParameterInfo()
parameters[0].value = v_directory_workspace
parameters[1].value = v_json_file
parameters[2].value = v_overwrite

directory_workspace = parameters[0].valueAsText
json_file = parameters[1].valueAsText
overwrite = parameters[2].value
global_flightline.setup_folder_structure(json_file,overwrite)

# Any time a field is changed, update the projectconfig.json
global_flightline.dump_to_projectconfig()