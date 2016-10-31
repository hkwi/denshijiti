import os
import unittest
import denshijiti
import shutil
import os.path
import rdflib

class TestCode(unittest.TestCase):
	def test_code(self):
		denshijiti.run_code()
		
		# verify we can load the data
		g = rdflib.Graph()
		g.load("code.ttl", format="turtle")
		
		if "TRAVIS_BUILD_DIR" in os.environ:
			try:
				shutil.copy("code.ttl", os.environ["TRAVIS_BUILD_DIR"])
			except shutil.SameFileError:
				pass
