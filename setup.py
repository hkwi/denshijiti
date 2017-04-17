import sys
from setuptools import setup, find_packages

setup(name='denshijiti',
	version='0.1.0',
	description='Japan denshijiti/code RDF generator',
	long_description=open("README.md").read(),
	author='Hiroaki Kawai',
	author_email='hiroaki.kawai@gmail.com',
	url='https://github.com/hkwi/denshijiti/',
	packages=find_packages(),
)
