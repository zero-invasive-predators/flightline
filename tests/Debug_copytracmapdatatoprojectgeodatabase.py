import arcpy
from flightline import flightline_project
import os
import time

global_flightline = flightline_project.FlightlineProject('')


mxd_path = r'E:\\temp\\afl7\\MasterMap.mxd'
v_helicopter_rego = 'YYY'
v_tracmap_data = r"C:\Users\braaksman\Downloads\DOC\Baitapplicationtoxic\ISK\0951\Broardcast"
v_treatment_area_fc = r'E:\temp\afl7\Planning.gdb\AerialBoundary'
v_download_time = '0600'
mxd = arcpy.mapping.MapDocument(mxd_path)
df = arcpy.mapping.ListDataFrames(mxd, "*")[0]

global_flightline.__load_project_folder__(os.path.dirname(mxd_path))
if global_flightline.valid_project_folder:
    if global_flightline.projectconfig_json_exists:
        global_flightline.load_from_projectconfig()


def setup_parameters():

    # parameter 0
        data_source_location = arcpy.Parameter(
            displayName = 'Drive or folder containing the Tracmap data to copy',
            name = 'data_source_location',
            datatype = 'DEWorkspace',
            parameterType = 'Required',
            direction = 'Input')

        # parameter 1
        tracmap_coordinate_system = arcpy.Parameter(
            displayName = 'Coordinate system of Tracmap data',
            name = 'coordinate_system',
            datatype = 'GPCoordinateSystem',
            parameterType = 'Required',
            direction = 'Input')
        if global_flightline.valid_project_folder:
            tracmap_coordinate_system.value = global_flightline.default_tracmap_data_projection_system

        # parameter 2
        destination_parent_directory = arcpy.Parameter(
            displayName = 'Parent directory where the raw Tracmap data will be stored',
            name = 'destination_parent_directory',
            datatype = 'DEFolder',
            parameterType = 'Required',
            direction = 'Input')
        if global_flightline.valid_project_folder:
            destination_parent_directory.value = global_flightline.tracmap_data_folder_location

        # parameter 3
        flightline_gdb = arcpy.Parameter(
            displayName="File geodatabase where the processed data from the helicopter will be stored",
            name="flightline_gdb",
            datatype="DEWorkspace",
            parameterType="Optional",
            direction="Input")
        if global_flightline.valid_project_folder:
            flightline_gdb.value = global_flightline.flight_data_gdb_location
        # Set the filter to accept only local (personal or file) geodatabases
        flightline_gdb.filter.list = ["Local Database"]

        # parameter 4
        treatment_area_featureclass = arcpy.Parameter(
            displayName = 'Feature class containing the treatment area blocks',
            name = 'treatment_area_featureclass',
            datatype = 'DEFeatureClass',
            parameterType = 'Optional',
            direction = 'Input')
        if global_flightline.valid_project_folder:
            treatment_area_featureclass.value = global_flightline.treatment_area_featureclass
        # Set the filter to only accept polygon feature classes
        treatment_area_featureclass.filter.list = ['Polygon']

        # parameter 5
        helicopter_reg_number = arcpy.Parameter(
            displayName = 'Helicopter Reg No',
            name = 'helicopter_reg_no',
            datatype = 'String',
            parameterType = 'Optional',
            direction = 'Input')
        if global_flightline.valid_project_folder:
            helicopter_reg_number.filter.list = sorted(global_flightline.helicopter_regno_list)

        # parameter 6
        download_time = arcpy.Parameter(
            displayName = 'Download time (defaults to current time)',
            name = 'download_time',
            datatype = 'String',
            parameterType = 'Required',
            direction = 'Input')
        download_time.value = time.strftime('%H%M')

        # parameter 7
        deflector_chkbox = arcpy.Parameter(
            displayName = 'Deflector bucket in use - this bucket spreads bait to the right side only',
            name = 'deflector_chkbox',
            datatype = 'GPBoolean',
            parameterType = 'Optional',
            direction = 'Input')
        deflector_chkbox.enabled = False

        parameters = []
        parameters.append(data_source_location) # Parameter 0
        parameters.append(tracmap_coordinate_system) # Parameter 1
        parameters.append(destination_parent_directory) # Parameter 2
        parameters.append(flightline_gdb) # Parameter 3
        parameters.append(treatment_area_featureclass) # Parameter 4
        parameters.append(helicopter_reg_number) # Parameter 5
        parameters.append(download_time) # Parameter 6
        parameters.append(deflector_chkbox) # Parameter 7

        return parameters


parameters = setup_parameters()
parameters[0].value = v_tracmap_data
parameters[4].value = v_treatment_area_fc
parameters[5].value = v_helicopter_rego
parameters[6].value = v_download_time

# Set variables
source_directory = parameters[0].valueAsText
treatment_area_fc = parameters[4].valueAsText
helicopter_rego = parameters[5].valueAsText

global_flightline.treatment_area_featureclass = treatment_area_fc

coordinate_system_text = parameters[1].value
coordinate_system = arcpy.SpatialReference(text="{0}".format(coordinate_system_text))
global_flightline.__tracmap_data_projection__ = coordinate_system.factoryCode

destination_tracmap_directory = global_flightline.tracmap_data_folder_location

helicopter_rego = parameters[5].valueAsText
download_time = parameters[6].valueAsText
deflector_chkbx = parameters[7].value

sum_total_fieldnames = global_flightline.sum_total_fieldnames

arcpy.env.geographicTransformations = 'NZGD_2000_To_WGS_1984_1'

project_folder_handler = global_flightline.project_folder_handler

# Copy the tracmap data from directory to project folder
if not global_flightline.copy_tracmap_data(source_directory, helicopter_rego, download_time):
    arcpy.AddError("{0} already exists, change download time".format(os.path.join(global_flightline.tracmap_data_folder_location, helicopter_rego, download_time)))

# Add layer files to current map document
global_flightline.add_copied_data_to_mxd(mxd, df)

# Copy new rows in the log shapefiles to the totalLines feature class
global_flightline.merge_tracmap_data_to_flight_data_gdb('log.shp',
                                                        os.path.join(global_flightline.tracmap_data_folder_location, helicopter_rego, download_time),
                                                        global_flightline.total_lines_fc,
                                                        coordinate_system)

# Update total_lines with the Machine and DL_Times etc - make sure 'Buffer is not empty
result = global_flightline.update_total_lines_featureclass(helicopter_rego, download_time, deflector_chkbx)
if not result:
    raise Exception("There are no new records to add")

# Copy new rows in the secondary shapefiles to the totalPoints featureclass
global_flightline.merge_tracmap_data_to_flight_data_gdb('secondary.shp',
                                                            os.path.join(global_flightline.tracmap_data_folder_location, helicopter_rego, download_time),
                                                            global_flightline.total_points_fc,
                                                            coordinate_system)
result = global_flightline.update_total_points_featureclass(helicopter_rego, download_time, deflector_chkbx)

# Convert the secondary points to lines
records_added = global_flightline.covert_secondary_points_to_lines(helicopter_rego, download_time)
arcpy.AddMessage("{0} new reocrds added from {1}".format(records_added, source_directory))

# Summarize new flight data
summary_result = global_flightline.summarize_new_flight_data(helicopter_rego, download_time, df)

if summary_result:
    arcpy.AddMessage("Summary Results Calculated and added to {0}.\n{1} created".format(global_flightline.flightline_sum_totals_table, summary_result))
else:
    arcpy.AddMessage("No new rows added to summary table")

global_flightline.dump_to_projectconfig()
