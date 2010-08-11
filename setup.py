from setuptools import setup, find_packages
from pkg_resources import Requirement, resource_filename
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),'src')))
import boViewGui
setup(
    name = "boViewGui",
    version = boViewGui.__version__,
    package_dir = {'':'src'},
    packages = find_packages('src'),
    extras_require = {'pymel': ['pymel>=1']},
    dependency_links = ['http://pymel.googlecode.com/files/pymel-1.0.2.zip'],
#    author = "",
#    author_email = "",
#    license = "",
#    description = "",
#    keywords = "",
    include_package_data = True,
)
