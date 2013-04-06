import unittest
import logging

from ooddr.tests import test_suite

logging.basicConfig()
unittest.TextTestRunner().run(test_suite())
