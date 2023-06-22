# Flightline
Set of tools to help with Aerial Operation Projects using arcpy

Summary
The aim is to have as many configurations stored in .xml/json files so that making changes based on a local environment
is easier.
When begining, a user creates a folder that defines their project, from here the tools will generate and
copy data/files into this project folder needed to run through the aerial project. A config.json file will keep
track of project settings so they can be passed across toolbox tools.
The user then runs through tools to set the project up. Once setup they will run other tools whilst
in the field supervising the aerial project.
Then on return to the office the data from the project will be submitted to a central dataset.

Rules
- Make the solution portable and easily implemented into any system running ArcGIS Pro.
- No hardcoding of configs/settings within python files (Instead store in json or config files)
- Usage of standard python libraries and arcpy to increase portability and remove dependencies.
- The Python Toolbox Tools should not house any major logic and should rely on the python modules.


Environment Setup
- In ArcGIS Pro, create a clone of your default Python environment if one does not exist.
- In a file browser navigate to the site_packages folder of your cloned environent.
- Create a python path file (text file with a .pth extension) and inside that file have the location to your flightline python module


Operation Setup
- Create a folder to house your operational project. 
- Either check that the /data/ProjectSetup.json has correct paths defined, or make a copy of this file and update to your environment.
- Open up ArcGIS Pro and save it into the folder you created in setp 1.
- Within the Tooblox section in Catalog, click Add Toolbox and navigate to the flightline.pyt file in the ArcToolbox folder of this repo.
- In the Flightline toolbox, run the "Create Folder Structure" tool and point it to the folder you created in step 1. This will setup your project folder.
- In the Flightline toolbox, run the "Create New Flightline Gdb" tool.
- 
