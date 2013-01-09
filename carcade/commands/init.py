import shutil
import os.path

import carcade


def main(project_name):
    carcade_path = os.path.dirname(os.path.abspath(carcade.__file__))
    source = os.path.join(carcade_path, 'template')
    destination = os.path.join(os.getcwd(), project_name)
    shutil.copytree(source, destination)
