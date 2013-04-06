import unittest
import importlib

def test_suite():
    module_names = [
        '.test_watch',
        '.test_changelog',
    ]
    suites = []
    for m in module_names:
        module = importlib.import_module(m, 'ooddr.tests')
        suites.append(module.test_suite())
    return unittest.TestSuite(suites)

