import unittest
from six import StringIO
from ..watch import Watch, urlunparse

FTP_SITE = 'ftp.kde.org'
FTP_PATH = '/pub/kde/stable/([\d\.]*)/src'
FTP_FILE = 'kde-runtime-([\d\.]*).tar.xz'
FTP_URL = 'ftp://' + FTP_SITE + FTP_PATH + '/' + FTP_FILE


class TestWatch(unittest.TestCase):
    def test_v3_ftp_noopts(self):
        watch_data = '\n'.join(['version=3', FTP_URL, ''])

        w = Watch(StringIO(watch_data))

        self.assertEqual(w.watch_version, 3)
        self.assertEqual(urlunparse(w.unresolved_url), FTP_URL)
        self.assertEqual(w.unresolved_path, FTP_PATH)
        self.assertEqual(w.unresolved_filename, FTP_FILE)

        self.assertEqual(repr(w), "Watch(None, " + FTP_URL + ")")


    def test_v3_ftp_uver(self):
        opts = 'opts=uversionmangle=s/^0.0./ \\'
        watch_data = '\n'.join(('version=3', opts, FTP_URL, ''))

        w = Watch(StringIO(watch_data))

        self.assertEqual(w.watch_version, 3)
        self.assertEqual(urlunparse(w.unresolved_url), FTP_URL)
        self.assertEqual(w.unresolved_path, FTP_PATH)
        self.assertEqual(w.unresolved_filename, FTP_FILE)
        self.assertEqual(len(w.options), 1)
        self.assertTrue('uversionmangle' in w.options)
        self.assertEqual(w.options['uversionmangle'],
                         's/^0.0./')


    def test_v3_manyopts(self):
        opts = 'opts=uversionmangle=s/^0.0./,pasv,\\\n'\
               'downloadurlmangle=/asdf/fdsa/ \\\n'
        watch_data = '\n'.join(('version=3', opts, FTP_URL, ''))

        w = Watch(StringIO(watch_data))

    def test_local_search(self):
        watch_data = '\n'.join(['version=3', FTP_URL, ''])

        w = Watch(StringIO(watch_data))
        self.assertEqual(w.watch_version, 3)

        local_dir = ['afile.tar.xz',
                     'anonter.tar.xz',
                     'kde-runtime-4.10.2.tar.xz',
                     'kde-runtime-4.8.2.tar.xz',]
        file_info = w.scan_local_filelist(local_dir, '/tmp')
        self.assertEqual(file_info[0], '4.10.2')
        self.assertEqual(urlunparse(file_info[1]),
                         'file:///tmp/kde-runtime-4.10.2.tar.xz')
        self.assertEqual(file_info[1].path, '/tmp/kde-runtime-4.10.2.tar.xz')

        w.version = file_info[0]
        w.url = file_info[1]
        self.assertEqual(repr(w),
                         "Watch(4.10.2, file:///tmp/kde-runtime-4.10.2.tar.xz)")

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)

if __name__ == '__main__':
    unittest.main()
