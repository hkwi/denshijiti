import os
import unittest
import denshijiti
import shutil
import os.path

class TestCode(unittest.TestCase):
	def test_code(self):
		denshijiti.run_code()
		if "TRAVIS_BUILD_DIR" in os.environ:
			shutil.copy("code.ttl", os.environ["TRAVIS_BUILD_DIR"])
