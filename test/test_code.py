import os.environ
import unittest
import denshijiti
import shutil
import os.path

class TestCode(unittest.TestCase):
	def test_code(self):
		denshijiti.run_code()
		shutil.copy("code.ttl", os.path.join(os.path.dirname(__file__), "../docs/"))
