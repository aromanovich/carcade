import os
import sys
import shutil
import argparse

import carcade


parser = argparse.ArgumentParser(prog='PROG')
parser.add_argument('name')
args = parser.parse_args()

p = os.path.dirname(os.path.abspath(carcade.__file__))
source = os.path.join(p, 'template')
destination = os.path.join(os.getcwd(), args.name)

shutil.copytree(source, destination)
