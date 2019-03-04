import arcpy
from flightline import flightline_project
import os
import datetime
import time

global_flightline = flightline_project.FlightlineProject('')

def check_project_map_loaded():
    """Checks if the project map is loaded up"""


class Toolbox(object):
    def __init__(self):
        """Define the toolbox"""
        self.label = "Flightline Toolbox"

        # List of tool classes associated with this toolbox
        self.tools = []
        self.tools.append(CreateFolderStructure)
        self.tools.append(EnterOrUpdateOperationMetadata)
        self.tools.append(CopyTracmapDataToProjectGeodatabase)
        self.tools.append(SummarizeFlightData)
        self.tools.append(CreateNewFlightDataGdb)

        self.mxd = arcpy.mapping.MapDocument("CURRENT")
        self.map_location = self.mxd.filePath
        global global_flightline
        global_flightline = flightline_project.FlightlineProject(os.path.dirname(self.map_location))

        # if global_flightline.projectconfig_json_exists:
            # global_flightline.load_from_projectconfig()


class CreateFolderStructure(object):
    def __init__(self):
        """Define the tool"""
        self.label = "Create Folder Structure"
        self.description = "Creates a folder structure based on a predefined json file"
        self.canRunInBackground = True
        self.category = "Project Setup"

    def getParameterInfo(self):
        """Define parameter definitions"""

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
        params.append(directory_workspace) # 1
        params.append(json_file) # 2
        params.append(overwrite)
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        # Any time a field is changed, update the projectconfig.json
        #global_flightline.dump_to_projectconfig()

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""


        if not parameters[0].altered:
            return
        global_flightline.__load_project_folder__(parameters[0].valueAsText)
        if not global_flightline.project_folder_empty and not parameters[2].value:
            parameters[2].setErrorMessage("Project folder is not empty, please select new project folder or enable overwrite")

        return

    def execute(self, parameters, messages):
        """The source code of the tool."""

        directory_workspace = parameters[0].valueAsText
        json_file = parameters[1].valueAsText
        overwrite = parameters[2].value
        global_flightline.setup_folder_structure(json_file,overwrite)

        # Any time a field is changed, update the projectconfig.json
        global_flightline.dump_to_projectconfig()

        return


#-------------------------------------------------------------
# - Enter or update operation Metadata
# ------------------------------------------------------------

class EnterOrUpdateOperationMetadata(object):

    def __init__(self):
        """Define the tool"""
        self.label = "Enter or update operation metadata"
        self.description = "Enter or update info on the helicopters used in the operation"
        self.canRunInBackground = True
        self.category = "Data Management"

        mxd = arcpy.mapping.MapDocument("CURRENT")
        mxd_path = mxd.filePath

        global global_flightline
        global_flightline.__load_project_folder__(os.path.dirname(mxd_path))
        if global_flightline.valid_project_folder:
            if global_flightline.projectconfig_json_exists:
                global_flightline.load_from_projectconfig()

    def getParameterInfo(self):
        """Define parameter definitions"""
        # Check if Project Map is loaded, if not then don't load all parameters into tool and post error message
        if not global_flightline.valid_project_folder: # Only setup parameter if data is available
            error_parameter =arcpy.Parameter(name='error_parameter',
                            displayName="Please open project map saved in project folder",
                            direction="Derived",
                           datatype="GPString",
                           parameterType="Required")
            error_parameter.value = "Tool cannot be run, load the project map saved in the root of the project folder and refresh toolbox"
            return [error_parameter]

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

    def isLicensed(self):
        """Set whether tool is licensed to execute.
           An arceditor or arcinfo licence is required to fully utilise this tool, specifically
           the ImportXMLWorkspaceDocument_management function used to add the empty feature classes
           and tables to the new file geodatabase or new fc's and tables to an existing file geodatabase"""

        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        # Any time a field is changed, update the projectconfig.json
        global_flightline.dump_to_projectconfig()

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""

        if parameters[1].altered:
            start_time_text = parameters[1].valueAsText
            if len(global_flightline.operation_times_table_records) > 0:
                parameters[1].setWarningMessage('There is already an entry for this. Existing entries will be overwritten.')
            try:
                time.strptime(start_time_text, "%H%M")
            except:
                parameters[1].setErrorMessage("This is not a valid time format, shold be hhmm eg. 0910")

        if parameters[2].altered:
            reg_number = parameters[2].valueAsText
            if reg_number[3] != ' ':
                parameters[2].setErrorMessage('Helicopter Reg No. must be 3 characters only i.e. HBC')

        return

    def execute(self, parameters, messages):
        """The source code of the tool"""
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

        return

# ---------------------------------------------------------
# Copy Tracmap Data from Directory to Project Gdb
# ---------------------------------------------------------

class CopyTracmapDataToProjectGeodatabase(object):

    def __init__(self):
        """Define the tool (tool name is the name of the class"""
        self.label = "Copy Tracmap Data into Project"
        self.description = "Copy the tracmap data from the USB drive into your Aerial Project"
        self.canRunInBackground = True
        self.category = "Data Management"

        mxd = arcpy.mapping.MapDocument("CURRENT")
        mxd_path = mxd.filePath

        arcpy.env.overwriteOutput = True

        global global_flightline
        global_flightline.__load_project_folder__(os.path.dirname(mxd_path))
        if global_flightline.valid_project_folder:
            if global_flightline.projectconfig_json_exists:
                global_flightline.load_from_projectconfig()

    def getParameterInfo(self):
        """Defines parameter definitions"""

        # Check if Project Map is loaded, if not then don't load all parameters into tool and post error message
        if not global_flightline.valid_project_folder: # Only setup parameter if data is available
            error_parameter =arcpy.Parameter(name='error_parameter',
                            displayName="Please open project map saved in project folder",
                            direction="Derived",
                           datatype="GPString",
                           parameterType="Required")
            error_parameter.value = "Tool cannot be run, load the project map saved in the root of the project folder and refresh toolbox"
            return [error_parameter]

        global_flightline.load_tool_setting_json_files()

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


    def isLicensed(self):
        """"
        Set whether tool is licensed to execute.
        An advanced (arcinfo) licence is required to use this tool, specifically
        the the feature vertices to points tool used to create the secondary lines and
        the ImportXMLWorkspaceDocument_management function used to add the empty feature classes
        and tables to the new file geodatabase or new fc's and tables to an existing file geodatabase
        """
        return True

        try:
            if arcpy.ProductInfo() <> 'ArcInfo':
                raise Exception
        except Exception:
            return False
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        # Any time a field is changed, update the projectconfig.json
        global_flightline.dump_to_projectconfig()

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""

        return

    def execute(self, parameters, messages):
        """The source code for the tool"""

        # Set variables
        source_directory = parameters[0].valueAsText

        coordinate_system_text = parameters[1].value
        coordinate_system = arcpy.SpatialReference(text="{0}".format(coordinate_system_text))
        global_flightline.__tracmap_data_projection__ = coordinate_system.factoryCode
        global_flightline.treatment_area_featureclass = parameters[4].valueAsText

        destination_tracmap_directory = global_flightline.tracmap_data_folder_location

        helicopter_rego = parameters[5].valueAsText
        download_time = parameters[6].valueAsText
        deflector_chkbx = parameters[7].value

        mxd = arcpy.mapping.MapDocument("CURRENT")
        df = arcpy.mapping.ListDataFrames(mxd, "*")[0]
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
            return

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

        return


# ----------------------------------------------------------
# - Summarizes flightline data
# ----------------------------------------------------------

class SummarizeFlightData(object):

    def __init__(self):
        """Define the tool (tool name is the name of the class)"""
        self.label = "Summarize Flight Data"
        self.description = "Summarizes the flight data"
        self.canRunInBackground = True
        self.category = "Data Management"
        mxd = arcpy.mapping.MapDocument("CURRENT")
        mxd_path = mxd.filePath
        arcpy.env.overwriteOutput = True

        global global_flightline
        global_flightline.__load_project_folder__(os.path.dirname(mxd_path))
        if global_flightline.projectconfig_json_exists:
            global_flightline.load_from_projectconfig()

    def getParameterInfo(self):
        """Defines parameter definitions"""

        # Check if Project Map is loaded, if not then don't load all parameters into tool and post error message
        if not global_flightline.valid_project_folder: # Only setup parameter if data is available
            error_parameter =arcpy.Parameter(name='error_parameter',
                            displayName="Please open project map saved in project folder",
                            direction="Derived",
                           datatype="GPString",
                           parameterType="Required")
            error_parameter.value = "Tool cannot be run, load the project map saved in the root of the project folder and refresh toolbox"
            return [error_parameter]

        global_flightline.load_tool_setting_json_files()

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

    def isLicensed(self):
        """"
        Set whether tool is licensed to execute.
        An advanced (arcinfo) licence is required to use this tool, specifically
        the the feature vertices to points tool used to create the secondary lines and
        the ImportXMLWorkspaceDocument_management function used to add the empty feature classes
        and tables to the new file geodatabase or new fc's and tables to an existing file geodatabase
        """
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        # Any time a field is changed, update the projectconfig.json
        global_flightline.dump_to_projectconfig()

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""

        return


    def execute(self, parameters, messages):
        """The source code of the tool"""

        mxd = arcpy.mapping.MapDocument("CURRENT")
        df = arcpy.mapping.ListDataFrames(mxd, "*")[0]

        global_flightline.summarize_flight_data(df)

        return

# ----------------------------------------------------------
# - Create Flight Data Gdb
# ----------------------------------------------------------

class CreateNewFlightDataGdb(object):

    def __init__(self):
        """Define the tool (tool name is the name of the class)"""
        self.label = "Create New Flightdata Gdb"
        self.description = "Creates a new flightdata gdb with the required schema"
        self.canRunInBackground = True
        self.category = "Project Setup"
        mxd = arcpy.mapping.MapDocument("CURRENT")
        mxd_path = mxd.filePath
        arcpy.env.overwriteOutput = True

        global global_flightline
        global_flightline.__load_project_folder__(os.path.dirname(mxd_path))
        if global_flightline.projectconfig_json_exists:
            global_flightline.load_from_projectconfig()

    def getParameterInfo(self):
        """Defines parameter definitions"""

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

    def isLicensed(self):
        """"
        Set whether tool is licensed to execute.
        An advanced (arcinfo) licence is required to use this tool, specifically
        the the feature vertices to points tool used to create the secondary lines and
        the ImportXMLWorkspaceDocument_management function used to add the empty feature classes
        and tables to the new file geodatabase or new fc's and tables to an existing file geodatabase
        """
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        # Any time a field is changed, update the projectconfig.json
        global_flightline.dump_to_projectconfig()

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""

        if not parameters[0].altered:
            return
        global_flightline.__load_project_folder__(parameters[0].valueAsText)

        return


    def execute(self, parameters, messages):
        """The source code of the tool"""

        project_directory = parameters[0].valueAsText
        new_gdb_name = parameters[1].valueAsText + '.gdb'


        global_flightline.add_new_flight_data_gdb_name(new_gdb_name)

        # Create new gdb and generate required tables/featureclasses
        global_flightline.create_flight_data_gdb(new_gdb_name)

        # Any time a field is changed, update the projectconfig.json
        global_flightline.dump_to_projectconfig()

        return

