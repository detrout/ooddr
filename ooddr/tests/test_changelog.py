import unittest
from six import StringIO

from debian.debian_support import NativeVersion

from ..changelog import OrderedChangelog

CHANGELOG = """package (1.2.3-4) experimental; urgency=low

  * A new version

 -- Debian Developer <example@debian.org>  Wed, 02 Jan 2013 03:45:57 +0000
"""

class TestChangelog(unittest.TestCase):
    def test_repr(self):

        log = OrderedChangelog(StringIO(CHANGELOG))
        self.assertEqual(repr(log), "OrderedChangelog('1.2.3-4')")

    def test_comparison(self):
        old_version = NativeVersion('1.0.0')
        new_version = NativeVersion('1.3.3')
        newdebian = NativeVersion('1.2.3-5')

        log = OrderedChangelog(StringIO(CHANGELOG))

        self.assertEqual(old_version, old_version)
        self.assertEqual(log, log)

        # does it sort?
        vers = [ newdebian, new_version, old_version, log]
        vers.sort()

        self.assertEqual(vers[0], old_version)
        self.assertEqual(vers[1], log)
        self.assertEqual(vers[2], newdebian)
        self.assertEqual(vers[3], new_version)



def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)

if __name__ == '__main__':
    unittest.main()
