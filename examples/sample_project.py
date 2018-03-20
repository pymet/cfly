import os

from cfly import module_from_source
from cfly.utils import read_files_from_folder

files = read_files_from_folder(os.path.join(os.path.dirname(__file__), 'sample_project'))
mymodule = module_from_source('mymodule', files.pop('module.cpp'), files)

print(mymodule.get_x())
