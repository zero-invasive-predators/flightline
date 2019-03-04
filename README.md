# Flightline
Set of tools to help with Aerial Operation Projects using arcpy

Overall Logic
The overall logic is to have all configs and settings stored in xml/json files to make it
easier for users to set it up for their local environment. The logic will be distributed throughout the python modules with minimal logic in the Python Toolbox tools.
When begining, a user creates a folder that defines their project, from here the tools will generate and copy data/files into this project folder needed to run through the aerial project. A config.json file will keep track of project settings so they can be passed across toolbox tools.
The user then runs through tools to set the project up. Once setup they will run other tools whilst in the field supervising the aerial project. Then on return to the office the data from the project will be submitted to a central dataset.

Rules
- Make the solution portable and easily implemented into any system running ArcMap.
- No hardcoding of configs/settings within python files (Instead store in json or config files)
- Usage of standard python libraries and arcpy to increase portability and remove dependencies.
- The Python Toolbox Tools should not house any major logic and should rely on the python modules.
