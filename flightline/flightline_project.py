import os
from flightline import folder_handler
from flightline import config_handler
from flightline import featureclass_handler
import json
import arcpy
import time
from distutils import dir_util

# Main class that manages the flightline project


class FlightlineProject(object):


    def __init__(self, project_folder):
        #TODO remove hardcoded values below into .json file
        self.project_folder = None
        self.__load_project_folder__(project_folder)
        self.project_setup_json = None
        self.__projectconfig_name__ = "projectconfig.json"
        self.__config_folder_name__ = "Config"
        self.__data_folder_name__ = 'Data'
        self.__maps_folder_name__ = "Maps"
        self.__tracmap_data_folder_name__ = 'TracMapData'
        self.__config_attributes__ = {}
        self.__flight_data_gdb_name__ = "FlightData.gdb"
        self.__operation_times_table_name__ = "operation_start_end_time"
        self.__operation_start_times_table_field_name__ = "Operation_Start_Time"
        self.__helicopter_info_table_name__ = "helicopter_info"
        self.__helicopter_info_regno_field_name__ = "helicopter_registration_no"
        self.__total_points_lyr_name__ = "total_points.lyr"
        self.__total_lines_lyr_name__ = "total_lines.lyr"
        self.__flight_path_lyr_name__ = "flight_path.lyr"
        self.__total_polygons_lyr_name__ = "total_polygons.lyr"
        self.__total_points_fc_name__ = "total_points"
        self.__total_lines_fc_name__ = "total_lines"
        self.__total_polygons_fc_name__ = "total_polygons"
        self.__flight_path_fc_name__ = "flight_path"
        self.__sum_totals_table_name__ = "sum_totals"
        self.__tracmap_data_projection__ = 4326
        self.__block_field_name__ = 'HeliBlkNm'

        self.operation_start_time = None
        self.operation_start_datetime = None
        self.default_tracmap_data_projection = None
        self.default_tracmap_destination_parent_directory = None
        self.treatment_area_featureclass = None
        self.sum_total_fieldnames = ['Machine','DL_Time','BlockName','Bucket','Hectares','Last_log_time',
                              'Nominal_Area','Real_Area','Distance_Travelled','Distance_spreading','Block_Area']
        self.flight_gdb_datasets = ['total_points','total_lines','total_polygons','flight_path','sum_totals','helicopter_info','operation_start_end_time']
        self.required_flight_data_fcs = ['total_points','total_lines','total_polygons','flight_path']
        self.flight_gdb_xml_file_name = 'total_gdb.xml'

        self.csv_summaries = []
        self.copied_tracmap_datasets = []
        self.flight_data_gdbs = [self.__flight_data_gdb_name__]

    @property
    def flight_data_required_fc_populated(self):
        """Determines if the required featureclasses have records in them or not"""
        record_counts = []
        for i in self.required_flight_data_fcs:
            fc = os.path.join(self.flight_data_gdb_location, i)
            record_counts.append(self.project_folder_handler.get_fc_record_count(fc))
        if sum(record_counts) > 0:
            return True
        else:
            return False

    @property
    def flightdata_gdb_xml_location(self):
        # Since the flightdata.gdb can be changed, the name used to get the xml
        # file is from the default gdb name which is the first in the self.flight_data_gdbs
        return os.path.join(self.config_folder_location, self.flight_gdb_xml_file_name)

    @property
    def default_tracmap_data_projection_name(self):
        return featureclass_handler.epsg_to_projection_name(self.__tracmap_data_projection__)

    @property
    def default_tracmap_data_projection_system(self):
        return featureclass_handler.spatial_reference(self.__tracmap_data_projection__)

    @property
    def data_folder_location(self):
        return os.path.join(self.project_folder, self.__data_folder_name__)
    @property
    def config_folder_location(self):
        return os.path.join(self.project_folder, self.__config_folder_name__)
    @property
    def maps_folder_location(self):
        return os.path.join(self.project_folder, self.__maps_folder_name__)
    @property
    def project_config_location(self):
        return os.path.join(self.project_folder,self.__projectconfig_name__)

    @property
    def total_polygons_fc(self):
        return os.path.join(self.flight_data_gdb_location, self.__total_polygons_fc_name__)
    @property
    def total_points_fc(self):
        return os.path.join(self.flight_data_gdb_location, self.__total_points_fc_name__)
    @property
    def total_lines_fc(self):
        return os.path.join(self.flight_data_gdb_location, self.__total_lines_fc_name__)
    @property
    def flight_path_fc(self):
        return os.path.join(self.flight_data_gdb_location, self.__flight_path_fc_name__)
    @property
    def total_points_layer(self):
        return os.path.join(self.maps_folder_location, self.__total_points_lyr_name__)
    @property
    def total_lines_layer(self):
        return os.path.join(self.maps_folder_location, self.__total_lines_lyr_name__)
    @property
    def total_polygons_layer(self):
        return os.path.join(self.maps_folder_location, self.__total_polygons_lyr_name__)
    @property
    def flight_path_layer(self):
        return os.path.join(self.maps_folder_location, self.__flight_path_lyr_name__)

    @property
    def helicopter_info_table(self):
        return os.path.join(self.flight_data_gdb_location, self.__helicopter_info_table_name__)

    def set_operation_start_date_time(self):
        if not self.operation_start_time:
            return
        self.operation_start_datetime = "{0} {1}:{2}:00".format(time.strftime('%Y-%m-%d'),self.operation_start_time[:2], self.operation_start_time[-2:])

    @property
    def helicopter_regno_list(self):
        records_list = []
        with arcpy.da.SearchCursor(self.helicopter_info_table, [self.__helicopter_info_regno_field_name__]) as cursor:
            for row in cursor:
                records_list.append(row[0])
        return records_list

    @property
    def flightline_total_points_fc(self):
        return os.path.join(self.flight_data_gdb_location, self.__total_points_fc_name__)
    @property
    def flightline_total_lines_fc(self):
        return os.path.join(self.flight_data_gdb_location, self.__total_lines_fc_name__)
    @property
    def flightline_total_polygons_fc(self):
        return os.path.join(self.flight_data_gdb_location, self.__total_polygons_fc_name__)
    @property
    def flightline_flight_path_fc(self):
        return os.path.join(self.flight_data_gdb_location, self.__flight_path_fc_name__)
    @property
    def flightline_sum_totals_table(self):
        return os.path.join(self.flight_data_gdb_location, self.__sum_totals_table_name__)

    @property
    def operation_times_table(self):
        return os.path.join(self.flight_data_gdb_location, self.__operation_times_table_name__)

    @property
    def operation_times_table_records(self):
        records_list = []
        with arcpy.da.SearchCursor(self.operation_times_table,[self.__operation_start_times_table_field_name__]) as cursor:
            for row in cursor:
                records_list.append(row[0])
        return records_list

    @property
    def tracmap_data_folder_location(self):
        return os.path.join(self.project_folder, self.__tracmap_data_folder_name__)

    @property
    def flight_data_gdb_location(self):
        return os.path.join(self.project_folder, self.__flight_data_gdb_name__)

    @property
    def projectconfig_json_exists(self):
        """Looks in current folder for a projectconfig.json file"""
        if not self.project_folder:
            return False
        return self.__projectconfig_name__ in [f.lower() for f in os.listdir(self.project_folder)]

    @property
    def valid_project_folder(self):
        if self.project_folder:
            if os.path.exists(self.project_folder):
                return True
        return False

    @property
    def project_folder_empty(self):
        """Determines if the project folder is empty"""
        if not self.project_folder:
            return False
        return not bool(len(os.listdir(self.project_folder)))

    @property
    def list_tool_setting_json_files(self):
        """Searches the configs folder for .json files"""
        basefolder = os.path.join(self.project_folder,self.__config_folder_name__)
        return [os.path.join(basefolder,i) for i in os.listdir(basefolder) if i.lower().endswith('.json')]

    @property
    def project_folder_handler(self):
        return folder_handler.FolderHandler(self.project_folder)

    def __load_project_folder__(self, project_folder):
        """Checks if project_folder exists"""
        if project_folder:
            if os.path.exists(project_folder):
                self.project_folder = project_folder
            else:
                raise SystemError("{0} does not exist".format(project_folder))

    def add_new_flight_data_gdb_name(self, gdb_name):
        """
        Records the flight data gdbs that have been used.
        """
        self.__flight_data_gdb_name__ = gdb_name
        self.flight_data_gdbs.append(gdb_name)

    def rename_required_flight_data_gdb_fcs(self):
        """
        Renames the required featureclasses in the flight data gdb
        This allows new datasets to be loaded in.
        """
        dataset_list = [os.path.join(self.flight_data_gdb_location, i) for i in self.required_flight_data_fcs ]
        featureclass_handler.rename_flight_data_datasets(self.flight_data_gdb_location, dataset_list)

    def add_copied_data_to_mxd(self, mxd, df):
        """
        Adds presaved layer files to current mxd, and updates the datasource to projects data
        if the layres are not already present
        """
        # TODO - Remove the hardcoded layer values, use self.requried_fcs list.
        # TODO - Move this out to a new module called map_handler or into the featureclass_handler
        # there shouldn't be any reference to arcpy within this module.
        layer_list = [lyr.dataSource for lyr in arcpy.mapping.ListLayers(mxd, '*', df) if lyr.supports("DATASOURCE")]
        check_lyr_dict = {self.total_points_fc: self.total_points_layer,
                          self.total_polygons_fc: self.total_polygons_layer,
                          self.total_lines_fc: self.total_lines_layer,
                          self.flight_path_fc: self.flight_path_layer}

        for lyr in check_lyr_dict.iteritems():
            if lyr[0] not in layer_list:
                new_lyr = arcpy.mapping.Layer(lyr[1])
                # Change the datasource to the current gdb
                new_lyr.replaceDataSource(workspace_path=os.path.dirname(lyr[0]),
                                         workspace_type="FILEGDB_WORKSPACE",
                                         dataset_name=os.path.basename(lyr[0]))
                arcpy.mapping.AddLayer(df, new_lyr, "TOP")

    def copy_tracmap_data(self, source_folder, helicopter_rego, download_time):
        """
        Copies tracmap helicopter data from source folder into the projects tracmap data store folder
        Parameters
        ---------
        source_folder : str - Folder location where the tarcmap data is coming from
        helicopter_rego : str - 3 character string, must exist in the helicopters table
        download_time : str - Time of download eg 0910

        Returns
        -------
        result : boolean
        """
        os.chdir(self.tracmap_data_folder_location)
        destination_directory = os.path.join(self.tracmap_data_folder_location, helicopter_rego, download_time)
        if destination_directory in self.copied_tracmap_datasets:
            return False
        self.copied_tracmap_datasets.append(destination_directory)
        if not os.path.exists(helicopter_rego):
            os.mkdir(helicopter_rego)
        os.chdir(helicopter_rego)
        if not os.path.exists(download_time):
            dir_util.copy_tree(source_folder, destination_directory)

        return True

    @staticmethod
    def merge_tracmap_data_to_flight_data_gdb(shapefile_name, downloaded_data_directory, destination_featureclass, coordinate_system):
        """
        Merges data from the specified shapefile into the flight data gdb datasets

        Parameters
        ----------
        shapefile_name : str - eg.. log.shp, secondary.shp
        downloaded_data_directory : str - eg. ./TracMapData/HelicopterRego/DownloadTime
        destination_featureclass : str - Location of the destination_featureclass featureclass
        coordinate_system - arcpy.SpatialReference()

        Returns
        -------
        data_merged : boolean
        """

        # Get list of shapefiles in the download_data_directory
        shapefile_list = featureclass_handler.directory_shapefile_list(shapefile_name, downloaded_data_directory)
        # Loop through each shapefile
        for shapefile in shapefile_list:
            # Get feature count, if empty then don't process shapefile
            feature_count = featureclass_handler.featureclass_record_count(shapefile)
            if feature_count == 0:
                # TODO post warning saying shapefile contains no data
                continue
            # Get shapetype, make sure is of type 'Polyline', 'Point'
            shape_type = featureclass_handler.featureclass_shape_type(shapefile)
            if shape_type not in ['Polyline','Point']:
                # TODO post error saying that shapefile is not of type Polyline
                continue
            # Repair the geometry
            featureclass_handler.repair_geometry(shapefile)

            # Define the projection if not alreay defined
            featureclass_handler.define_projection(shapefile, coordinate_system)

            # Merge the tracmap data
            featureclass_handler.merge_tracmap_data_featureclass(downloaded_data_directory, shapefile, destination_featureclass)

    def update_total_lines_featureclass(self, helicopter_rego, download_time, deflector):
        """
        Updates the total lines featureclass
        """
        result = featureclass_handler.update_totallines_featureclass(self.total_lines_fc,
                                                            self.total_polygons_fc,
                                                            helicopter_rego,
                                                            download_time,
                                                            deflector)
        return result

    def update_total_points_featureclass(self, helicopter_rego, download_time, deflector):
        """
        Updates the total points featureclass with helicopter and time attributes
        """
        result = featureclass_handler.update_totalpoints_featureclass(
            self.total_points_fc,
            helicopter_rego,
            download_time)

        return result

    def covert_secondary_points_to_lines(self, helicopter_rego, download_time):
        """Generates lines from the secondary points feature class"""

        # Check if there are any new records to add or not

        records_added = featureclass_handler.convert_secondary_points_to_lines(self.total_points_fc,
                                                               self.total_lines_fc,
                                                               self.flight_path_fc,
                                                               self.operation_times_table,
                                                               helicopter_rego,
                                                               download_time)
        return records_added

    def summarize_flight_data(self, df):
        """Summarizes flight data for data loaded to date"""

        flight_data_gdb = self.flight_data_gdb_location
        total_polygons = self.total_polygons_fc
        sum_total_rows = self.flightline_sum_totals_table

        sum_table_field_names = self.sum_total_fieldnames

        results = featureclass_handler.summarize_flight_data(flight_data_gdb, total_polygons, sum_total_rows, df, sum_table_field_names)

        self.csv_summaries.append(results)

    def summarize_new_flight_data(self, helicopter_rego, download_time, df):
        """
        For newly added tracmap data this creaes a summary.txt file and
        adds a new record to the sum_totals_table
        """
        total_lines = self.total_lines_fc
        total_points = self.total_points_fc
        total_polygons = self.total_polygons_fc
        tracmap_data_folder = self.tracmap_data_folder_location
        sum_totals_table = self.flightline_sum_totals_table
        sum_totals_field_names = self.sum_total_fieldnames
        total_polygons_lyr_file = self.total_polygons_layer

        block_area_dict = featureclass_handler.feature_class_as_dict(self.treatment_area_featureclass, self.__block_field_name__, ['Hectares'])

        results = featureclass_handler.new_flight_data_summary(total_lines,
                                                    total_points,
                                                    total_polygons,
                                                    tracmap_data_folder,
                                                    helicopter_rego,
                                                    download_time,
                                                    sum_totals_table,
                                                    sum_totals_field_names,
                                                    block_area_dict,
                                                    df,
                                                    total_polygons_lyr_file)

        if results:
            self.csv_summaries.append(results)

        return results

    def xml_file_location(self, xml_name):
        """Returns the location of an xml file based on the input name"""
        return os.path.join(self.project_folder, self.__config_folder_name__, "{0}.xml".format(xml_name))

    def create_flight_data_gdb(self, gdb_name):
        """Creates an empty flight data gdb with the name specified"""
        self.project_folder_handler.__create_file_geodatabase__(gdb_name, self.flightdata_gdb_xml_location)

    def create_flight_gdb_datasets(self):
        """Creates the required featureclasses from xml files into the flight_data.gdb"""
        for x in self.required_flight_data_fcs:
            xml_file = self.xml_file_location(x)
            self.project_folder_handler.__create_gdb_dataset__(self.flight_data_gdb_location, xml_file)

    def get_config_attribute(self, attribute_name):
        """Retrieves the value of a attribute in __config_attributes__"""
        if self.__config_attributes__.has_key(attribute_name):
            return self.__config_attributes__[attribute_name]
        else:
            raise KeyError("Attribute name: {0} not in __config_attributes__".format(attribute_name))

    def __load_tool_setting_file__(self, json_file):
        """Loads the json file key value pairs into self"""
        json_file = open(json_file)
        json_dict = json.load(json_file)
        json_file.close()

        for key in json_dict.keys():
            self.__config_attributes__[key] = json_dict[key]

    def load_tool_setting_json_files(self):
        """Loads key value pairs from config json files into self"""
        # First delete any current attributes
        self.__config_attributes__ = {}

        for config in self.list_tool_setting_json_files:
            self.__load_tool_setting_file__(config)

    def setup_folder_structure(self, json_file, overwrite=False):
        """Sets up the project folder structure based on a json file"""
        project_folder_handler = self.project_folder_handler
        project_folder_handler.load_settings_file(json_file, overwrite)
        project_folder_handler.create_structure()

    def dump_to_projectconfig(self):
        """
        Dumps the key value pairs into the projectconfig.json file
        Overwrite will update existing key values with new values
        """
        config_handler.dump_to_projectconfig(self, self.project_config_location)

    def load_from_projectconfig(self):
        """Loads from the projectconfig json file into the self"""
        config_handler.load_from_projectconfig(self, self.project_config_location)








