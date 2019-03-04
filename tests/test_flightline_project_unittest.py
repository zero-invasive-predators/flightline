import unittest
import os
import shutil
import uuid
import time
import tempfile

from flightline import flightline_project

class Resources():

    wgs84_name = u'GCS_WGS_1984'
    wgs84_system = u"GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]];-400 -400 1000000000;-100000 10000;-100000 10000;8.98315284119522E-09;0.001;0.001;IsHighPrecision"

    project_setup_json_name = 'ProjectSetup.json'

    @staticmethod
    def generate_temp_space():
        """
        Provides a temp name, temp directory name and uniqueid

        Returns
        -------
        [temp_name, temp_directory_name, unique_id]
        """
        temp_name = tempfile.mkdtemp()
        temp_directory_name = os.path.dirname(temp_name)
        unique_id = uuid.uuid1().clock_seq
        return [temp_name, temp_directory_name, unique_id]

    @staticmethod
    def get_test_data_folder():
        cwd = os.getcwd()
        if os.path.basename(cwd).lower() == 'tests':
            return os.path.join(os.getcwd(), 'test_data')
        elif os.path.basename(cwd).lower() == 'flightline':
            return os.path.join(os.getcwd(), 'tests','test_data')
        else:
            return os.getcwd()





class TestFlightlineProject(unittest.TestCase):

    def setUp(self):
        self.temp_name, self.temp_directory, self.unique_id = Resources.generate_temp_space()
        self.flightline_project_obj = flightline_project.FlightlineProject(self.temp_name)

    def tearDown(self):
        shutil.rmtree(self.temp_directory, ignore_errors=True)

    def test_create_flightline_project_instance(self):

        self.assertIsInstance(self.flightline_project_obj, flightline_project.FlightlineProject, msg = "Created instance not flightline_project.FligthlineProject")

    def test_flightline_project_attributes(self):
        flp = self.flightline_project_obj

        self.assertEqual(flp.project_folder, self.temp_name, msg = "Project folder attribute. Expected: {0} Got: {1}".format(self.temp_name, flp.project_folder))
        self.assertEqual(flp.project_setup_json, None, msg = "project_setup_json attribute. Expected: {0} Got: {1}".format(None, flp.project_setup_json))
        self.assertEqual(flp.__projectconfig_name__, 'projectconfig.json', msg = "__projectconfig_name__ attribute. Expected: {0} Got: {1}".format('projectconfig.json', flp.__projectconfig_name__))
        self.assertEqual(flp.__config_folder_name__, 'Config', msg = "__config_folder_name__ attribute. Expected: {0} Got: {1}".format('Config', flp.__config_folder_name__))
        self.assertEqual(flp.__data_folder_name__, 'Data', msg = "__data_folder_name__ attribute. Expected: {0} Got: {1}".format('Config', flp.__config_folder_name__))
        self.assertEqual(flp.__maps_folder_name__, 'Maps', msg = "__maps_folder_name__ attribute. Expected: {0} Got: {1}".format('Maps', flp.__maps_folder_name__))
        self.assertEqual(flp.__tracmap_data_folder_name__, 'TracMapData', msg = "__tracmap_data_folder_name__ attribute. Expected: {0} Got: {1}".format('TracMapData', flp.__tracmap_data_folder_name__))
        self.assertEqual(flp.__config_attributes__, {}, msg = "__config_attributes__ attribute. Expected: {0} Got: {1}".format({}, flp.__config_attributes__))
        self.assertEqual(flp.__flight_data_gdb_name__, 'FlightData.gdb', msg = "__flight_data_gdb_name__ attribute. Expected: {0} Got: {1}".format('FlightData.gdb', flp.__flight_data_gdb_name__))
        self.assertEqual(flp.__operation_times_table_name__, 'operation_start_end_time', msg = "__operation_times_table_name__ attribute. Expected: {0} Got: {1}".format('operation_start_end_time', flp.__operation_times_table_name__))
        self.assertEqual(flp.__operation_start_times_table_field_name__, 'Operation_Start_Time', msg = "__operation_start_times_table_field_name__ attribute. Expected: {0} Got: {1}".format('Operation_Start_Time', flp.__operation_start_times_table_field_name__))
        self.assertEqual(flp.__helicopter_info_table_name__, 'helicopter_info', msg = "__helicopter_info_table_name__ attribute. Expected: {0} Got: {1}".format('helicopter_info', flp.__helicopter_info_table_name__))
        self.assertEqual(flp.__helicopter_info_regno_field_name__, 'helicopter_registration_no', msg = "__helicopter_info_regno_field_name__ attribute. Expected: {0} Got: {1}".format('helicopter_registration_no', flp.__helicopter_info_regno_field_name__))
        self.assertEqual(flp.__total_points_lyr_name__, 'total_points.lyr', msg = "__total_points_lyr_name__ attribute. Expected: {0} Got: {1}".format('total_points.lyr', flp.__total_points_lyr_name__))
        self.assertEqual(flp.__total_lines_lyr_name__, 'total_lines.lyr', msg = "__total_lines_lyr_name__ attribute. Expected: {0} Got: {1}".format('total_lines.lyr', flp.__total_lines_lyr_name__))
        self.assertEqual(flp.__flight_path_lyr_name__, 'flight_path.lyr', msg = "__flight_path_lyr_name__ attribute. Expected: {0} Got: {1}".format('flight_path.lyr', flp.__flight_path_lyr_name__))
        self.assertEqual(flp.__total_polygons_lyr_name__, 'total_polygons.lyr', msg = "__total_polygons_lyr_name__ attribute. Expected: {0} Got: {1}".format('total_polygons.lyr', flp.__total_polygons_lyr_name__))
        self.assertEqual(flp.__total_points_fc_name__, 'total_points', msg = "__total_points_fc_name__ attribute. Expected: {0} Got: {1}".format('total_points', flp.__total_points_fc_name__))
        self.assertEqual(flp.__total_lines_fc_name__, 'total_lines', msg = "__total_lines_fc_name__ attribute. Expected: {0} Got: {1}".format('total_lines', flp.__total_lines_fc_name__))
        self.assertEqual(flp.__total_polygons_fc_name__, 'total_polygons', msg = "__total_polygons_fc_name__ attribute. Expected: {0} Got: {1}".format('total_polygons', flp.__total_polygons_fc_name__))
        self.assertEqual(flp.__flight_path_fc_name__, 'flight_path', msg = "__flight_path_fc_name__ attribute. Expected: {0} Got: {1}".format('flight_path', flp.__flight_path_fc_name__))
        self.assertEqual(flp.__sum_totals_table_name__, 'sum_totals', msg = "__sum_totals_table_name__ attribute. Expected: {0} Got: {1}".format('sum_totals', flp.__sum_totals_table_name__))
        self.assertEqual(flp.__tracmap_data_projection__, 4326, msg = "__tracmap_data_projection__ attribute. Expected: {0} Got: {1}".format(4326, flp.__tracmap_data_projection__))
        self.assertEqual(flp.__block_field_name__, 'HeliBlkNm', msg = "__block_field_name__ attribute. Expected: {0} Got: {1}".format('HeliBlkNm', flp.__block_field_name__))
        self.assertEqual(flp.operation_start_time, None, msg = "operation_start_time attribute. Expected: {0} Got: {1}".format(None, flp.operation_start_time))
        self.assertEqual(flp.operation_start_datetime, None, msg = "operation_start_datetime attribute. Expected: {0} Got: {1}".format(None, flp.operation_start_datetime))
        self.assertEqual(flp.default_tracmap_data_projection, None, msg = "default_tracmap_data_projection attribute. Expected: {0} Got: {1}".format(None, flp.default_tracmap_data_projection))
        self.assertEqual(flp.default_tracmap_destination_parent_directory, None, msg = "default_tracmap_destination_parent_directory attribute. Expected: {0} Got: {1}".format(None, flp.default_tracmap_destination_parent_directory))
        self.assertEqual(flp.treatment_area_featureclass, None, msg = "treatment_area_featureclass attribute. Expected: {0} Got: {1}".format(None, flp.treatment_area_featureclass))
        self.assertEqual(flp.sum_total_fieldnames, ['Machine','DL_Time','BlockName','Bucket','Hectares','Last_log_time',
                              'Nominal_Area','Real_Area','Distance_Travelled','Distance_spreading','Block_Area'], msg = "sum_total_fieldnames attribute. Expected: {0} Got: {1}".format(['Machine','DL_Time','BlockName','Bucket','Hectares','Last_log_time',
                              'Nominal_Area','Real_Area','Distance_Travelled','Distance_spreading','Block_Area'], flp.sum_total_fieldnames))
        self.assertEqual(flp.flight_gdb_datasets, ['total_points','total_lines','total_polygons','flight_path','sum_totals','helicopter_info','operation_start_end_time'], msg = "flight_gdb_datasets attribute. Expected: {0} Got: {1}".format(['total_points','total_lines','total_polygons','flight_path','sum_totals','helicopter_info','operation_start_end_time'], flp.flight_gdb_datasets))
        self.assertEqual(flp.required_flight_data_fcs, ['total_points','total_lines','total_polygons','flight_path'], msg = "required_flight_data_fcs attribute. Expected: {0} Got: {1}".format(['total_points','total_lines','total_polygons','flight_path'], flp.required_flight_data_fcs))
        self.assertEqual(flp.flight_gdb_xml_file_name, 'total_gdb.xml', msg = "flight_gdb_xml_file_name attribute. Expected: {0} Got: {1}".format('total_gdb.xml', flp.flight_gdb_xml_file_name))
        self.assertEqual(flp.csv_summaries, [], msg = "csv_summaries attribute. Expected: {0} Got: {1}".format([], flp.csv_summaries))
        self.assertEqual(flp.copied_tracmap_datasets, [], msg = "copied_tracmap_datasets attribute. Expected: {0} Got: {1}".format([], flp.copied_tracmap_datasets))
        self.assertEqual(flp.flight_data_gdbs, ['FlightData.gdb'], msg = "flight_data_gdbs attribute. Expected: {0} Got: {1}".format(['FlightData.gdb'], flp.flight_data_gdbs))

    def test_flightline_project_properties(self):
        flp = self.flightline_project_obj

        #self.assertFalse(flp.flight_data_required_fc_populated, msg = "Property flight_data_required_fc_populated: Expected: {0} Got: {1}".format(False, flp.flight_data_required_fc_populated))
        self.assertEquals(flp.flightdata_gdb_xml_location, os.path.join(self.temp_name, flp.__config_folder_name__, flp.flight_gdb_xml_file_name), msg = "Property flight_data_required_fc_populated: Expected: {0} Got: {1}".format(os.path.join(self.temp_name, flp.__config_folder_name__, flp.flight_gdb_xml_file_name), flp.flightdata_gdb_xml_location))

        self.assertEquals(flp.default_tracmap_data_projection_name, Resources.wgs84_name, msg = "Property default_tracmap_data_projection_name: Expected: {0} Got: {1}".format(Resources.wgs84_name, flp.default_tracmap_data_projection_name))
        self.assertEquals(flp.default_tracmap_data_projection_system, Resources.wgs84_system, msg = "Property default_tracmap_data_projection_system: Expected: {0} Got: {1}".format(Resources.wgs84_system, flp.default_tracmap_data_projection_system))
        self.assertEquals(flp.data_folder_location, os.path.join(self.temp_name, flp.__data_folder_name__), msg = "Property data_folder_location: Expected: {0} Got: {1}".format(os.path.join(self.temp_name, flp.__data_folder_name__), flp.data_folder_location))
        self.assertEquals(flp.config_folder_location, os.path.join(self.temp_name, flp.__config_folder_name__), msg = "Property config_folder_location: Expected: {0} Got: {1}".format(os.path.join(self.temp_name, flp.__config_folder_name__), flp.config_folder_location))
        self.assertEquals(flp.maps_folder_location, os.path.join(self.temp_name, flp.__maps_folder_name__), msg = "Property maps_folder_location: Expected: {0} Got: {1}".format(os.path.join(self.temp_name, flp.__maps_folder_name__), flp.maps_folder_location))
        self.assertEquals(flp.project_config_location, os.path.join(self.temp_name, flp.__projectconfig_name__), msg = "Property project_config_location: Expected: {0} Got: {1}".format(os.path.join(self.temp_name, flp.__projectconfig_name__), flp.project_config_location))
        self.assertEquals(flp.total_polygons_fc, os.path.join(self.temp_name, flp.__flight_data_gdb_name__, flp.__total_polygons_fc_name__), msg = "Property total_polygons_fc: Expected: {0} Got: {1}".format(os.path.join(self.temp_name, flp.__flight_data_gdb_name__, flp.__total_polygons_fc_name__), flp.total_polygons_fc))
        self.assertEquals(flp.total_points_fc, os.path.join(self.temp_name, flp.__flight_data_gdb_name__, flp.__total_points_fc_name__), msg = "Property total_points_fc: Expected: {0} Got: {1}".format(os.path.join(self.temp_name, flp.__flight_data_gdb_name__, flp.__total_points_fc_name__), flp.total_points_fc))
        self.assertEquals(flp.total_lines_fc, os.path.join(self.temp_name, flp.__flight_data_gdb_name__, flp.__total_lines_fc_name__), msg = "Property total_lines_fc: Expected: {0} Got: {1}".format(os.path.join(self.temp_name, flp.__flight_data_gdb_name__, flp.__total_lines_fc_name__), flp.total_lines_fc))
        self.assertEquals(flp.flight_path_fc, os.path.join(self.temp_name, flp.__flight_data_gdb_name__, flp.__flight_path_fc_name__), msg = "Property flight_path_fc: Expected: {0} Got: {1}".format(os.path.join(self.temp_name, flp.__flight_data_gdb_name__, flp.__flight_path_fc_name__), flp.flight_path_fc))
        self.assertEquals(flp.total_points_layer, os.path.join(self.temp_name, flp.__maps_folder_name__, flp.__total_points_lyr_name__), msg = "Property total_points_layer: Expected: {0} Got: {1}".format(os.path.join(self.temp_name, flp.__maps_folder_name__, flp.__total_points_lyr_name__), flp.total_points_layer))
        self.assertEquals(flp.total_lines_layer, os.path.join(self.temp_name, flp.__maps_folder_name__, flp.__total_lines_lyr_name__), msg = "Property total_lines_layer: Expected: {0} Got: {1}".format(os.path.join(self.temp_name, flp.__maps_folder_name__, flp.__total_lines_lyr_name__), flp.total_lines_layer))
        self.assertEquals(flp.total_polygons_layer, os.path.join(self.temp_name, flp.__maps_folder_name__, flp.__total_polygons_lyr_name__), msg = "Property total_polygons_layer: Expected: {0} Got: {1}".format(os.path.join(self.temp_name, flp.__maps_folder_name__, flp.__total_polygons_lyr_name__), flp.total_polygons_layer))
        self.assertEquals(flp.flight_path_layer, os.path.join(self.temp_name, flp.__maps_folder_name__, flp.__flight_path_lyr_name__), msg = "Property flight_path_layer: Expected: {0} Got: {1}".format(os.path.join(self.temp_name, flp.__maps_folder_name__, flp.__flight_path_lyr_name__), flp.flight_path_layer))
        self.assertEquals(flp.helicopter_info_table, os.path.join(self.temp_name, flp.__flight_data_gdb_name__, flp.__helicopter_info_table_name__), msg = "Property helicopter_info_table: Expected: {0} Got: {1}".format(os.path.join(self.temp_name, flp.__flight_data_gdb_name__, flp.__helicopter_info_table_name__), flp.helicopter_info_table))
        self.assertEquals(flp.flightline_total_points_fc, os.path.join(self.temp_name, flp.__flight_data_gdb_name__, flp.__total_points_fc_name__), msg = "Property flightline_total_points_fc: Expected: {0} Got: {1}".format(os.path.join(self.temp_name, flp.__flight_data_gdb_name__, flp.__total_points_fc_name__), flp.flightline_total_points_fc))
        self.assertEquals(flp.flightline_total_lines_fc, os.path.join(self.temp_name, flp.__flight_data_gdb_name__, flp.__total_lines_fc_name__), msg = "Property flightline_total_lines_fc: Expected: {0} Got: {1}".format(os.path.join(self.temp_name, flp.__flight_data_gdb_name__, flp.__total_lines_fc_name__), flp.flightline_total_lines_fc))
        self.assertEquals(flp.flightline_total_polygons_fc, os.path.join(self.temp_name, flp.__flight_data_gdb_name__, flp.__total_polygons_fc_name__), msg = "Property flightline_total_polygons_fc: Expected: {0} Got: {1}".format(os.path.join(self.temp_name, flp.__flight_data_gdb_name__, flp.__total_polygons_fc_name__), flp.flightline_total_polygons_fc))
        self.assertEquals(flp.flightline_flight_path_fc, os.path.join(self.temp_name, flp.__flight_data_gdb_name__, flp.__flight_path_fc_name__), msg = "Property flightline_flight_path_fc: Expected: {0} Got: {1}".format(os.path.join(self.temp_name, flp.__flight_data_gdb_name__, flp.__flight_path_fc_name__), flp.flightline_flight_path_fc))
        self.assertEquals(flp.flightline_sum_totals_table, os.path.join(self.temp_name, flp.__flight_data_gdb_name__, flp.__sum_totals_table_name__), msg = "Property flightline_sum_totals_table: Expected: {0} Got: {1}".format(os.path.join(self.temp_name, flp.__flight_data_gdb_name__, flp.__sum_totals_table_name__), flp.flightline_sum_totals_table))
        self.assertEquals(flp.operation_times_table, os.path.join(self.temp_name, flp.__flight_data_gdb_name__, flp.__operation_times_table_name__), msg = "Property operation_times_table: Expected: {0} Got: {1}".format(os.path.join(self.temp_name, flp.__flight_data_gdb_name__, flp.__operation_times_table_name__), flp.operation_times_table))
        self.assertEquals(flp.flightline_total_points_fc, os.path.join(self.temp_name, flp.__flight_data_gdb_name__, flp.__total_points_fc_name__), msg = "Property flightline_total_points_fc: Expected: {0} Got: {1}".format(os.path.join(self.temp_name, flp.__flight_data_gdb_name__, flp.__total_points_fc_name__), flp.flightline_total_points_fc))
        self.assertEquals(flp.tracmap_data_folder_location, os.path.join(self.temp_name, flp.__tracmap_data_folder_name__), msg = "Property tracmap_data_folder_location: Expected: {0} Got: {1}".format(os.path.join(self.temp_name, flp.__tracmap_data_folder_name__), flp.tracmap_data_folder_location))
        self.assertEquals(flp.flight_data_gdb_location, os.path.join(self.temp_name, flp.__flight_data_gdb_name__), msg = "Property flight_data_gdb_location: Expected: {0} Got: {1}".format(os.path.join(self.temp_name, flp.__flight_data_gdb_name__), flp.flight_data_gdb_location))
        self.assertIsInstance(flp.project_folder_handler, flightline_project.folder_handler.FolderHandler, msg = "property project_folder_handler: Expected: {0} Got: {1}".format(flp.project_folder_handler, flightline_project.folder_handler.FolderHandler))



    def test_set_operation_start_date_time(self):
        flp = self.flightline_project_obj

        prior_result = flp.operation_start_datetime
        flp.set_operation_start_date_time()
        post_result = flp.operation_start_datetime

        self.assertEquals(prior_result, post_result, msg = "Method set_operation_start_date_time should update operation_start_datetime: Expected: {0} Got: {1}".format(prior_result, post_result))

        op_start_time = '1102'
        flp.operation_start_time = op_start_time
        flp.set_operation_start_date_time()
        expected_result = "{0} {1}:{2}:00".format(time.strftime('%Y-%m-%d'),op_start_time[:2], op_start_time[-2:])

        self.assertIsInstance(flp.operation_start_datetime, str, msg = "Attribute operation_start_datetime is not instance of {0} Got: {1}".format(str, type(flp.operation_start_datetime)))
        self.assertEquals(flp.operation_start_datetime, expected_result, msg = "Attribute operation_start_datetime: Expected: {0} Got: {1}".format(expected_result, flp.operation_start_datetime))

    def test_operation_times_table_records(self):
        # TODO: Populate operation_times_table with record then run operation_times_table_records to get list of rows
        pass

    def test_helicopter_regno_list(self):
        # TODO: Populate helicopter_info table with record then run test_helicopter_regno_list to get list of rows
        pass

    def test_projectconfig_json_exists(self):
        # TODO: Test property projectconfig_json_exists returns False, then run dump_to_projectconfig and run property again, should return True
        pass

    def test_valid_project_folder(self):
        flp = self.flightline_project_obj
        invalid_flp = flightline_project.FlightlineProject(None)

        self.assertTrue(flp.valid_project_folder, msg = "Property valid_project_folder did not return True")
        self.assertFalse(invalid_flp.valid_project_folder, msg = "Property valid_project_folder didn not return False")

    def test_project_folder_empty(self):
        flp = self.flightline_project_obj

        self.assertTrue(flp.project_folder_empty, msg = "Property project_folder_empty did not return True")
        os.mkdir(os.path.join(flp.project_folder,'dummyfolder'))
        self.assertFalse(flp.project_folder_empty, msg = "Property project_folder_empty did not return False")

        os.rmdir(os.path.join(flp.project_folder,'dummyfolder'))

    def test_load_project_folder(self):
        flp = self.flightline_project_obj
        flp.__load_project_folder__(self.temp_name)

        self.assertEquals(flp.project_folder, self.temp_name, msg = "Method __load_project_folder__ did not load path: {0} Got: {1}".format(self.temp_name, flp.project_folder))
        with self.assertRaises(excClass=SystemError) as e:
            flp.__load_project_folder__('InvalidFolder')
            self.assertEqual(e.exception, 'InvalidFolder does not exist')

    def test_add_new_flight_data_gdb_name(self):
        flp = self.flightline_project_obj

        flp.add_new_flight_data_gdb_name('NewGDB.gdb')

        self.assertTrue(flp.__flight_data_gdb_name__ == 'NewGDB.gdb', msg = "Method add_new_flight_data_gdb_name did not update attribute __flight_data_gdb_name__ Got: {0}".format(flp.__flight_data_gdb_name__))
        self.assertTrue('NewGDB.gdb' in flp.flight_data_gdbs, "Method add_new_flight_data_gdb did not update attribute flight_data_gdbs. Got: {0}".format(flp.flight_data_gdbs))

    def test_rename_required_flight_data_gdb_fcs(self):
        # This is covered in the featureclass handler class
        pass

    def test_add_copied_data_to_mxd(self):
        # This method is due to be shifted, no unit test required
        pass

    def test_load_toolsetting_file__(self):
        flp = self.flightline_project_obj
        flp.__load_tool_setting_file__(os.path.join(Resources.get_test_data_folder(), Resources.project_setup_json_name))

        self.assertGreater(len(flp.__config_attributes__), 0, msg = "Method __load_tool_settings_file__ did not load config attributes. Got: {0}".format(flp.__config_attributes__))

    def test_load_tool_setting_json_files(self):
        # This test is covered by list_tool_setting_json_files and __load_tool_settings_file__
        pass

    def test_get_config_attribute(self):
        flp = self.flightline_project_obj
        flp.__load_tool_setting_file__(os.path.join(Resources.get_test_data_folder(), Resources.project_setup_json_name))

        self.assertEquals(flp.get_config_attribute('Files'), {u'Values': [], u'Order': 2}, msg = "Method __load_tool_setting_file__ should have loaded projectsetup.json and assigned __config_attributes__ a record of: {0}".format({u'Values': [], u'Order': 2}))

        with self.assertRaises(excClass=KeyError) as e:
            flp.get_config_attribute('Dummy')
            self.assertEqual(e.exception, 'Attribute name: {0} not in __config_attributes__'.format('Dummy'))

    def test_dump_to_projectconfig(self):
        flp = self.flightline_project_obj

        flp.dump_to_projectconfig()

        self.assertTrue(flp.projectconfig_json_exists, msg = "Method dump_to_projectconfig did not create projectconfig.json file")

    def test_load_from_projectconfig(self):
        flp = self.flightline_project_obj
        flp2 = flightline_project.FlightlineProject(self.temp_name)

        flp.dump_to_projectconfig()
        flp2.load_from_projectconfig()

        self.assertDictEqual(flp.__dict__, flp2.__dict__)
































