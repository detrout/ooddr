from six import StringIO, string_types
import shlex
import logging
import os
import re
import ftplib

from debian.debian_support import NativeVersion

try:
    # python 3
    from urllib.parse import urlparse, urlunparse, ParseResult
except ImportError:
    # python 2
    from urlparse import urlparse, urlunparse, ParseResult

logger = logging.getLogger(__name__)

CURRENT_WATCH_VERSION = 3

class Watch(object):
    def __init__(self, sequence=None):
        self.watch_version = 1
        self.options = {}
        self.unresolved_url = None
        self.unresolved_path = None
        self.unresolved_filename = None
        # Remote we found it
        self.version = None
        self.url = None
        self.pathname = None
        self.regex = None
        self.action = None

        versioneq = 'version='

        if sequence is not None:
            if isinstance(sequence, bytes):
                stream = StringIO(sequence.decode('utf-8'))
                sequence = self.read_watch_stream(stream)
            elif isinstance(sequence, string_types):
                stream = StringIO(sequence)
                sequence = self.read_watch_stream(stream)
            elif hasattr(sequence, 'readline'):
                sequence = self.read_watch_stream(sequence)

            if sequence[0].startswith(versioneq):
                version = sequence.pop(0)
                self.watch_version = int(version[len(versioneq):])

            if self.watch_version == 3:
                self.parse_watch3(sequence)
            else:
                raise ValueError('Unsupported version %s',
                                 self.version
                                )

    def __repr__(self):
        if self.version:
            version = str(self.version)
        else:
            version = 'None'

        if self.url:
            url = str(urlunparse(self.url))
        elif self.unresolved_url:
            url = str(urlunparse(self.unresolved_url))
        else:
            url = 'Uninitialized'


        return self.__class__.__name__ + "(" + version + ', ' + url + ")"

    def _get_file_re(self):
        """Return just the filename portion of pattern
        """
        if self.url is None:
            return None
        path, name = os.path.split(self.unresolved_url.path)
        return name
    file_re = property(_get_file_re)

    def read_watch_stream(self, stream):
        state = None

        lines = []
        for line in stream:
            line = line.strip()
            if len(line) == 0 or line.startswith('#'):
                continue
            if state == 'line-continue':
                lines[-1] += line
                state = None
            else:
                lines.append(line)

            if line.endswith('\\'):
                state = 'line-continue'
                #chomp
                lines[-1] = lines[-1][:-1]

        return lines

    def parse_watch3(self, sequence):
        optseq = 'opts='
        for line in sequence:
            watchinfo = line.split()
            if len(watchinfo) == 0:
                raise RuntimeError('No watch line')

            if watchinfo[0].startswith(optseq):
                self.parse_options(watchinfo[0][len(optseq):])
                watchinfo.pop(0)

            self.unresolved_url = urlparse(watchinfo.pop(0))
            last_slash = self.unresolved_url.path.rindex('/')
            self.unresolved_path = self.unresolved_url.path[:last_slash]
            self.unresolved_filename = self.unresolved_url.path[last_slash+1:]

            if watchinfo:
                self.regex = watchinfo.pop(0)
            if watchinfo:
                self.action = watchinfo.pop(0)


    def parse_options(self, options):
        for o in options.split(','):
            olist = o.split('=')
            if len(olist) == 1:
                self.options[olist[0]] = olist[0]
            else:
                self.options[olist[0]] = olist[1]


    def get_latest(self):
        url = self.unresolved_url
        if url.scheme == 'ftp':
            version, path = open_ftp(url)
            url = urlunparse((url.scheme,
                              url.netloc,
                              path,
                              url.params,
                              url.query,
                              url.fragment,
                             ))
            self.version = version
            self.url = url
        elif url.scheme in ('http', 'https'):
            version, path = open_http(url)

        else:
            print ('Unsupported:', urlunparse(url))
            return None


    def scan_local_dir(self, dirname):
        """Scan a local directory for a matching file
        """
        filelist = os.listdir(dirname)
        return scan_local_filelist(filelist, dirname)

    def scan_local_filelist(self, filelist, dirname):
        """Check a list of files for the watch target file name.

        Returns tuple of Version, url
        """
        hits = []
        for f in filelist:
            match = re.match(self.unresolved_filename, f)
            if match:
                version = '.'.join(match.groups())
                pathname = os.path.join(dirname,f)
                url = ParseResult('file','',pathname,'','','')
                hits.append((NativeVersion(version), url))

        hits.sort()
        if hits:
            self.version = hits[-1][0]
            self.url = hits[-1][1]
            return hits[-1]


def open_ftp(url):
    simple_path = []
    directories = url.path.split('/')

    with ftplib.FTP(url.netloc) as ftp:
        ftp.login()
        return newest_dir(ftp, directories)


def newest_dir(conn, directories):
    current = []
    version = None
    for d in directories:
        if re.search('\(.*\)', d):
            conn.cwd('/'.join(current))
            candidates = []
            for f in conn.nlst():
                match = re.search(d, f)
                if match:
                    try:
                        version = NativeVersion('.'.join(match.groups()))
                        candidates.append((version, f))
                    except ValueError as e:
                        pass

            candidates = sorted(candidates)
            current.append(candidates[-1][1])
            version = candidates[-1][0]
        else:
            current.append(d)

    return version, '/'.join(current)
