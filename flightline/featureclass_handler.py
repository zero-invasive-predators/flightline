# Flightline Project

# Author: Nicholas Braaksma
# Date: 07-08-2017

# Description:
# Manages the tasks related to featureclasses.

import os
import arcpy
import datetime
import time
import csv
import glob
import linecache

def epsg_to_projection_name(epsg):
    """Returns the name of the epsg number"""
    try :
        spatial_reference = arcpy.SpatialReference(epsg)
        return spatial_reference.name
    except Exception as e:
        return None

def spatial_reference(epsg):
    return arcpy.SpatialReference(epsg).exportToString()

def directory_shapefile_list(shape_name, tracmap_data_directory):
    """
    Walks through the provided directory and returns a list of shapefiles that
    end with shape_name

    Parameters
    ----------
    shape_name : str
    tracmap_data_directory : str
    """

    shapefile_list = []
    for dirpath, dirnames, filenames in os.walk(tracmap_data_directory):
        for filename in [f.lower() for f in filenames if f.endswith(shape_name.lower())]:
            shapefile_list.append(os.path.join(dirpath, filename))

    return shapefile_list

def repair_geometry(featuerclass):
    """Repairs the geometry using arcpy.RepairGeometry.."""
    arcpy.RepairGeometry_management(in_features=featuerclass, delete_null='DELETE_NULL')

def featureclass_record_count(featureclass):
    """
    Returns the count of records in a featureclass

    Parameters
    ----------
    featureclass : str - location of featureclass

    Return
    ------
    record_count : int
    """

    record_count = int(arcpy.GetCount_management(featureclass).getOutput(0))
    return record_count

def featureclass_shape_type(featureclass):
    """
    Returns the featureclass shape type

    Parameters
    ----------
    featureclass : str - location of featureclass

    Return
    ------
    feature_type : str ['POLYGON','POINT','LINE']
    """

    desc = arcpy.Describe(featureclass)
    shape_type = desc.shapeType
    return shape_type

def define_projection(featureclass, coordinate_system):
    """
    If the coordinate system is unknown then defines the supplied coordinate system

    Parameters
    ----------
    featureclass : str - location of featureclass
    coordinate_system - ESRI Spatial Reference
    """

    desc = arcpy.Describe(featureclass)
    if desc.spatialReference.Name == 'Unknown':
        arcpy.DefineProjection_management(featureclass, coordinate_system)

def get_list_of_time_records(featureclass):
    """Returns list of times in the featureclasses Time field"""
    time_list = []
    with arcpy.da.SearchCursor(featureclass, ['Time']) as cursor:
        for row in cursor:
            time_list.append(row[0])
    return time_list

def merge_tracmap_data_featureclass(tracmap_data_directory, shapefile, merge_featureclass):
    """
    Copies data from a tracmap shapefile and merges it
    into the merge_featureclass

    Parameters
    ----------
    tracmap_data_directory : str - Directory containing the tracmap data
    shapefile_name : str - location of the shapefile to merge
    merge_featureclass : str - location of merge featureclass
    """

    # Copy the shapefile into memory to add a '_' instead of the space in the 'GPS Alt' field name
    temp_fc = 'in_memory\\temp_fc'
    arcpy.CopyFeatures_management(shapefile,temp_fc)
    desc_fc = arcpy.Describe(temp_fc)
    field_list = [f.name for f in arcpy.ListFields(temp_fc) if f.name != desc_fc.OIDFieldName]
    field_list.append('SHAPE@') # Add geometry field into list
    blockname = os.path.basename(os.path.dirname(shapefile))
    tempfc_desc = arcpy.Describe(temp_fc)
    tempfc_spatialreference = tempfc_desc.spatialReference

    # Get a list of all the existing Time records concatenated with Speed records
    total_fc_list = []
    with arcpy.da.SearchCursor(merge_featureclass, ['Time','Speed']) as time_speed_cursor:
        for row in time_speed_cursor:
            total_fc_list.append("{0}_{1}".format(row[0],str(row[1])))

    # If the data is from Tracmap version 1 (Date and Time fields are sperated)
    if field_list[1] == 'Date':
        new_row_list = []
        with arcpy.da.SearchCursor(temp_fc, field_list, spatial_reference = tempfc_spatialreference) as source_cursor:
            field_list.append('BlockName')
            field_list.pop(1)
            with arcpy.da.InsertCursor(merge_featureclass, field_list) as destination_cursor:
                for row in source_cursor:
                    # If the row already exists, don't add it
                    date_time = "{0}T{1}+1300".format(row[1],row[2][:-5])
                    line = "{0}_{1}".format(date_time,str(row[3]))
                    if line not in total_fc_list:
                        row = list(row)
                        row[1] = date_time
                        row.remove(row[2])
                        if blockname == os.path.basename(tracmap_data_directory):
                            if shapefile.endswith('log.shp'):
                                row.append(os.path.basename(shapefile)[:-7])
                            else:
                                row.append(os.path.basename(shapefile)[:-13])
                        else:
                            row.append(blockname)
                        destination_cursor.insertRow(row)
                        new_row_list.append(row[1])

        #TODO Addmessage
        #Add message displaying the number of rows added to the feature class
        #arcpy.AddMessage(str(len(newRowsList)) + ' rows added to ' + featureClass + ' fc from ' + shapefile)

    # If the data is from Tracmap version 2 or later (Date and Time are concatenated into one field)
    elif field_list[1] == 'Time':
        new_row_list = []
        with arcpy.da.SearchCursor(temp_fc, field_list, spatial_reference = tempfc_spatialreference) as source_cursor:
            field_list.append('BlockName')
            with arcpy.da.InsertCursor(merge_featureclass, field_list) as destination_cursor:
                for row in source_cursor:
                    # If the row already exists, don't add it.
                    line = "{0}_{1}".format(row[1], str(row[2]))
                    if line not in total_fc_list:
                        row = list(row)
                        if blockname == os.path.basename(tracmap_data_directory):
                            row.append('')
                        else:
                            row.append(blockname)
                        destination_cursor.insertRow(row)
                        new_row_list.append(row[1])

        # TODO Add message
        # Add message displaying the number of rows added to the feature class
        #arcpy.AddMessage(str(len(newRowsList)) + ' rows added to ' + featureClass + ' fc from ' + shapefile)

    else:
        # TODO add error message
        #arcpy.AddError(shpName + ' does not contain the required fields. Check your data!')
        pass
    # Delete tempory featureclass
    arcpy.Delete_management(temp_fc)


def rename_flight_data_datasets(flight_data_gdb, dataset_list):
    """
    Renames the datasets by adding a number to the end of them.
    The number is the next number in the list of already backedup datasets.

    Parameters
    ----------
    flight_data_gdb : str - Location of flight data geodatabase
    dataset_list : list<str> - Names of datasets to look for
    """
    # Datasets can include both tables and featureclasses

    arcpy.env.workspace = flight_data_gdb
    workspace_dataset_list = []
    workspace_dataset_list.extend(arcpy.ListFeatureClasses())
    workspace_dataset_list.extend(arcpy.ListTables())

    for ds in workspace_dataset_list:
        if ds in dataset_list:
            ds_copies = [i for i in workspace_dataset_list if ds in i]
            arcpy.Rename_management(in_data=ds, out_data="{0}_{1}".format(ds,len(ds_copies)))

def update_totallines_featureclass(total_lines_fc, total_polygons_fc, helicopter_rego, download_time, deflector):
    """
    Updates the totallines featureclass when new tracmap data has been loaded in

    Parameters
    ----------
    total_lines_fc : str - TotalLines featureclass location
    """

    arcpy.env.overwriteOutput = True

    # Update totallines with the Machine and Download Times etc.. make sure 'Buffer' is not empty
    null_buffer = arcpy.MakeFeatureLayer_management(total_lines_fc, 'null_buffer', 'Buffer IS NULL')
    null_buffer_count = int(arcpy.GetCount_management(null_buffer).getOutput(0))

    if null_buffer_count == 0:
        return 0

    with arcpy.da.UpdateCursor(total_lines_fc, ['Width','Machine','DL_Time','Bucket','Buffer'],'Buffer IS NULL') as update_tl_cursor:
        for row in update_tl_cursor:
            row[1] = helicopter_rego
            row[2] = download_time
            if row[0] >= 120:
                row[3] = 'Broadcast'
                buffer_type = 'Round'
            elif row[0] >= 40 and row[0] < 120:
                row[3] = 'Narrow'
                buffer_type = 'Round'
            elif row[0] < 40 and row [0] >= 4:
                row[3] = 'Trickle'
                buffer_type = 'Square'
            elif row[0] < 4 and row[0] > 0:
                row[3] = 'Sprayboom'
                buffer_type = 'Square'
            if row[3] == 'Trickle':
                row[4] = 15
            else:
                row[4] = row[0] / 2

            update_tl_cursor.updateRow(row)

        # Expression to select newly added rows
        new_row_where_clause = "Machine = '{0}' AND DL_TIME = '{1}'".format(helicopter_rego, download_time)

        # Buffer the records just added to the total_lines featureclass and add them to the total_polygons featureclass
        new_row_selection = arcpy.MakeFeatureLayer_management(
            in_features=total_lines_fc,
            out_layer='new_row_selection',
            where_clause=new_row_where_clause)
        if deflector:
            temp_buffer = arcpy.Buffer_analysis(new_row_selection, 'in_memory\\temp_buffer','Buffer','RIGHT','FLAT')
        else:
            if buffer_type == 'Round':
                temp_buffer = arcpy.Buffer_analysis(new_row_selection, 'in_memory\\temp_buffer', 'Buffer')
            elif buffer_type == 'Square':
                temp_buffer = arcpy.Buffer_analysis(new_row_selection, 'in_memory\\temp_buffer', 'Buffer', 'FULL', 'FLAT')

        temp_buffer_sort = arcpy.Sort_management(temp_buffer, 'in_memory\\temp_buffer_sort','Time')
        arcpy.Append_management(temp_buffer_sort, total_polygons_fc, 'NO_TEST')

        # Calculate Hectares
        arcpy.CalculateField_management(total_polygons_fc, 'Hectares', 'round(!shape.area!/10000,4)', "PYTHON_9.3", '')

        # Tidy up temporary files
        arcpy.Delete_management('in_memory\\temp_buffer')
        arcpy.Delete_management('in_memory\\temp_buffer_sort')
        arcpy.Delete_management(null_buffer)

        new_rows_added = int(arcpy.GetCount_management(new_row_selection).getOutput(0))
        arcpy.Delete_management(new_row_selection)
        arcpy.env.overwriteOutput = False
        # TODO add the count of new rows added to the tools output
        return new_rows_added

def update_totalpoints_featureclass(total_points_fc, helicopter_rego, download_time):
    """
    Updates the totalpoints featureclass when new tracmap data has been loaded in

    Parameters
    ----------
    total_points_fc : str - TotalLines featureclass location
    helicopter_rego : str - eg. 'JKC'
    download_time : str - eg 0910
    """

    with arcpy.da.UpdateCursor(total_points_fc, ['Machine', 'DL_Time'], 'DL_Time IS NULL') as cursor:
        for row in cursor:
            row[0] = helicopter_rego
            row[1] = download_time
            cursor.updateRow(row)

    # Expression to select newly added rows
    new_row_where_clause = "Machine = '{0}' AND DL_TIME = '{1}'".format(helicopter_rego, download_time)

    # Make a feature layer of the newly added points
    total_points = arcpy.MakeFeatureLayer_management(total_points_fc, 'new_row_points_selection', new_row_where_clause)
    selected_points_count = int(arcpy.GetCount_management(total_points).getOutput(0))
    if selected_points_count == 0:
        # TODO add message to tool output
        msg = 'There are no new records to add'
    arcpy.Delete_management(total_points)
    return selected_points_count

def convert_secondary_points_to_lines(total_points, total_lines, flight_path, operation_start_time_table, helicopter_rego, download_time):
    """
    Converts secondary points to lines
    This is a mega method and should be broken down into manageable chunks.
    """

    # Setup variables
    # Expression to select newly added rows
    new_row_where_clause = "Machine = '{0}' AND DL_TIME = '{1}'".format(helicopter_rego, download_time)
    make_line = True
    sow_line_list = []
    # Make feature layers of featureclasses
    new_lines_lyr = arcpy.MakeFeatureLayer_management(total_lines, 'new_lines_selection', new_row_where_clause)
    new_points_lyr = arcpy.MakeFeatureLayer_management(total_points, 'new_points_selection', new_row_where_clause)
    total_points_desc = arcpy.Describe(total_points)

    new_records_added_count = int(arcpy.GetCount_management(new_points_lyr).getOutput(0))
    # If there are no new records then return
    if not new_records_added_count:
        return new_records_added_count

    speed_list = [speed[0] for speed in arcpy.da.SearchCursor(new_points_lyr,['Speed'])]
    mean_speed = sum(speed_list) / len(speed_list)
    if mean_speed < 40:
        nearest_point_distance = 5
    else:
        nearest_point_distance = 10

    # Create a temporary fc of the start points of the newly added lines
    new_line_start_points = arcpy.FeatureVerticesToPoints_management(new_lines_lyr, 'in_memory\\new_line_start_points','START')
    # Identify any start points that are within 10 meters of a secondary point
    arcpy.Near_analysis(new_points_lyr, new_line_start_points, nearest_point_distance)

    total_points_desc = arcpy.Describe(total_points)
    total_lines_desc = arcpy.Describe(total_lines)

    with arcpy.da.SearchCursor(new_points_lyr, ['SHAPE@X','SHAPE@Y','Time','BlockName','NEAR_DIST','NEAR_FID', total_points_desc.oidFieldName]) as flight_points_cursor:
        with arcpy.da.InsertCursor(flight_path, ['SHAPE@','StartTime','EndTime','Machine','DL_Time','BlockName']) as flight_path_cursor:
            point = arcpy.Point()
            array = arcpy.Array()
            start_text = [s_time for s_time in arcpy.da.SearchCursor(new_points_lyr, ['Time']).next()][0]
            start_time = datetime.datetime.strptime(start_text[0:19], '%Y-%m-%dT%H:%M:%S')
            try: # TODO Create method to get operation_start_time
                operation_start_time = [op_start_time for op_start_time in arcpy.da.SearchCursor(operation_start_time_table,['Operation_Start_Time'])][0][0]
            except Exception:
                operation_start_time = datetime.datetime.strptime('2014-11-30T07:45:10','%Y-%m-%dT%H:%M:%S')

            for pnt in flight_points_cursor:
                block = pnt[3].encode('ascii','ignore')
                pnt_time = datetime.datetime.strptime(pnt[2][0:19],'%Y-%m-%dT%H:%M:%S')
                if pnt_time > operation_start_time:
                    sow_time_pnt_id_list = [[line_time, obj_id] for line_time, obj_id in arcpy.da.SearchCursor(new_line_start_points,['Time',total_lines_desc.oidFieldName]) if pnt[5] == obj_id]
                    if len(sow_time_pnt_id_list) == 1:
                        sow_time = datetime.datetime.strptime(sow_time_pnt_id_list[0][0][0:19], '%Y-%m-%dT%H:%M:%S')
                        time_diff = (sow_time - pnt_time).total_seconds()
                        pnt_id = sow_time_pnt_id_list[0][1]
                    else:
                        pnt_id = ''
                    if make_line == False:
                        start_time = pnt_time
                    # If the NEAR_DIST field has been populated and the number of points in the array is more than 0, create a new polyline based on the array
                    if pnt[4] > 0 and make_line == True and pnt_id not in sow_line_list and pnt_time <= sow_time and time_diff < 5:
                        if array.count != 0:
                            point.X = pnt[0]
                            point.Y = pnt[1]
                            array.add(point)
                            end_time = pnt_time
                            # Create a polyline object based on the array of points
                            polyline = arcpy.Polyline(array)
                            # Insert the feature
                            flight_path_cursor.insertRow([polyline, start_time, end_time, helicopter_rego, download_time, block])
                            # Clear the array
                            array.removeAll()
                            make_line = False
                            if pnt_id != '':
                                sow_line_list.append(pnt_id)
                            start_time = pnt_time
                        else:
                            point.X = pnt[0]
                            point.Y = pnt[1]
                            array.add(point)
                            end_time = pnt_time
                    else:
                        point.X = pnt[0]
                        point.Y = pnt[1]
                        array.add(point)
                        make_line = True
                        end_time = pnt_time
            # Catch the final polyline
            if array.count >= 1:
                polyline = arcpy.Polyline(array)
                array.removeAll()
                flight_path_cursor.insertRow([polyline, start_time, end_time, helicopter_rego, download_time, block])

            del flight_points_cursor, flight_path_cursor
            arcpy.Delete_management(new_line_start_points)

        # TODO Add message advising number of non sowing flight lines created
        new_flight_path_rows = arcpy.MakeFeatureLayer_management(flight_path, 'new_flight_path_rows', new_row_where_clause)
        flight_path_row_count = int(arcpy.GetCount_management(new_flight_path_rows).getOutput(0))

        # Cleanup
        arcpy.Delete_management(new_lines_lyr)
        arcpy.Delete_management(new_points_lyr)
        arcpy.Delete_management(new_flight_path_rows)
        # TODO Add message about new rows added.
        return flight_path_row_count

def calculate_operational_area_completion_dict(treatment_area):
    """
    For each block, stores the block name and the hectares of the block
    """
    block_area_dict = {}
    with arcpy.da.SearchCursor(treatment_area, ['HeliBlkNm','Hectares']) as block_areas:
        for block in block_areas:
            block_area_dict[block[0]] = block[1]

    return block_area_dict

def add_hectares_to_fc(featureclass):
    """Adds a new field and calculates the hectares of the records"""
    arcpy.AddField_management(featureclass, 'Hectares','DOUBLE')
    arcpy.CalculateField_management(featureclass, 'Hectares','round(!shape.area!/10000,4)','PYTHON_9.3','')

def feature_class_as_dict(featureclass, key_field, value_fields):
    """
    Cursors through a feature class and returns the rows as a dictionary

    Parameters
    ----------
    feature_class : str - Location of the featureclass
    key_field : str - Field used as the dictionaries key
    value_fields : list<str> List of fields to be used as values

    Returns
    -------
    dict : dictionary
    """

    fields = [key_field]
    fields.extend(value_fields)
    results_dict = {}

    with arcpy.da.SearchCursor(featureclass,fields) as cursor:
        for row in cursor:
            results_dict[row[0]] = [i for i in row[1:]]

    return results_dict


def new_flight_data_summary(total_lines, total_points, total_polygons, tracmap_data_folder, helicopter_rego, download_time, sum_totals_table, sum_totals_field_names, block_area_dict, df, total_polygons_lyr_file):
    """
    For newly added tracmap data, this summarizes it by reading the summary.txt file in the tracmap data folder
    and adding a record to the sum_totals table

    Parameters
    ----------
    total_lines : str - location of total_lines featureclass
    total_points : str - location of the toal_points featureclass
    total_polygons : str - location of the total_polygons featureclass
    tracmap_data_folder : str location of the newly downloaded tracmap data
    helicopter_rego : str - registration of the helicopter providing the tracmap data eg 'YYY'
    download_time : str - time tracmap data downloaded eg. '0910'
    sum_totals_table : str - location of the sum_totals table
    sum_totals_field_names : list<str> - list of the sum_totals_table field names
    block_area_dict : dict - Dict of treament area block name and hectares
    df : arcpy DataFrame - DataFrame of the project map
    total_polygons_lyr_file : str - Location of total_polygons layer file

    Returns
    -------
    Result : str - Empty string if no records returned, otherwise the summary.txt file location
    """
    new_rows_where_clause = "Machine = '{0}' AND DL_Time = '{1}'".format(helicopter_rego, download_time)
    new_total_lines_lyr = arcpy.MakeFeatureLayer_management(total_lines, 'new_total_lines_lyr', new_rows_where_clause)

    new_row_count = int(arcpy.GetCount_management(new_total_lines_lyr).getOutput(0))

    if new_row_count == 0:
        #TODO add message arcpy.AddMessage('No new rows to add to summary table')
        return ''

    with arcpy.da.SearchCursor(total_polygons, ['Machine','DL_Time','BlockName','Bucket','Hectares'],
                               where_clause = new_rows_where_clause,
                               sql_clause=(None, 'ORDER BY Machine, BlockName, Bucket')) as get_new_polygons_cursor:
        with arcpy.da.InsertCursor(sum_totals_table,sum_totals_field_names) as sum_totals_cursor:
            row_list = []
            for row in get_new_polygons_cursor:
                new_row = list(row[0:5])
                row_selection = "Machine = '{0}' AND DL_Time = '{1}' AND BlockName = '{2}'".format(new_row[0], new_row[1], new_row[2])
                last_points_time = [row_time[0].encode('ascii','ignore') for row_time in arcpy.da.SearchCursor(total_points, ['Time'], row_selection)][-1]
                new_row.append(last_points_time[11:19])
                source_txt_file_dir = os.path.join(tracmap_data_folder, new_row[0], new_row[1], new_row[2])
                if not os.path.exists(source_txt_file_dir):
                    source_txt_file_dir = os.path.join(tracmap_data_folder, new_row[0], new_row[1])
                source_txt_file = [name for name in glob.glob(source_txt_file_dir + r'\*.txt')][0]
                if linecache.getline(source_txt_file, 1)[:8] == 'Distance':
                    nominal_area = float(linecache.getline(source_txt_file,3)[19:-3].strip())
                    real_area = float(linecache.getline(source_txt_file,4)[19:-3].strip())
                    distance_flown = float(linecache.getline(source_txt_file,1)[20:-3].strip())
                    distance_spread = float(linecache.getline(source_txt_file,2)[19:-3].strip())
                    new_row.extend([nominal_area, real_area, distance_flown, distance_spread])
                elif linecache.getline(source_txt_file,1)[:4] == 'Area':
                    nominal_area = float(linecache.getline(source_txt_file,1)[17:-3].strip())
                    real_area = float(linecache.getline(source_txt_file,2)[17:-3].strip())
                    distance_flown = float(linecache.getline(source_txt_file,3)[19:-3].strip())
                    distance_spread = float(linecache.getline(source_txt_file,4)[19:-3].strip())
                    new_row.extend([nominal_area, real_area, distance_flown, distance_spread])
                if row[2].title() in block_area_dict:
                    new_row.append(block_area_dict[row[2].title()])
                else:
                    new_row.append(0)
                    #arcpy.AddWarning('treatmentArea feature class does not contain a block called  ' + row[2].title() + '. Check your data!')
                row_list.append(new_row)
            first_row = row_list[0]
            for row in row_list[1:]:
                if row[0:3] == first_row[0:3]:
                    row[4] = row[4] + first_row[4]
                    row_list.pop(row_list.index(row) - 1)
                    first_row = row
                else:
                    first_row = row
            for row in row_list:
                sum_totals_cursor.insertRow(row)

    # Message advising how many rows added to the summary table
    arcpy.AddMessage("{0} rows added to {1}".format(str(len(row_list)), sum_totals_table))
    try:

        # Update the symbology for the total_polygons layer with the newly added rows
        total_polygons_lyr = arcpy.mapping.Layer(total_polygons_lyr_file)
        total_polygons_mxd_lyr = arcpy.mapping.Layer(total_polygons_lyr.name)
        total_polygons_mxd_lyr.symbology.valueField = 'Machine'
        total_polygons_mxd_lyr.symbology.addAllValues()
        df.extent = total_polygons_mxd_lyr.getExtent()
        arcpy.RefreshActiveView()
    except:
        arcpy.AddMessage("Refresh of total_polygons_layer did not occur, manually update symbology")
    # Cleanup
    arcpy.Delete_management(new_total_lines_lyr)
    return source_txt_file

def summarize_flight_data(flight_data_gdb, total_polygons, sum_total_rows, df, sum_table_field_names):
    """
    Summarizes the current flight data. Creates a dissolved by block and total dissolved fc and a
    csv file summarizing the polygon data.

    Parameters
    ----------

    Returns
    -------

    """

    with arcpy.da.SearchCursor(total_polygons, ['BlockName']) as check_block_name:
        check_block_list = []
        for block_name in check_block_name:
            check_block_list.append(block_name[0])
        if '' not in check_block_list:
            dissolve_block_fc = os.path.join(flight_data_gdb, 'dissolved_by_block_{0}'.format(str(time.strftime('%m%d%H%M'))))
            arcpy.Dissolve_management(total_polygons, dissolve_block_fc, 'BlockName')
            add_hectares_to_fc(dissolve_block_fc)
            dissolved_block_fc_lyr = arcpy.mapping.Layer(dissolve_block_fc)
            arcpy.mapping.AddLayer(df, dissolved_block_fc_lyr)

            # TODO add message arcpy.AddMessage(dissolved_block_fc + ' created and added to map')
        else:
            dissolve_block_fc = False
            # TODO add warning message ('Some of the block name fields are empty - no dissolve by block undertaken)

    # Dissolve the polygons to get an overall area
    dissolved_total_polygon_fc = os.path.join(flight_data_gdb, 'total_dissolved_{0}'.format(str(time.strftime('%m%d%H%M'))))
    arcpy.Dissolve_management(total_polygons, dissolved_total_polygon_fc)
    add_hectares_to_fc(dissolved_total_polygon_fc)
    dissolved_total_polygon_fc_lyr = arcpy.mapping.Layer(dissolved_total_polygon_fc)
    arcpy.mapping.AddLayer(df, dissolved_total_polygon_fc_lyr)
    # TODO add message arcpy.AddMessage(dissolved_total_polygon_fc + ' created and added to map')

    # Order the sum_totals table by BlockName and Last_Log_Time and export to a csv file
    if dissolve_block_fc:
        csv_table_field_names = sum_table_field_names[2:]
        csv_table_field_names.append('Dissolved area')
        csv_table_field_names.append('Percentage sown')
        csv_file = os.path.join(os.path.dirname(flight_data_gdb), 'sum_totals_{0}.csv'.format(str(time.strftime('%H%M'))))
        with open(csv_file, 'wb') as export_file:
            csv_write = csv.writer(export_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
            csv_write.writerow(csv_table_field_names)
            with arcpy.da.SearchCursor(sum_total_rows, sum_table_field_names[2:], sql_clause=(None, 'ORDER BY BlockName, Last_log_time')) as csv_output:
                csv_output_list = []
                for row in csv_output:
                    csv_output_list.append(list(row))
                row_count = 0
                for row in csv_output_list:
                    dissolved_block_area = [block_area for block_name, block_area in arcpy.da.SearchCursor(dissolve_block_fc,['BlockName','Hectares']) if block_name == row[0]]
                    if row_count == 0:
                        row.append(round(dissolved_block_area[0], 4))
                        if row[8] != 0:
                            row.append(round((row[2] / row[8]) * 100, 2))
                        else:
                            row.append(0)
                        first_row = row
                    else:
                        if row[0] == first_row[0]:
                            row[2] += first_row[2]
                            row.append(round(dissolved_block_area[0], 4))
                            if row[8] != 0:
                                row.append(round((row[2] / row[8]) * 100, 2))
                            else:
                                row.append(0)
                            first_row = row
                        else:
                            row.append(round(dissolved_block_area[0], 4))
                            if row[8] != 0:
                                row.append(round((row[2] / row[8]) * 100, 2))
                            else:
                                row.append(0)
                            csv_write.writerow(first_row)
                            first_row = row
                    if row_count +1 == len(csv_output_list):
                        csv_write.writerow(row)
                    row_count += 1
                    csv_write.writerow('')
                    dissolved_total_polygon_area = [total_area for total_area in arcpy.da.SearchCursor(dissolved_total_polygon_fc,['Hectares'])]
                    csv_write.writerow(['Total dissolved area','','','','','','','','',dissolved_total_polygon_area[0][0],''])
        return csv_file

        # TODO addmessage arcpy.AddMessage('sum_totals sorted and saved to ' + csv_file)
    else:
        # TODO addwarning arcpy.AddWarning('Some of the block name fields are empty - no summary csv file created)
        pass

def get_featureclass_field_names(featureclass):
    """
    Returns list of the featureclasses fieldnames

    Parameters
    ---------
    featureclass : str - Location of featureclass

    Returns
    -------
    field_names_list : list<str>
    """

    field_names = []

    for i in arcpy.ListFields(featureclass):
        field_names.append(i.name)

    return field_names

def featureclass_exists(featureclass):
    """
    Returns boolean of the existance of the featureclass
    Parameters
    ----------
    featureclass : str - location of the featureclass

    Returns
    -------
    exists : boolean
    """

    return arcpy.Exists(featureclass)

def add_field_to_featureclass(featureclass, field_name, field_type, field_length=None):
    """
    Adds field to featureclass using arcpy.AddField_management()

    Parameters
    ----------
    featureclass : str - Location of featureclass
    field_type : str
    field_length : int
    """

    arcpy.AddField_management(in_table=featureclass, field_name=field_name,
                             field_type=field_type,
                             field_length=field_length)


























