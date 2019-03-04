import arcpy, time, linecache, os, csv, glob
from datetime import datetime
from distutils import dir_util

# V201602121220
# To do:
# Catch error when renaming fc's that are locked - error message not correct
# 1/ remove data captured prior to start (travel lines)
# 2/ remove long lines where gps is turned off /on in flight
# Catch error if a feature class has been put in a group layer

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = 'Tracmap Utilities Toolbox'
        self.alias = 'Tracmap Utilities Tbx'

        # List of tool classes associated with this toolbox
        self.tools = [Copy_tracmap_data_to_geodatabase, Enter_or_update_operation_metadata]

class Copy_tracmap_data_to_geodatabase(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""

        self.label = 'Copy Tracmap data'
        self.description = 'Copy the Tracmap data from the usb drive to the pc'
        self.canRunInBackground = True

    def getParameterInfo(self):
        """Define parameter definitions"""

        parametersFilePath = os.path.join(os.path.dirname(__file__),'parameters.csv')
        linecache.updatecache(parametersFilePath)

        # parameter 0
        sourceDataLocation = arcpy.Parameter(
            displayName = 'Drive or folder containing the Tracmap data to copy',
            name = 'data_source_location',
            datatype = 'DEWorkspace',
            parameterType = 'Required',
            direction = 'Input')
        sourceDataLocation.value = linecache.getline(os.path.join(os.path.dirname(__file__),'parameters.csv'),1)[:-1]

        # parameter 1
        coordinateSystem = arcpy.Parameter(
            displayName = 'Coordinate system of Tracmap data',
            name = 'coordinate_system',
            datatype = 'GPCoordinateSystem',
            parameterType = 'Required',
            direction = 'Input')
        coordinateSystem.value = linecache.getline(parametersFilePath,2)[:-1]

        # parameter 2
        parentDestinationDirectory = arcpy.Parameter(
            displayName = 'Parent directory where the raw Tracmap data will be stored',
            name = 'parent_directory',
            datatype = 'DEFolder',
            parameterType = 'Required',
            direction = 'Input')
        parentDestinationDirectory.value = linecache.getline(parametersFilePath,3)[:-1]

        # parameter 3
        treatmentAreaFeatureClass = arcpy.Parameter(
            displayName = 'Feature class containing the treatment area blocks',
            name = 'treatment_area_fc',
            datatype = 'DEFeatureClass',
            parameterType = 'Optional',
            direction = 'Input')
        treatmentAreaFeatureClass.value = linecache.getline(parametersFilePath,4)[:-1]

        # Set the filter to only accept polygon feature classes
        treatmentAreaFeatureClass.filter.list = ['Polygon']

        # parameter 4
        localGDB = arcpy.Parameter(
            displayName="File geodatabase where the processed data from the helicopter will be stored",
            name="in_workspace",
            datatype="DEWorkspace",
            parameterType="Optional",
            direction="Input")
        localGDB.value = linecache.getline(parametersFilePath,5)[:-1]

        # Set the filter to accept only local (personal or file) geodatabases
        localGDB.filter.list = ["Local Database"]

        # parameter 5
        newGeodatabaseChkBx = arcpy.Parameter(
            displayName = 'Create new geodatabase',
            name = 'new_geodatabase_chkbox',
            datatype = 'GPBoolean',
            parameterType = 'Optional',
            direction = 'Input')
        newGeodatabaseChkBx.value = False

        # parameter 6
        newFGDBLocation = arcpy.Parameter(
            displayName = 'Location of the new file geodatabase',
            name = 'file_geodatabase_location',
            datatype = 'DEFolder',
            parameterType = 'Optional',
            direction = 'Input')

        # parameter 7
        newFGDBName = arcpy.Parameter(
            displayName = 'Name of the new file geodatabase',
            name = 'file_geodatabase_name',
            datatype = 'GPString',
            parameterType = 'Optional',
            direction = 'Input')

        # parameter 8
        helicopterRegNo = arcpy.Parameter(
            displayName = 'Helicopter Reg No',
            name = 'helicopter_reg_no',
            datatype = 'String',
            parameterType = 'Optional',
            direction = 'Input')
        #helicopterRegNo.value = '???'

        # parameter 9
        downloadTime = arcpy.Parameter(
            displayName = 'Download time (defaults to current time)',
            name = 'download_time',
            datatype = 'String',
            parameterType = 'Required',
            direction = 'Input')

        # parameter 10
        writeParametersChkBx = arcpy.Parameter(
            displayName = 'Set up and write parameters to ' +
                           parametersFilePath + '. No flight data will be processed. Refresh toolbox!',
            name = 'write_to_parameters_file',
            datatype = 'GPBoolean',
            parameterType = 'Optional',
            direction = 'Input')
        writeParametersChkBx.value = False

        # parameter 11
        createSummariesChkBx = arcpy.Parameter(
            displayName = 'Dissolve polygons (by block and total) in ' +
                          os.path.basename(linecache.getline(parametersFilePath,5)[:-1])  +
                          ' and output a summary csv file in ' +
                          os.path.dirname(linecache.getline(parametersFilePath,5)[:-1]),
            name = 'create_dissolved_polygons',
            datatype = 'GPBoolean',
            parameterType = 'Optional',
            direction = 'Input')
        createSummariesChkBx.value = False

        # parameter 12
        deflectorChkBx = arcpy.Parameter(
            displayName = 'Deflector bucket in use - this bucket spreads bait to the right side only',
            name = 'deflector_chkbox',
            datatype = 'GPBoolean',
            parameterType = 'Optional',
            direction = 'Input')
        deflectorChkBx.enabled = False

        params = [sourceDataLocation, coordinateSystem, parentDestinationDirectory, treatmentAreaFeatureClass,
                  localGDB, newGeodatabaseChkBx, newFGDBLocation, newFGDBName, helicopterRegNo, downloadTime,
                  writeParametersChkBx, createSummariesChkBx, deflectorChkBx]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute.
           An advanced (arcinfo) licence is required to use this tool, specifically
           the the feature vertices to points tool used to create the secondary lines and
           the ImportXMLWorkspaceDocument_management function used to add the empty feature classes
           and tables to the new file geodatabase or new fc's and tables to an existing file geodatabase
        """

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

        # If the 'Write parameters to file' is ticked, enable the relevant inputs
        if parameters[10].value == True:
            parameters[0].enabled = True
            parameters[1].enabled = True
            parameters[2].enabled = True
            parameters[3].enabled = True
            parameters[4].enabled = True
            parameters[5].enabled = True
            parameters[8].enabled = False
            parameters[9].enabled = False
            parameters[11].enabled = False
            #parameters[12].enabled = False
        elif parameters[10].value == False:
            parameters[1].enabled = False
            parameters[2].enabled = False
            parameters[3].enabled = False
            parameters[4].enabled = False
            parameters[5].value = False
            parameters[5].enabled = False
            parameters[8].enabled = True
            parameters[9].enabled = True
            parameters[11].enabled = True
            #parameters[12].enabled = True

        # If 'Create new geodatabase' is ticked, enable the relevant inputs
        # ('Write parameters to file' must be ticked intially)
        if parameters[5].value == True:
            parameters[4].value = None
            parameters[4].enabled = False
            parameters[6].enabled = True
            parameters[7].enabled = True
        elif parameters[5].value == False:
            parameters[6].enabled = False
            parameters[7].enabled = False

        # If 'Dissolve polygons ...' is ticked, disable all other inputs
        # as they do not need to be changed
        if parameters[11].value == True:
            parameters[8].enabled = False
            parameters[9].enabled = False
            parameters[10].enabled = False
            parameters[12].enabled = False
        elif parameters[11].value == False:
            parameters[10].enabled = True

        # Create a drop down list of helicopter regNo's from the helicopter_info table

        localGDB = parameters[4].valueAsText
        if localGDB is not None:
            helicopterList = [regNo[0] for regNo in arcpy.da.SearchCursor(os.path.join(localGDB,'helicopter_info'),['helicopter_registration_no'])]
            helicopterList.sort()
            parameters[8].filter.list = helicopterList

        # Add the current time
        if not parameters[9].altered:
            parameters[9].value = time.strftime('%H%M')

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""

        #
        if parameters[4].altered:
            if parameters[4].valueAsText is not None:
                localGDB = parameters[4].valueAsText
                if localGDB[-4:] != '.gdb':
                    parameters[4].setErrorMessage('The database must be a file geodatabase')

        #
        if parameters[8].altered:
            if len([regNo[0] for regNo in arcpy.da.SearchCursor(os.path.join(localGDB,'helicopter_info'),['helicopter_registration_no'])]) == 0:
                parameters[8].setErrorMessage('Enter helicopter information via the "Enter or update operation metadata" tool')

        # Create a drop down list of all the helicopterRegNo directories if they exist.
        if parameters[9].altered:
            if parameters[8].altered:
                helicopterRegNo = parameters[8].valueAsText
                parentDestinationDirectory = parameters[2].valueAsText
                if parentDestinationDirectory:
                    downloadTime = parameters[9].valueAsText
                    if os.path.exists(os.path.join(parentDestinationDirectory,helicopterRegNo)):
                        if os.path.exists(os.path.join(parentDestinationDirectory,helicopterRegNo,downloadTime)):
                            timeDownloadedList = os.listdir(os.path.join(parentDestinationDirectory,helicopterRegNo))
                            # Generate a message if the downloadTime directory the user is trying to create already exists.
                            if downloadTime in timeDownloadedList:
                                parameters[9].setErrorMessage(downloadTime + ' directory already exists')
                            else:
                                parameters[9].clearMessage()
                    try:
                        if time.strptime(downloadTime,'%H%M'):
                            if len(downloadTime) != 4:
                                parameters[9].setWarningMessage('Download time must be 4 numbers i.e. 1234')
                            elif not int(downloadTime):
                                parameters[9].setWarningMessage('Download time must be 4 numbers i.e. 1234')
                            else:
                                parameters[9].clearMessage()
                    except:
                        raise ValueError('This is not a valid time format')

        #
        if parameters[10].value == True:
            if parameters[5].value == False:
                if parameters[4].value is None:
                    parameters[4].value = linecache.getline(os.path.join(os.path.dirname(__file__),'parameters.csv'),5)[:-1]
        else:
            if parameters[4].value is None:
                parameters[4].value = linecache.getline(os.path.join(os.path.dirname(__file__),'parameters.csv'),5)[:-1]

        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        def copy_data(shpName,tracmapDataDirectory,featureClass,coordinateSystem):
            ''' A function to define the projections of the 'log' and 'secondary' shapefiles
                in the tracmap data, repair their geometry and then copy the new rows in
                each shapefile to the specified feature class in a file geodatabase
            '''

            # Search through all the subdirectories in the tracmap folder and create a list of all the files called shpName
            shapefileList = []
            for dirpath,dirnames,filenames in os.walk(tracmapDataDirectory):
                for filename in [f for f in filenames if f.endswith(shpName)]:
                    shapefileList.append(os.path.join(dirpath,filename))

            # If shapefileList is empty stop the script
            if len(shapefileList) == 0:
                   arcpy.AddError('Directory does not contain a shapefile named ' + shpName)
            else:
                # Loop through all shapefiles in the tracmap directory and add all new rows to the feature class
                for shapefile in shapefileList:

                    # Check if the shapefile contains any records
                    countRows = arcpy.GetCount_management(shapefile)
                    countRowsResult = int(countRows.getOutput(0))
                    if countRowsResult == 0:
                        arcpy.AddWarning(shapefile + ' contains no data')
                    else:

                        # Check that the shapeType is a polyline or a point
                        descShp = arcpy.Describe(shapefile)
                        shpType = descShp.shapeType
                        if shpType in ['Polyline','Point']:

                            # Repair geometry
                            arcpy.RepairGeometry_management(shapefile, 'DELETE_NULL')

                            # If not already defined, define the projection of the shapefiles
                            if descShp.spatialReference.Name == 'Unknown':
                                arcpy.DefineProjection_management(shapefile, coordinateSystem)

                            # Copy the shapefile to in_memory to add a '_' instead of the space in the 'GPS Alt' field name.
                            tempFC = r'in_memory\temp_fc'
                            arcpy.CopyFeatures_management(shapefile,tempFC)

                            # Get the field objects from the shapefile
                            descFC = arcpy.Describe(tempFC)
                            fCFields = descFC.fields

                            # List all the field names except for the OID field
                            shpFieldNames = [field.name for field in fCFields if field.name != descFC.OIDFieldName]

                            # Append the field name containing the geometry
                            shpFieldNames.append('SHAPE@')

                            # Get the blockname - the shapefile's parent directory
                            blockName = os.path.basename(os.path.dirname(shapefile))

                            # Get a list of all the existing Time records concatenated with Speed records
                            totalFCList = []
                            with arcpy.da.SearchCursor(featureClass,['Time','Speed']) as timeSpeedCursor:
                                for row in timeSpeedCursor:
                                    totalFCList.append(row[0] + '_' +str(row[1]))

                            # If the data is from Tracmap version 1 (Date and Time fields are separated)
                            if shpFieldNames[1] == 'Date':

                                # Create cursors and insert new rows
                                newRowsList = []
                                with arcpy.da.SearchCursor(tempFC,shpFieldNames,spatial_reference=descFC.spatialReference) as sourceCursor:
                                    shpFieldNames.append('BlockName')
                                    shpFieldNames.pop(1)
                                    with arcpy.da.InsertCursor(featureClass,shpFieldNames) as destCursor:
                                        for row in sourceCursor:
                                            # if the row already exists, don't add it
                                            date_time = row[1] + 'T' + row[2][:-5] + '+1300'
                                            line = date_time + '_' + str(row[3])
                                            if line not in totalFCList:
                                                row = list(row)
                                                row[1] = date_time
                                                row.remove(row[2])
                                                if blockName == os.path.basename(tracmapDataDirectory):
                                                    if shapefile.endswith('log.shp'):
                                                        row.append(os.path.basename(shapefile)[:-7])
                                                    else:
                                                        row.append(os.path.basename(shapefile)[:-13])
                                                else:
                                                    row.append(blockName)
                                                destCursor.insertRow(row)
                                                newRowsList.append(row[1])

                                # Add message displaying the number of rows added to the feature class
                                arcpy.AddMessage(str(len(newRowsList)) + ' rows added to ' + featureClass + ' fc from ' + shapefile)

                            # If the data is from Tracmap version 2 or later (Date and Time are concatenated into one field)
                            elif shpFieldNames[1] == 'Time':

                                # Create cursors and insert new rows
                                newRowsList = []
                                with arcpy.da.SearchCursor(tempFC,shpFieldNames,spatial_reference=descFC.spatialReference) as sourceCursor:
                                    shpFieldNames.append('BlockName')
                                    with arcpy.da.InsertCursor(featureClass,shpFieldNames) as destCursor:
                                        for row in sourceCursor:
                                            # if the row already exists, don't add it
                                            line = row[1] + '_' + str(row[2])
                                            if line not in totalFCList:
                                                row = list(row)
                                                if blockName == os.path.basename(tracmapDataDirectory):
                                                    row.append('')
                                                else:
                                                    row.append(blockName)
                                                destCursor.insertRow(row)
                                                newRowsList.append(row[1])

                                # Add message displaying the number of rows added to the feature class
                                arcpy.AddMessage(str(len(newRowsList)) + ' rows added to ' + featureClass + ' fc from ' + shapefile)

                            else:
                                arcpy.AddError(shpName + ' does not contain the required fields. Check your data!')

                            # Delete temporary shapefiles
                            arcpy.Delete_management(tempFC)

                        else:
                            if shpName == 'log.shp':
                                arcpy.AddError(shapefile + ' is a ' + shpType + ' shapefile. It should be a Polyline shapefile.\n No rows added to ' + totalLines)
            return

        # Set variables
        arcpy.env.overwriteOutput = True
        sourceDataLocation = parameters[0].valueAsText
        coordinateSystem = parameters[1].value
        coordinateSystemTxt = parameters[1].valueAsText
        parentDestinationDirectory = parameters[2].valueAsText
        treatmentAreaFeatureClass = parameters[3].value
        treatmentAreaFeatureClassTxt = parameters[3].valueAsText
        localGDB = parameters[4].valueAsText
        newGeodatabaseChkBx = parameters[5].value
        if  newGeodatabaseChkBx == True:
            newFGDBLocation = parameters[6].valueAsText
            newFGDBName = parameters[7].valueAsText
            localGDB = os.path.join(newFGDBLocation,newFGDBName) + '.gdb'
        helicopterRegNo = parameters[8].valueAsText
        downloadTime = parameters[9].valueAsText
        writeParametersChkBx = parameters[10].value
        createSummariesChkBx = parameters[11].value
        deflectorChkBox = parameters[12].value
        totalPoints = os.path.join(localGDB,'total_points')
        totalLines = os.path.join(localGDB,'total_lines')
        totalPolygons = os.path.join(localGDB,'total_polygons')
        flightPath = os.path.join(localGDB,'flight_path')
        sumTotalRows = os.path.join(localGDB,'sum_totals')
        operationStartTimeTbl = os.path.join(localGDB,'operation_start_end_time')

        # Location of script
        thisFolder = os.path.dirname(__file__)

        # Set variables for layers to be displayed in the mxd
        totalPointsLyrFile = os.path.join(thisFolder,'total_points.lyr')
        totalLinesLyrFile = os.path.join(thisFolder,'total_lines.lyr')
        flightPathLyrFile = os.path.join(thisFolder,'flight_path.lyr')
        totalPolygonsLyrFile = os.path.join(thisFolder,'total_polygons.lyr')

        mxd = arcpy.mapping.MapDocument(r'CURRENT')
        df = arcpy.mapping.ListDataFrames(mxd,'*')[0]
##        lyrList = [lyr.dataSource for lyr in arcpy.mapping.ListLayers(mxd,'*',df) if lyr.supports("DATASOURCE")]
##        chkLyrDict = {totalPolygons:totalPolygonsLyrFile,totalLines:totalLinesLyrFile,
##                      flightPath:flightPathLyrFile,totalPoints:totalPointsLyrFile}
        sumTableFieldNames = ['Machine','DL_Time','BlockName','Bucket','Hectares','Last_log_time',
                              'Nominal_Area','Real_Area','Distance_Travelled','Distance_spreading','Block_Area']

        try:
            # Update parameters.csv with the new entries
            if writeParametersChkBx == True:
                parametersFilePath = os.path.join(os.path.dirname(__file__),'parameters.csv')
                with open(parametersFilePath,'w') as parameterFile:
                    parameterFile.write(sourceDataLocation + '\n')
                    parameterFile.write(coordinateSystemTxt + '\n')
                    parameterFile.write(parentDestinationDirectory + '\n')
                    if treatmentAreaFeatureClassTxt is None:
                        parameterFile.write('\n')
                    else:
                        parameterFile.write(treatmentAreaFeatureClassTxt + '\n')
                    if newGeodatabaseChkBx == True:
                        parameterFile.write(os.path.join(newFGDBLocation,newFGDBName) + r'.gdb')
                    else:
                        parameterFile.write(localGDB + '\n')
                    arcpy.AddMessage('Parameters.csv saved in ' + parametersFilePath)
                    linecache.updatecache(parametersFilePath)

                # If newGeodatabaseChkBx is True (checked), create a new file geodatabase
                if  newGeodatabaseChkBx == True:
                    arcpy.CreateFileGDB_management(newFGDBLocation,newFGDBName)
                    arcpy.ImportXMLWorkspaceDocument_management(os.path.join(newFGDBLocation,newFGDBName) + '.gdb',os.path.join(thisFolder,'xml','total_gdb.xml'),'SCHEMA_ONLY')
                    arcpy.AddMessage('New file geodatabase ' + newFGDBName + ' created in ' + newFGDBLocation + '\nwith schema from ' +  os.path.join(thisFolder,'xml','total_gdb.xml'))
                else:
                    # If using an existing file geodatabase, if any of the required feature classes exist,
                    # rename them and create a new empty feature classes
                    requiredFCs = ['total_points','total_lines','total_polygons','flight_path']
                    arcpy.env.workspace = localGDB
                    fCList = arcpy.ListFeatureClasses()
                    for fC in requiredFCs:
                        if fC in fCList:
                            fCCopies = [i for i in fCList if fC in i]
                            arcpy.Rename_management(fC,fC + '_' + str(len(fCCopies)))
                            arcpy.ImportXMLWorkspaceDocument_management(localGDB,os.path.join(thisFolder,'xml',fC) + r'.xml','SCHEMA_ONLY')
                            arcpy.AddMessage(fC + ' renamed to ' + fC + '_' + str(len(fCCopies)) + ' and new ' + fC + ' fC created')
                        else:
                            arcpy.ImportXMLWorkspaceDocument_management(localGDB,os.path.join(thisFolder,'xml',fC) + r'.xml','SCHEMA_ONLY')

                    requiredTbls = ['sum_totals','helicopter_info','operation_start_end_time']
                    tblList = arcpy.ListTables()
                    for tbl in requiredTbls:
                        if tbl in tblList:
                            tblCopies = [i for i in tblList if tbl in i]
                            arcpy.Rename_management(tbl, tbl + '_' + str(len(tblCopies)))
                            arcpy.ImportXMLWorkspaceDocument_management(localGDB,os.path.join(thisFolder,'xml',tbl) + r'.xml','SCHEMA_ONLY')
                            arcpy.AddMessage(tbl + ' renamed to ' + tbl + '_' + str(len(tblCopies)) + ' and new ' + tbl + ' table created')
                        else:
                            arcpy.ImportXMLWorkspaceDocument_management(localGDB,os.path.join(thisFolder,'xml',tbl) + r'.xml','SCHEMA_ONLY')
                arcpy.AddWarning('To update any changes made to the tools parameters, refresh the toolbox before the tool is opened.' +
                                 '\nNow use the "Enter or update operation metadata tool" to add helicopters and operation start time ')

                # Add something to refresh the toolbox so next time it opens it has the updated values
                # At the moment this must be done manually - right click on the toolbox and refresh

            elif createSummariesChkBx == False:
                # Copy all the data in the sourceDataLocation directory / drive to the destination directory
                os.chdir(parentDestinationDirectory)
                destinationDirectory = os.path.join(parentDestinationDirectory,helicopterRegNo,downloadTime)
                if not os.path.exists(helicopterRegNo):
                    os.mkdir(helicopterRegNo)
                    os.chdir(helicopterRegNo)
                else:
                    os.chdir(helicopterRegNo)
                if not os.path.exists(downloadTime):
                    dir_util.copy_tree(sourceDataLocation,destinationDirectory)
                    arcpy.AddMessage('Tracmap data in ' + sourceDataLocation + ' copied to ' + destinationDirectory)
                else:
                    arcpy.AddError('Directory ' + destinationDirectory + ' already exists')
                os.chdir(parentDestinationDirectory)

                # Set Geographic Transformation
                arcpy.env.geographicTransformations = 'NZGD_2000_To_WGS_1984_1'

                # Add the lyrs files in the Toolbox directory to the mxd and replace the datasources with the new feature classes
                lyrList = [lyr.dataSource for lyr in arcpy.mapping.ListLayers(mxd,'*',df) if lyr.supports("DATASOURCE")]
                chkLyrDict = {totalPolygons:totalPolygonsLyrFile,totalLines:totalLinesLyrFile,
                              flightPath:flightPathLyrFile,totalPoints:totalPointsLyrFile}
                for lyr in chkLyrDict.iteritems():
                    if lyr[0] not in lyrList:
                        newLyr = arcpy.mapping.Layer(lyr[1])
                        # Change the source to the feature class in the current geodatabase
                        newLyr.replaceDataSource(os.path.dirname(lyr[0]),'FILEGDB_WORKSPACE',os.path.basename(lyr[0]))
                        arcpy.mapping.AddLayer(df,newLyr,'TOP')

                # Copy new rows in the log shapefiles to the totalLines feature class
                copy_data("log.shp",destinationDirectory,totalLines,coordinateSystem)

                # Update totalLines with the Machine and DL_Times etc - make sure 'Buffer' is not empty
                arcpy.MakeFeatureLayer_management(totalLines, 'nullBuffer','Buffer IS NULL')
                nullBufferCount = int(arcpy.GetCount_management('nullBuffer').getOutput(0))
                if nullBufferCount == 0:
                    arcpy.AddMessage('There are no new rows to add from ' + sourceDataLocation)
                else:
                    with arcpy.da.UpdateCursor(totalLines,['Width','Machine','DL_Time','Bucket','Buffer'],'Buffer IS NULL') as updateTLCursor:
                        for row in updateTLCursor:
                            row[1] = helicopterRegNo
                            row[2] = downloadTime
                            if row[0] >= 120:
                                row[3] = 'Broadcast'
                                bufferType = 'Round'
                            elif row[0] >= 40 and row[0] < 120:
                                row[3] = 'Narrow'
                                bufferType = 'Round'
                            elif row[0] < 40 and row [0] >= 4:
                                row[3] = 'Trickle'
                                bufferType = 'Square'
                            elif row[0] < 4 and row[0] > 0:
                                row[3] = 'Sprayboom'
                                bufferType = 'Square'
                            if row[3] == 'Trickle':
                                row[4] = 15
                            else:
                                row[4] = row[0] / 2

                            updateTLCursor.updateRow(row)

                        # Expression to select newly added rows
                        newRowsSelectionWhereClause = 'Machine = ' + "'" + helicopterRegNo + "'" + ' And DL_Time = ' + "'" + downloadTime + "'"

                        # Buffer the records just added to the total_lines feature class and add them to the total_polygons feature class
                        arcpy.MakeFeatureLayer_management(totalLines,'newRowsSelection',newRowsSelectionWhereClause)
                        if deflectorChkBox == True:
                            arcpy.Buffer_analysis('newRowsSelection',r'in_memory\temp_buffer','Buffer','RIGHT','FLAT')
                        else:
                            if bufferType == 'Round':
                                arcpy.Buffer_analysis('newRowsSelection',r'in_memory\temp_buffer','Buffer')
                            elif bufferType == 'Square':
                                arcpy.Buffer_analysis('newRowsSelection',r'in_memory\temp_buffer','Buffer','FULL','FLAT')

                        arcpy.Sort_management(r'in_memory\temp_buffer',r'in_memory\temp_buffer_sort','Time')
                        arcpy.Append_management(r'in_memory\temp_buffer_sort',totalPolygons,"NO_TEST")

                        # Calculate hectares
                        arcpy.CalculateField_management(totalPolygons, 'Hectares', 'round(!SHAPE_area!/10000,4)', "PYTHON_9.3", '')

                        # Add a message showing the number of polygons added to the totalPolygons fc
                        countRowsStr = arcpy.GetCount_management('newRowsSelection').getOutput(0)
                        arcpy.AddMessage(countRowsStr + ' rows added to ' + totalPolygons + ' fc')

                        # Tidy up temporary files
                        arcpy.Delete_management(r'in_memory\temp_buffer')
                        arcpy.Delete_management(r'in_memory\temp_buffer_sort')

                        # Copy new rows in the secondary shapefiles to the totalPoints feature class
                        copy_data("secondary.shp",destinationDirectory,totalPoints,coordinateSystem)

                        # Get a list of the time records in the newly added rows
                        timeList =[]
                        with arcpy.da.SearchCursor('newRowsSelection',['Time']) as timeCursor:
                            for rowTime in timeCursor:
                                timeList.append(rowTime[0])

                        # Update totalPoints with the Machine and DL_Times etc
                        with arcpy.da.UpdateCursor(totalPoints,['Machine','DL_Time'],'DL_Time IS NULL') as updateSecPointsCursor:
                            for row in updateSecPointsCursor:
                                row[0] = helicopterRegNo
                                row[1] = downloadTime
                                updateSecPointsCursor.updateRow(row)

                        # Convert the secondary points to lines #

                        # Make a feature layer of the newly added points
                        arcpy.MakeFeatureLayer_management(totalPoints,'newPointsSelection',newRowsSelectionWhereClause)

                        # Make sure 'newPointsSelection' is not empty
                        selectedPointsCount = int(arcpy.GetCount_management('newPointsSelection').getOutput(0))
                        if selectedPointsCount == 0:
                            arcpy.AddMessage('There are no new rows to add from ' + sourceDataLocation)
                        else:
                            makeLine = True
                            speedList = [speed[0] for speed in arcpy.da.SearchCursor('newPointsSelection',['Speed'])]
                            meanSpeed = sum(speedList) / len(speedList)
                            if meanSpeed < 40:
                                nearestPntDistance = 5
                            else:
                                nearestPntDistance = 10
                            sowLineList = []
                            # Create a temporary fc of the start points of the newly added lines
                            arcpy.FeatureVerticesToPoints_management(r'newRowsSelection',r'in_memory\new_line_start_points','START')
                            # Identify any start points that are within 10 metres of a secondary point
                            arcpy.Near_analysis('newPointsSelection',r'in_memory\new_line_start_points',nearestPntDistance)

                            with arcpy.da.SearchCursor('newPointsSelection',['SHAPE@X','SHAPE@Y','Time','BlockName','NEAR_DIST','NEAR_FID','OBJECTID']) as flightPntsCursor:
                                with arcpy.da.InsertCursor(flightPath,['SHAPE@','StartTime','EndTime','Machine','DL_Time','BlockName']) as flightPathCursor:
                                    point = arcpy.Point()
                                    array = arcpy.Array()
                                    startText = [sTime for sTime in arcpy.da.SearchCursor('newPointsSelection',['Time']).next()][0]
                                    startTime = datetime.strptime(startText[0:19],'%Y-%m-%dT%H:%M:%S')
                                    try:
                                        operationStartTime =[opStartTime for opStartTime in arcpy.da.SearchCursor(operationStartTimeTbl,['Operation_Start_Time'])][0][0]
                                    except Exception:
                                        operationStartTime = datetime.strptime('2014-11-30T07:45:10','%Y-%m-%dT%H:%M:%S')

                                    #operationStartTime = datetime.strptime('2015-05-27T08:50:10','%Y-%m-%dT%H:%M:%S') # for testing - Makarora data

                                    for pnt in flightPntsCursor:
                                        block = pnt[3].encode('ascii','ignore')
                                        pntTime = datetime.strptime(pnt[2][0:19],'%Y-%m-%dT%H:%M:%S')
                                        if pntTime > operationStartTime:
                                            time1 = pntTime
                                            sowTimePntIDList = [[lineTime,objId] for lineTime, objId in arcpy.da.SearchCursor(r'in_memory\new_line_start_points',['Time','OBJECTID']) if pnt[5] == objId]
                                            if len(sowTimePntIDList) == 1:
                                                sowTime = datetime.strptime(sowTimePntIDList[0][0][0:19],'%Y-%m-%dT%H:%M:%S')
                                                timeDiff = (sowTime - pntTime).total_seconds()
                                                pntID = sowTimePntIDList[0][1]
                                            else:
                                                pntID = ''
                                            if makeLine == False:
                                                startTime = pntTime

                                            # If the NEAR_DIST field has been populated and the number of points in the array is more than 0, create a new polyline based on the array
                                            if pnt[4] > 0 and makeLine == True and pntID not in sowLineList and pntTime <= sowTime and timeDiff < 5:
                                                if array.count != 0:
                                                    point.X = pnt[0]
                                                    point.Y = pnt[1]
                                                    array.add(point)
                                                    endTime = pntTime
                                                    # Create a polyline object based on the array of points
                                                    polyline = arcpy.Polyline(array)
                                                    # Insert the feature
                                                    flightPathCursor.insertRow([polyline,startTime,endTime,helicopterRegNo,downloadTime,block])
                                                    # Clear the array
                                                    array.removeAll()
                                                    makeLine = False
                                                    if pntID <> '':
                                                        sowLineList.append(pntID)
                                                    startTime = pntTime
                                                else:
                                                    point.X = pnt[0]
                                                    point.Y = pnt[1]
                                                    array.add(point)
                                                    endTime = pntTime

                                            else:
                                                point.X = pnt[0]
                                                point.Y = pnt[1]
                                                array.add(point)
                                                makeLine = True
                                                endTime = pntTime

                                    # Catch the final polyline
                                    if array.count >= 1:
                                        polyline = arcpy.Polyline(array)
                                        array.removeAll()
                                        flightPathCursor.insertRow([polyline,startTime,endTime,helicopterRegNo,downloadTime,block])

                            del flightPntsCursor, flightPathCursor
                            arcpy.Delete_management(r'in_memory\new_line_start_points')

                        # Add message advising number of non sowing flight lines created
                        arcpy.MakeFeatureLayer_management(flightPath, 'newFlightPathRows', newRowsSelectionWhereClause)
                        flightPathRowCount = arcpy.GetCount_management('newFlightPathRows').getOutput(0)
                        arcpy.AddMessage(flightPathRowCount + ' lines created in ' + flightPath + ' from ' + str(selectedPointsCount) + ' newly added points in ' + totalPoints )

                        # Get operational area feature class if available
                        blockAreaDict = {}
                        if treatmentAreaFeatureClass:
#                            # Check if there are fields called 'BlockName' and 'Hectares' in the treatment area feature class
#                            treatmentAreaFeatureClassFields = [f.name for f in arcpy.ListFields(treatmentAreaFeatureClass)]
#                            requiredFields = ['BlockName','Hectares']
                            with arcpy.da.SearchCursor(treatmentAreaFeatureClass,['HeliBlkNm','Hectares']) as blockAreas:
                                for block in blockAreas:
                                    blockAreaDict[block[0]] = block[1]
                        else:
                            arcpy.AddWarning('There is no operational area feature class linked to this data. Percentage completed will not be calculated')

                        # Summarise the newly added data and append it to the sum_totals table
                        selectedRowsCount = int(arcpy.GetCount_management('newRowsSelection').getOutput(0))

                        if selectedRowsCount == 0:
                            arcpy.AddMessage('No new rows to add to summary table')
                        else:
                            with arcpy.da.SearchCursor(totalPolygons, ['Machine','DL_Time','BlockName','Bucket','Hectares'],
                                                       where_clause = newRowsSelectionWhereClause,
                                                       sql_clause=(None, 'ORDER BY Machine,BlockName,Bucket')) as getNewPolygonsCursor:
                                with arcpy.da.InsertCursor(sumTotalRows,sumTableFieldNames) as sumTotalsCursor:
                                    rowList = []
                                    for row in getNewPolygonsCursor:
                                        newRow = list(row[0:5])
                                        rowSelection = 'Machine = ' + "'" + newRow[0] + "'" + ' And DL_Time = ' + "'" + newRow[1] + "'" + ' And BlockName = ' + "'" + newRow[2] + "'"
                                        lastPointsTime = [rowTime[0].encode('ascii','ignore') for rowTime in arcpy.da.SearchCursor(totalPoints,['Time'],rowSelection)][-1]
                                        newRow.append(lastPointsTime[11:19])
                                        sourceTxtFileDir = os.path.join(parentDestinationDirectory,newRow[0],newRow[1],newRow[2])
                                        if not os.path.exists(sourceTxtFileDir):
                                            sourceTxtFileDir = os.path.join(parentDestinationDirectory,newRow[0],newRow[1])
                                        sourceTxtFile = [name for name in glob.glob(sourceTxtFileDir + r'\*.txt')][0]
                                        if linecache.getline(sourceTxtFile,1)[:8] == 'Distance':
                                            nomArea = float(linecache.getline(sourceTxtFile,3)[19:-3].strip())
                                            realArea = float(linecache.getline(sourceTxtFile,4)[19:-3].strip())
                                            distanceFlown = float(linecache.getline(sourceTxtFile,1)[20:-3].strip())
                                            distanceSpread = float(linecache.getline(sourceTxtFile,2)[19:-3].strip())
                                            newRow.extend([nomArea, realArea, distanceFlown, distanceSpread])
                                        elif linecache.getline(sourceTxtFile,1)[:4] == 'Area':
                                            nomArea = float(linecache.getline(sourceTxtFile,1)[17:-3].strip())
                                            realArea = float(linecache.getline(sourceTxtFile,2)[17:-3].strip())
                                            distanceFlown = float(linecache.getline(sourceTxtFile,3)[19:-3].strip())
                                            distanceSpread = float(linecache.getline(sourceTxtFile,4)[19:-3].strip())
                                            newRow.extend([nomArea, realArea, distanceFlown, distanceSpread])
                                        if row[2].title() in blockAreaDict:
                                            newRow.append(blockAreaDict[row[2].title()])
                                        else:
                                            newRow.append(0)
                                            #arcpy.AddWarning('treatmentArea feature class does not contain a block called  ' + row[2].title() + '. Check your data!')
                                        rowList.append(newRow)
                                    firstRow = rowList[0]
                                    for row in rowList[1:]:
                                        if row[0:3] == firstRow[0:3]:
                                            row[4] = row[4] + firstRow[4]
                                            rowList.pop(rowList.index(row) - 1)
                                            firstRow = row
                                        else:
                                            firstRow = row
                                    for row in rowList:
                                        sumTotalsCursor.insertRow(row)

                            # Message advising how many rows added to the summary table
                            arcpy.AddMessage(str(len(rowList)) + ' rows added to ' + sumTotalRows)

                    # Delete the temporary feature classes
                    arcpy.Delete_management('newPointsSelection')
                    arcpy.Delete_management('newFlightPathRows')
                    arcpy.Delete_management('newRowsSelection')

                    # Update the symbology for the total_polygons layer with the newly added rows
                    totalPolygonsLyr = arcpy.mapping.Layer(totalPolygonsLyrFile)
                    totalPolygonsMxdLyr = arcpy.mapping.Layer(totalPolygonsLyr.name)
                    totalPolygonsMxdLyr.symbology.valueField = 'Machine'
                    totalPolygonsMxdLyr.symbology.addAllValues()
                    df.extent = totalPolygonsMxdLyr.getExtent()
                    arcpy.RefreshActiveView()

                del mxd, df

            # If user has ticked the createSummariesChkBox, create a dissolved by block and total dissolved fc and
            # a csv file summarising the polygon data
            elif createSummariesChkBx == True:

                # Dissolve the polygons to get an area covered by block
                # if any of rows don't have a block name, don't do a dissolve by block
                with arcpy.da.SearchCursor(totalPolygons,['BlockName']) as checkBlockName:
                    checkBlockNameList = []
                    for blockName in checkBlockName:
                        checkBlockNameList.append(blockName[0])
                    if '' not in checkBlockNameList:
                        dissolvedBlkFC = os.path.join(localGDB,'dissolved_by_block_') + str(time.strftime('%m%d%H%M'))
                        arcpy.Dissolve_management(totalPolygons,dissolvedBlkFC,'BlockName')
                        arcpy.AddField_management(dissolvedBlkFC,'Hectares','DOUBLE')
                        arcpy.CalculateField_management(dissolvedBlkFC,'Hectares','round(!SHAPE_area!/10000,4)','PYTHON_9.3', '')
                        dissolvedBlkFCLyr = arcpy.mapping.Layer(dissolvedBlkFC)
                        arcpy.mapping.AddLayer(df,dissolvedBlkFCLyr)
                        arcpy.AddMessage(dissolvedBlkFC + ' created and added to map')
                    else:
                        dissolvedBlkFC = False
                        arcpy.AddWarning('Some of the block name fields are empty - no dissolve by block undertaken')

                # Dissolve the polygons to get an overall area
                dissolvedTotalPolyFC = os.path.join(localGDB,'total_dissolved_') + str(time.strftime('%m%d%H%M'))
                arcpy.Dissolve_management(totalPolygons,dissolvedTotalPolyFC)
                arcpy.AddField_management(dissolvedTotalPolyFC,'Hectares','DOUBLE')
                arcpy.CalculateField_management(dissolvedTotalPolyFC,'Hectares','round(!SHAPE_area!/10000,4)','PYTHON_9.3', '')
                dissolvedTotalPolyFCLyr = arcpy.mapping.Layer(dissolvedTotalPolyFC)
                arcpy.mapping.AddLayer(df,dissolvedTotalPolyFCLyr)
                arcpy.AddMessage(dissolvedTotalPolyFC + ' created and added to map')

                # Order the sum_totals table by BlockName and Last_Log_Time and export to a csv file
                if dissolvedBlkFC != False:
                    csvTableFieldNames = sumTableFieldNames[2:]
                    csvTableFieldNames.append('Dissolved area')
                    csvTableFieldNames.append('Percentage sown')
                    csvFile = os.path.join(os.path.dirname(localGDB),'sum_totals_' + str(time.strftime('%H%M')) + '.csv')
                    with open(csvFile,'wb') as exportFile:
                        csvWrite = csv.writer(exportFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
                        csvWrite.writerow(csvTableFieldNames)
                        with arcpy.da.SearchCursor(sumTotalRows, sumTableFieldNames[2:], sql_clause=(None, 'ORDER BY BlockName, Last_log_time')) as csvOutput:
                            csvOutputList = []
                            for row in csvOutput:
                                csvOutputList.append(list(row))
                            rowCount = 0
                            for row in csvOutputList:
                                if rowCount == 0:
                                    dissolvedBlkArea = [blkArea for blkName, blkArea in arcpy.da.SearchCursor(dissolvedBlkFC,['BlockName','Hectares']) if blkName == row[0]]
                                    row.append(round(dissolvedBlkArea[0], 4))
                                    if row[8] != 0:
                                        row.append(round((row[2] / row[8]) * 100,2))
                                    else:
                                        row.append(0)
                                    firstRow = row
                                else:
                                    if row[0] == firstRow[0]:
                                        row[2] += firstRow[2]
                                        dissolvedBlkArea = [blkArea for blkName, blkArea in arcpy.da.SearchCursor(dissolvedBlkFC,['BlockName','Hectares']) if blkName == row[0]]
                                        row.append(round(dissolvedBlkArea[0], 4))
                                        if row[8] != 0:
                                            row.append(round((row[2] / row[8]) * 100,2))
                                        else:
                                            row.append(0)
                                        firstRow = row
                                    else:
                                        dissolvedBlkArea = [blkArea for blkName, blkArea in arcpy.da.SearchCursor(dissolvedBlkFC,['BlockName','Hectares']) if blkName == row[0]]
                                        row.append(round(dissolvedBlkArea[0], 4))
                                        if row[8] != 0:
                                            row.append(round((row[2] / row[8]) * 100,2))
                                        else:
                                            row.append(0)
                                        csvWrite.writerow(firstRow)
                                        firstRow = row
                                if rowCount + 1 == len(csvOutputList):
                                    csvWrite.writerow(row)
                                rowCount += 1
                            csvWrite.writerow('')
                            dissolvedTotalPolyArea = [totalArea for totalArea in arcpy.da.SearchCursor(dissolvedTotalPolyFC,['Hectares'])]
                            csvWrite.writerow(['Total dissolved area','','','','','','','','',dissolvedTotalPolyArea[0][0],''])

                    #
                    arcpy.AddMessage('sum_totals sorted and saved to ' + csvFile)
                else:
                    arcpy.AddWarning('Some of the block name fields are empty - no summary csv file created')

        except IOError as iOErr:
            arcpy.AddError(iOErr.message)

        except ValueError as valErr:
            arcpy.AddError(valErr.message)

        except Exception as e:
            # Return geoprocessing tool specific errors
            for msg in range(0, arcpy.GetMessageCount()):
                if arcpy.GetSeverity(msg) == 2:
                    arcpy.AddReturnMessage(msg)
            # Also return the line number and error message
            import traceback, sys
            tb = sys.exc_info()[2]
            arcpy.AddError("Line {0}".format(tb.tb_lineno))
            arcpy.AddError(e.message)
        return

class Enter_or_update_operation_metadata(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""

        self.label = 'Enter or update operation metadata'
        self.description = 'Enter or update info on the helicopters used in the operation'
        self.canRunInBackground = True

    def getParameterInfo(self):
        """Define parameter definitions"""

        parametersFilePath = os.path.join(os.path.dirname(__file__),'parameters.csv')
        linecache.updatecache(parametersFilePath)

        # parameter 0
        localGDB = arcpy.Parameter(
            displayName="File geodatabase where the processed data from the helicopter will be stored",
            name="in_workspace",
            datatype="DEWorkspace",
            parameterType="Optional",
            direction="Input")
        localGDB.value = linecache.getline(parametersFilePath,5)[:-1]

        # Set the filter to accept only local (personal or file) geodatabases
        localGDB.filter.list = ["Local Database"]

        # parameter 1
        operationStartTime = arcpy.Parameter(
            displayName = 'Enter the time the operation went "'"Toxic"'" i.e 0910',
            name = 'data_source_location',
            datatype = 'GPString',
            parameterType = 'Optional',
            direction = 'Input')

        # parameter 2
        helicopterInfo = arcpy.Parameter(
            displayName = 'Enter the helicopter registration number',
            name = 'helicopter_info',
            datatype = 'GPValueTable',
            parameterType = 'Optional',
            direction = 'Input')
        helicopterInfo.columns = [['GPString','RegNo'],['GPString','Pilot Name'],['GPString','Helicopter Type'],['Long','Bucket Size (kg)'],['Double','Sow rate (kg/ha)']]# Long for Bucket and Double for Sow rate
        helicopterInfo.filters[2].type = 'ValueList'
        helicopterInfo.filters[2].list = ['Unknown','Bell 206B Jetranger','Bell 206L-4 Longranger','Bell UH-1H Iroquois','Eurocopter AS350 B2','Eurocopter AS350 B3','Eurocopter AS350 BA','Eurocopter AS355 BA','Kawasaki BK117 B-2','McDonnel Douglas 500N','Robinson R44','Other']
        helicopterInfo.filters[3].type = 'ValueList'
        helicopterInfo.filters[3].list = [0,150,300,500,600,900,1200]
        helicopterInfo.filters[4].type = 'ValueList'
        helicopterInfo.filters[4].list = [0,1,1.5,2,2.5,3.0]

        params = [localGDB,operationStartTime,helicopterInfo]

        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute.
           An arceditor or arcinfo licence is required to fully utilise this tool, specifically
           the ImportXMLWorkspaceDocument_management function used to add the empty feature classes
           and tables to the new file geodatabase or new fc's and tables to an existing file geodatabase"""
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
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""

        localGDB = parameters[0].valueAsText
        operationStartEndTimeTbl = os.path.join(localGDB,'operation_start_end_time')
        if parameters[1].altered:
            startTimeText = parameters[1].valueAsText
            if len([startTime for startTime in arcpy.da.SearchCursor(operationStartEndTimeTbl,['Operation_Start_Time'])]) > 0:
                parameters[1].setWarningMessage('There is already an entry for this. Existing entries will be overwritten.')
            try:
                time.strptime(startTimeText,'%H%M')
            except:
                raise ValueError('This is not a valid time format')

        if parameters[2].altered:
##            if parameters[1].valueAsText is None:
##                if len([startTime for startTime in arcpy.da.SearchCursor(operationStartEndTimeTbl,['Operation_Start_Time'])]) == 0:
##                    parameters[1].setErrorMessage('Please enter an operation start time')
            regNo = parameters[2].valueAsText
            if regNo[3] != ' ':
                parameters[2].setErrorMessage('Helicopter Reg No. must be 3 characters only i.e. HBC')
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        localGDB = parameters[0].valueAsText
        operationStartTime = parameters[1].valueAsText
        helicopterInfo = parameters[2].value
        operationStartEndTimeTbl = os.path.join(localGDB,'operation_start_end_time')
        helicopterInfoTbl = os.path.join(localGDB,'helicopter_info')

        #
        try:

            #
            if operationStartTime is not None:
                if len([startTime for startTime in arcpy.da.SearchCursor(operationStartEndTimeTbl,['Operation_Start_Time'])]) > 0:
                    arcpy.AddWarning(os.path.basename(operationStartEndTimeTbl) + ' can only contain 1 start time entry. Existing entrys will be deleted')
                    with arcpy.da.UpdateCursor(operationStartEndTimeTbl,['Operation_Start_Time']) as deleteEntries:
                        for row in deleteEntries:
                            deleteEntries.deleteRow()
                with arcpy.da.InsertCursor(operationStartEndTimeTbl,['Operation_Start_Time']) as insertOpStartTime:
                    startTime = time.strftime('%d/%m/%Y') + ' ' + operationStartTime[:2] + ':' + operationStartTime[-2:]  + ':00'
                    insertOpStartTime.insertRow([startTime])
                arcpy.AddMessage(startTime + ' added to ' + operationStartEndTimeTbl)

            #
            heliInfoFieldNames = [heli.name for heli in arcpy.ListFields(helicopterInfoTbl)]

            if helicopterInfo is not None:
                with arcpy.da.InsertCursor(helicopterInfoTbl,heliInfoFieldNames[1:]) as insertHeliInfo:
                    for heli in helicopterInfo:
                        insertHeliInfo.insertRow(heli)
                arcpy.AddMessage('Helicopter info added to ' + helicopterInfoTbl)

        except IOError as iOErr:
            arcpy.AddError(iOErr.message)

        except ValueError as valErr:
            arcpy.AddError(valErr.message)

        except Exception as e:
            # Return geoprocessing tool specific errors
            for msg in range(0, arcpy.GetMessageCount()):
                if arcpy.GetSeverity(msg) == 2:
                    arcpy.AddReturnMessage(msg)
            # Also return the line number and error message
            import traceback, sys
            tb = sys.exc_info()[2]
            arcpy.AddError("Line {0}".format(tb.tb_lineno))
            arcpy.AddError(e.message)
        return
