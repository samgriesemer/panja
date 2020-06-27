This is the base Python project directory structure. The outermost directory contains every file related to that project, including a README, module requirements, local virtual environments, and any other meta files (e.g. WSGI files, socket files, etc). All code for the project will be located within an inner folder with the same name as the project.
 The structure looks as follows:

project/
|- README.md
|- requirements.txt
|- env/
|- project/
   |- __init__.py
   |- lib/
