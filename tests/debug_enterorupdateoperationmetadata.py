import arcpy
from flightline import flightline_project
import os

global_flightline = flightline_project.FlightlineProject('')

mxd_path = r"E:\temp\afl7\MasterMap.mxd"
mxd = arcpy.mapping.MapDocument(mxd_path)
df = arcpy.mapping.ListDataFrames(mxd, '*')[0]

v_operation_start_time = '0910'
v_helicopter_rego = 'YYY'

global global_flightline
global_flightline.__load_project_folder__(os.path.dirname(mxd_path))
if global_flightline.valid_project_folder:
    if global_flightline.projectconfig_json_exists:
        global_flightline.load_from_projectconfig()


def getParameterInfo():
    """Defin parameter definitions"""

    global_flightline.load_tool_setting_json_files()

    params = []

    # parameter 0
    local_gdb = arcpy.Parameter(name="local_gdb",
                                    displayName="File Geodatabase where the processed data from the helicopter will be stored",
                                direction="Input",
                                   datatype="DEWorkspace",
                                   parameterType="Required")
    local_gdb.filter.list = ["Local Database"]
    local_gdb.value = global_flightline.flight_data_gdb_location
    params.append(local_gdb)

    # parameter 1
    operation_start_time = arcpy.Parameter(name="operation_start_time",
                                               displayName="Enter the time the operation went 'Toxic' i.e 0910",
                                               direction="Input",
                                              datatype="GPString",
                                              parameterType="Optional")
    params.append(operation_start_time)

    # parameter 2
    helicopter_info = arcpy.Parameter(name="helicopter_info",
                                          displayName="Enter the helicopter registration number",
                                          direction="Input",
                                         datatype="GPValueTable",
                                         parameterType="Optional")

    # Set Parameter Values, note that the names (if extracing from config json) here should be exactly the same as in the config json files
    helicopter_info.columns = [["GPString","RegNo"], ["GPString","Pilot Name"], ["GPString","HelicopterTypes"], ["Long","Bucket Size (Kg)"],["Double","Sow rate (Kg/ha)"]]
    #helicopter_info.columns.append(["Double","Sow rate (Kg/ha)"])
    helicopter_info.filters[2].type = "ValueList"
    helicopter_info.filters[3].type = "ValueList"
    helicopter_info.filters[4].type = "ValueList"
    helicopter_info.filters[2].list = global_flightline.get_config_attribute("HelicopterTypes")
    helicopter_info.filters[3].list = global_flightline.get_config_attribute("BucketSizes")
    helicopter_info.filters[4].list = global_flightline.get_config_attribute("SowRates")
    params.append(helicopter_info)

    return params

parameters = getParameterInfo()
parameters[1].value = v_operation_start_time
parameters[2].value = v_helicopter_rego

operation_start_time = parameters[1].valueAsText
helicopter_info = parameters[2].value

global_flightline.operation_start_time = parameters[1].valueAsText
global_flightline.set_operation_start_date_time()

if operation_start_time:
    if global_flightline.operation_times_table_records:
        arcpy.AddWarning("{0} can only contain 1 start time entry. Existing entrys will be deleted".format(global_flightline.operation_times_table))
        arcpy.DeleteFeatures_management(global_flightline.operation_times_table)
    with arcpy.da.InsertCursor(global_flightline.operation_times_table, ['Operation_Start_Time']) as insert_cursor:
        insert_cursor.insertRow([global_flightline.operation_start_datetime])
    arcpy.AddMessage("{0} added to {1}".format(global_flightline.operation_start_datetime, global_flightline.operation_times_table))

heli_info_field_names = [heli.name for heli in arcpy.ListFields(global_flightline.helicopter_info_table)]

if helicopter_info:
    with arcpy.da.InsertCursor(global_flightline.helicopter_info_table, heli_info_field_names[1:]) as insert_cursor:
        for heli in helicopter_info:
            insert_cursor.insertRow(heli)
    arcpy.AddMessage("Helicopter info added to {0}".format(global_flightline.helicopter_info_table))