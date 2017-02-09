from setuptools import setup, find_packages
import subprocess
import os
import re

version_py = os.path.join(os.path.dirname(__file__), 'codebom', '_version.py')

if not os.path.exists(version_py):
    with open(version_py, 'w') as hdl:
        version = str(subprocess.check_output(['git', 'describe', '--tags'])).strip()
        hdl.write('__version__ = ' + repr(version))

exec(open(version_py).read())


setup(
    name="codebom",
    description='Command-line tool to create, validate and analyze a Bill of Materials',
    author='Greg Fitzgerald',
    author_email='garious@gmail.com',
    url='https://github.com/codebom/codebom',
    version=re.sub(r'-(\d+)-', r'+\1.', __version__),  # Make PEP 440 compliant
    packages=find_packages(),
    package_data={'codebom': ['licenses/*.txt']},
    scripts=['bin/codebom'],
    install_requires=[
      'ruamel.yaml~=0.13.13',
      'graphviz~=0.5.2',
    ]
)
