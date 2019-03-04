import unittest
import os
import uuid
import shutil
import arcpy
import tempfile


from flightline import folder_handler

class Resources():

    total_gdb_xml_name = "total_gdb.xml"
    flight_path_xml_name = "flight_path.xml"
    project_settings_file_name = "ProjectSetup.json"

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





class TestFolderHandler(unittest.TestCase):

    def setUp(self):
        self.temp_name, self.temp_directory, self.unique_id = Resources.generate_temp_space()
        self.folder_handler_obj = folder_handler.FolderHandler(self.temp_name)

    def tearDown(self):
        shutil.rmtree(self.temp_directory, ignore_errors=True)

    def test_folder_handler_class(self):
        fho = self.folder_handler_obj

        self.assertIsInstance(fho, folder_handler.FolderHandler, msg = "Folder handler did not return instance of self")
        self.assertEquals(fho.source_folder, self.temp_name, msg = "Attribute source_folder. Expected: {0} Got: {1}".format(self.temp_name, fho.source_folder))
        self.assertEquals(fho.settings_file, None, msg = "Attribute settings_file. Expected {0} Got: {1}".format(None, fho.settings_file))
        self.assertEquals(fho.__action__attributes__, {}, msg = "Attribute settings_file. Expected {0} Got: {1}".format({}, fho.__action__attributes__))

    def test_add_action(self):
        fho = self.folder_handler_obj
        expected_results = {'TestAction': {'Values': 'ActionValue', 'Order': 1}}

        fho.__add_action__(1, 'TestAction', 'ActionValue')
        self.assertDictEqual(fho.__action__attributes__, expected_results, msg = "Method __add_action__ shold have added: {0} Got: {1}".format(expected_results, fho.__action__attributes__))

    def test_ordered_action_names(self):
        fho = self.folder_handler_obj

        expected_results = ['TestAction1', 'TestAction5', 'TestAction10']

        fho.__add_action__(1, 'TestAction1','ActionValue1')
        fho.__add_action__(10, 'TestAction10','ActionValue10')
        fho.__add_action__(5, 'TestAction5','ActionValue5')

        self.assertEquals(expected_results, fho.__ordered_action_names__, msg = "Property __ordered_action_names: Expected: {0} Got: {1}".format(expected_results, fho.__ordered_action_names__))

    def test_is_source_folder_populated(self):
        fho = self.folder_handler_obj

        self.assertFalse(fho.__is_source_folder_populated__, msg = "Property __is_source_folder_populated_: Expected: {0} Got: {1}".format(False, fho.__is_source_folder_populated__))
        os.mkdir(os.path.join(self.temp_name, 'TestFolder'))
        self.assertTrue(fho.__is_source_folder_populated__, msg = "Property __is_source_folder_populated_: Expected: {0} Got: {1}".format(True, fho.__is_source_folder_populated__))
        os.rmdir(os.path.join(self.temp_name, 'TestFolder'))

    def test_create_folder(self):
        fho = self.folder_handler_obj
        new_folder = os.path.join(self.temp_name, 'TestFolder')

        fho.__create_folder__(new_folder)

        self.assertTrue(os.path.exists(new_folder), msg = "Method __create_folder__ did not create folder: {0}".format(new_folder))

        os.rmdir(new_folder)

    def test_create_file_geodatabase(self):
        fho = self.folder_handler_obj
        new_gdb_name = 'NewGdb.gdb'
        new_gdb = os.path.join(self.temp_name, new_gdb_name)
        new_gdb_name_2 = 'NewGdb2.gdb'
        new_gdb_2 = os.path.join(self.temp_name, new_gdb_name_2)
        xml_file = os.path.join(Resources.get_test_data_folder(), Resources.total_gdb_xml_name)

        fho.__create_file_geodatabase__(new_gdb_name)
        self.assertTrue(os.path.exists(new_gdb), msg = "Method __create_file_geodatabase__ did not create new File GDB: {0}".format(new_gdb))
        arcpy.Delete_management(new_gdb)

        fho.__create_file_geodatabase__(new_gdb_name_2)
        self.assertTrue(os.path.exists(new_gdb_2), msg = "Method __create_file_geodatabase__ did not create new File GDB: {0}".format(new_gdb_2))
        arcpy.Delete_management(new_gdb_2)


    def test_create_gdb_dataset(self):

        fho = self.folder_handler_obj
        new_gdb_name = 'NewGdb.gdb'
        new_gdb = os.path.join(self.temp_name, new_gdb_name)
        xml_file = os.path.join(Resources.get_test_data_folder(), Resources.flight_path_xml_name)

        fho.__create_file_geodatabase__(new_gdb_name)
        fho.__create_gdb_dataset__(new_gdb, xml_file)

        arcpy.env.workspace = new_gdb
        fcs = [i for i in arcpy.ListFeatureClasses("*")]
        self.assertTrue('flight_path' in fcs, msg = "Method __create_gdb_dataset__ did not create fc in gdb: {0} from xml file: {1}".format(new_gdb, xml_file))

        arcpy.env.workspace = None
        arcpy.Delete_management(new_gdb)

    def test_copy_file(self):
        fho = self.folder_handler_obj
        file_source = os.path.join(Resources.get_test_data_folder(), Resources.flight_path_xml_name)
        file_destination = os.path.join(self.temp_name, Resources.flight_path_xml_name)
        file_destination_2 = os.path.join(self.temp_name, 'NewFile.txt')

        fho.__copy_file__(file_source, self.temp_name)

        self.assertTrue(os.path.exists(file_destination), msg = "Method __copy_file__ did not copy file from source: {0} to destination: {1}".format(file_source, file_destination))
        os.remove(file_destination)
        fho.__copy_file__(file_source, self.temp_name, new_filename='NewFile.txt')
        self.assertTrue(os.path.exists(file_destination_2), msg = "Method __copy_file__ did not copy file from source: {0} to destination: {1}".format(file_source, file_destination_2))
        os.remove(file_destination_2)

    def test_copy_featureclass(self):
        fho = self.folder_handler_obj
        source_gdb_name = "SourceGdb.gdb"
        source_gdb = os.path.join(self.temp_name, source_gdb_name)
        destination_gdb_name = 'DestinationGdb.gdb'
        destination_gdb = os.path.join(self.temp_name, destination_gdb_name)
        xml_file = os.path.join(Resources.get_test_data_folder(), Resources.flight_path_xml_name)
        source_fc = os.path.join(source_gdb, 'flight_path')
        destination_fc = os.path.join(destination_gdb, 'flight_path')

        fho.__create_file_geodatabase__(source_gdb_name)
        fho.__create_file_geodatabase__(destination_gdb_name)
        fho.__create_gdb_dataset__(source_gdb, xml_file)

        fho.__copy_featureclass__(source_fc, destination_fc)

        arcpy.env.workspace = source_gdb
        source_fc_list = [i for i in arcpy.ListFeatureClasses("*")]
        arcpy.env.workspace = destination_gdb
        destination_fc_list = [j for j in arcpy.ListFeatureClasses("*")]

        self.assertListEqual(source_fc_list, destination_fc_list, msg = "Method __copy_featureclass__ did not copy featureclass. Source FC List: {0}, Destination FC List: {1}".format(source_fc_list, destination_fc_list))

        arcpy.Delete_management(source_gdb)
        arcpy.Delete_management(destination_gdb)

    def test_empty_source_folder(self):
        fho = self.folder_handler_obj

        new_folder = os.path.join(self.temp_name, 'TestFolder')
        os.mkdir(new_folder)

        fho.__empty_source_folder__()

        self.assertFalse(os.path.exists(new_folder), msg = "Method __empty_source_folder__ did not empty folder, {0} still exists".format(new_folder))

    def test_load_settings_file(self):

        fho = self.folder_handler_obj
        settings_file = os.path.join(Resources.get_test_data_folder(), Resources.project_settings_file_name)

        expected_results = {u'Folders': {'Values': [u'TracMapData', u'Maps', u'Data', u'Config'], 'Order': 1}, u'Files': {'Values': [], 'Order': 2}, u'CopyFeatureClass': {'Values': {u'AerialBoundary': {u'WhereClause': u"STRATA_NM LIKE 'Hatepe Sector 1A' AND FINYEAR LIKE '2017-2018'", u'OutputFeatureClass': u'Planning.gdb\\AerialBoundary', u'InputFeatureClass': u'T:\\ArcGISLayerFiles\\DatabaseConnections\\PRODGIS-V - ahb_prod.sde\\ahb_prod.SDEADMIN.VM_REGION_NN\\ahb_prod.SDEADMIN.NN_Strata'}}, 'Order': 10}, u'CopyFiles': {'Values': {u'File3': {u'FileSource': u'C:\\Users\\braaksman\\Downloads\\DOC\\TracMap Utilities\\Tracmap_utilities\\xml\\flight_path.xml', u'FolderDestination': u'Config'}, u'File2': {u'FileSource': u'C:\\Users\\braaksman\\Downloads\\DOC\\TracMap Utilities\\Tracmap_utilities\\xml\\total_gdb.xml', u'FolderDestination': u'Config'}, u'File1': {u'FileSource': u'E:\\Temp\\FlightLineTestFile.txt', u'FolderDestination': u'Data'}, u'File10': {u'FileSource': u'C:\\Users\\braaksman\\Downloads\\DOC\\TracMap Utilities\\Tracmap_utilities\\xml\\HelicopterMetadata.json', u'FolderDestination': u'Config'}, u'File7': {u'FileSource': u'C:\\Users\\braaksman\\Downloads\\DOC\\TracMap Utilities\\Tracmap_utilities\\xml\\total_lines.xml', u'FolderDestination': u'Config'}, u'File6': {u'FileSource': u'C:\\Users\\braaksman\\Downloads\\DOC\\TracMap Utilities\\Tracmap_utilities\\xml\\sum_totals.xml', u'FolderDestination': u'Config'}, u'File5': {u'FileSource': u'C:\\Users\\braaksman\\Downloads\\DOC\\TracMap Utilities\\Tracmap_utilities\\xml\\operation_start_end_time.xml', u'FolderDestination': u'Config'}, u'File4': {u'FileSource': u'C:\\Users\\braaksman\\Downloads\\DOC\\TracMap Utilities\\Tracmap_utilities\\xml\\helicopter_info.xml', u'FolderDestination': u'Config'}, u'File9': {u'FileSource': u'C:\\Users\\braaksman\\Downloads\\DOC\\TracMap Utilities\\Tracmap_utilities\\xml\\total_polygons.xml', u'FolderDestination': u'Config'}, u'File8': {u'FileSource': u'C:\\Users\\braaksman\\Downloads\\DOC\\TracMap Utilities\\Tracmap_utilities\\xml\\total_points.xml', u'FolderDestination': u'Config'}, u'File11': {u'FileSource': u'C:\\Users\\braaksman\\Downloads\\DOC\\TracMap Utilities\\Tracmap_utilities\\flight_path.lyr', u'FolderDestination': u'Maps'}, u'File14': {u'FileSource': u'C:\\Users\\braaksman\\Downloads\\DOC\\TracMap Utilities\\Tracmap_utilities\\total_polygons.lyr', u'FolderDestination': u'Maps'}, u'File12': {u'FileSource': u'C:\\Users\\braaksman\\Downloads\\DOC\\TracMap Utilities\\Tracmap_utilities\\total_lines.lyr', u'FolderDestination': u'Maps'}, u'File13': {u'FileSource': u'C:\\Users\\braaksman\\Downloads\\DOC\\TracMap Utilities\\Tracmap_utilities\\total_points.lyr', u'FolderDestination': u'Maps'}}, 'Order': 3}, u'FileGeoDatabases': {'Values': {u'flightdata': {u'ImportXml': u'Config\\total_gdb.xml', u'Name': u'FlightData.gdb'}, u'planning': {u'ImportXml': None, u'Name': u'Planning.gdb'}}, 'Order': 4}, u'CopyRaster': {'Values': {}, 'Order': 11}}

        fho.load_settings_file(settings_file)

        self.assertDictEqual(fho.__action__attributes__, expected_results, msg = "Method load_settings_file should have loaded: {0} to __action__attributes__. __action__attributes__ contains: {1}".format(expected_results, fho.__action__attributes__))

    def test_create_structure(self):
        fho = self.folder_handler_obj

        fho.load_settings_file(os.path.join(Resources.get_test_data_folder(), Resources.project_settings_file_name))

        fho.create_structure()

        for action in fho.__ordered_action_names__:
            if action.lower() == "files":
                for file_item in getattr(fho, action)["Values"]:
                    self.assertTrue(os.path.exists(file_item), msg = "Expected {0} to exist".format(file_item))
            elif action.lower() == "folders":
                for folder in getattr(fho, action)["Values"]:
                    new_folder = os.path.join(fho.source_folder, folder)
                    self.assertTrue(os.path.exists(new_folder), msg = "Expected {0} to exist".format(new_folder))
            elif action.lower() == "filegeodatabases":
                for fgdb in getattr(fho, action)["Values"]:
                    gdb_dict = getattr(fho, action)["Values"][fgdb]
                    new_gdb = os.path.join(fho.source_folder, gdb_dict["Name"])
                    self.assertTrue(os.path.exists(new_gdb), msg = "Expected {0} to exist".format(new_gdb))
            elif action.lower() == "copyfiles":
                for cf in getattr(fho, action)["Values"]:
                    file_dict = getattr(fho, action)["Values"][cf]
                    new_file = os.path.join(fho.source_folder, file_dict["FolderDestination"], os.path.basename(file_dict["FileSource"]))
                    self.assertTrue(os.path.exists(new_file), msg = "Expected {0} to exist".format(new_file))
            elif action.lower() == "copyfeatureclass":
                for fc in getattr(fho, action)["Values"]:
                    fc_dict = getattr(fho,action)["Values"][fc]
                    new_fc = os.path.join(fho.source_folder, fc_dict["OutputFeatureClass"])
                    pass
            elif action.lower() == "copyraster":
                for r in getattr(fho, action)["Values"]:
                    pass


















