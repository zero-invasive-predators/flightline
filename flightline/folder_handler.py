import os
import json
import shutil
import arcpy

class FolderHandler(object):

     def __init__(self,source_folder):
          self.source_folder = source_folder
          self.settings_file = None
          self.__action__attributes__ = {}

     def __create__file(self,new_file):
          """Creates a new file"""
          pass

     def __add_action__(self, order_number, action_name, action_value):
          """Adds an action to __action_attributes__"""
          self.__action__attributes__[action_name] = {"Order":order_number, "Values":action_value}

     @property
     def __ordered_action_names__(self):
          """Returns list of action names ordered by their order number"""
          sorted_items = sorted([[self.__action__attributes__[i]["Order"],i] for i in self.__action__attributes__])
          return [a[1] for a in sorted_items]

     @property
     def __is_source_folder_populated__(self):
          return bool(len(os.listdir(self.source_folder)))

     @staticmethod
     def __create_folder__(new_folder):
          """Creates a new folder"""
          os.mkdir(new_folder)

     def __create_file_geodatabase__(self, new_gdb, xml_file=None):
          """Creates a new filegeodatabase"""
          arcpy.CreateFileGDB_management(out_folder_path=self.source_folder, out_name=new_gdb)
          if xml_file:
               xml_file_location = os.path.join(self.source_folder,xml_file)
               if not os.path.exists(xml_file_location): raise ValueError("XMLFile: {0} does not exist".format(xml_file_location))
               arcpy.ImportXMLWorkspaceDocument_management(target_geodatabase=os.path.join(self.source_folder, new_gdb), in_file=xml_file_location, import_type="SCHEMA_ONLY")

     @staticmethod
     def __create_gdb_dataset__(gdb, xml_file):
          """Creates dataset from xml file in supplied geodatabase"""
          arcpy.ImportXMLWorkspaceDocument_management(target_geodatabase=gdb, in_file=xml_file, import_type="SCHEMA_ONLY")


     def __copy_file__(self, file_source, folder_destination, new_filename = None):
          """Copies a file from the source to destination folder"""
          if not os.path.exists(file_source):
               raise ValueError("File: {0} does not exist".format(file_source))
          _folder_destination = os.path.join(self.source_folder, folder_destination)
          if new_filename:
               _destination = os.path.join(folder_destination, new_filename)
          else:
               _destination = _folder_destination

          shutil.copy2(file_source, _destination)

     @staticmethod
     def __copy_featureclass__(source_fc, destination_fc, where_clause=None):
          """Copies a feature class with the option of a where clause"""
          if not arcpy.Exists(source_fc):
               raise ValueError("source_fc: {0} does not exist".format(source_fc))
          try:
               arcpy.Select_analysis(in_features=source_fc, out_feature_class=destination_fc, where_clause=where_clause)
          except Exception as e:
               print(e)

     def __empty_source_folder__(self):
          """Empties out the source folder"""
          # Delete entire folder, then create a new one
          try:
               if os.path.exists(self.source_folder): shutil.rmtree(self.source_folder)
               if not os.path.exists(self.source_folder): os.mkdir(self.source_folder)
          except Exception as e:
               print(str(e))

     def load_settings_file(self, settings_file, overwrite = False):
          """
          Loads a settings file (.json) into the class
          Interprets the settings folder in a list of instructions
          to generate a folder structure.
          """

          if not os.path.exists(settings_file):
               raise ValueError("File {0} does not exist".format(settings_file))
          if not settings_file.lower().endswith(".json"):
               raise TypeError("File {0} is not of type .json".format(settings_file))
          if self.__is_source_folder_populated__ and not overwrite:
               raise  AttributeError("Instance.overwrite set to: {0} but source folder is populated is: {1}".format(overwrite, self.__is_source_folder_populated__))

          self.settings_file = settings_file
          json_file = open(self.settings_file,'rb')
          json_dict = json.load(json_file)
          json_file.close()

          for key in sorted(json_dict.keys(),reverse=True):
               setattr(self, key, json_dict[key])
               self.__add_action__(json_dict[key]["Order"], key, json_dict[key]["Values"])

     def create_structure(self, overwrite=False):
          """Creates the structure based on the settings_file loaded"""

          if overwrite: self.__empty_source_folder__()

          if not bool(self.settings_file):
               raise ValueError("No settings file loaded, run load_settings_file")

          for action in self.__ordered_action_names__:
               if action.lower() == "files":
                    for file_item in getattr(self, action)["Values"]:
                         self.__create__file(file_item)
               elif action.lower() == "folders":
                    for folder in getattr(self, action)["Values"]:
                         self.__create_folder__(os.path.join(self.source_folder,folder))
               elif action.lower() == "filegeodatabases":
                    for fgdb in getattr(self, action)["Values"]:
                         gdb_dict = getattr(self, action)["Values"][fgdb]
                         self.__create_file_geodatabase__(gdb_dict["Name"], gdb_dict["ImportXml"])
               elif action.lower() == "copyfiles":
                    for cf in getattr(self, action)["Values"]:
                         file_dict = getattr(self, action)["Values"][cf]
                         self.__copy_file__(file_dict["FileSource"], os.path.join(self.source_folder, file_dict["FolderDestination"]))
               elif action.lower() == "copyfeatureclass":
                    for fc in getattr(self, action)["Values"]:
                         fc_dict = getattr(self,action)["Values"][fc]
                         self.__copy_featureclass__(fc_dict["InputFeatureClass"], os.path.join(self.source_folder, fc_dict["OutputFeatureClass"]), fc_dict["WhereClause"])
               elif action.lower() == "copyraster":
                    for r in getattr(self, action)["Values"]:
                         pass
     @staticmethod
     def get_fc_record_count(featureclass):
          """Returns the count of records in the featureclass"""
          return int(arcpy.GetCount_management(featureclass).getOutput(0))