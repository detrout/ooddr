import pandas as pd
import os

from .builddeps import Dsc, Control, Packages
from .watch import Watch
from .changelog import OrderedChangelog, ChangelogParseError

VCS_DIRS = ('.git', '.hg', '.bzr', '.svn')

def find_debian_files(root):
    """Scan through a directory tree looking for unpacked debian sources
    """
    debian_files = []
    for pathname, dirnames, filenames in os.walk(root, topdown=True):
        # don't decend into vcs dirs
        to_delete = set()
        for i, d in enumerate(dirnames):
            if d in 'debian':
                to_delete.add(i)
                changelog = os.path.join(pathname, 'debian', 'changelog')
                control = os.path.join(pathname, 'debian', 'control')
                if os.path.exists(changelog) and os.path.exists(control):
                    debian_files.append(('package', pathname))
                    to_delete = set(range(len(dirnames)))
                    # deleting here doesn't work, dirnames
                    # seems protected by the for loop
            elif d in VCS_DIRS:
                to_delete.add(i)

        for i in sorted(to_delete)[::-1]:
            del dirnames[i]

        for f in filenames:
            if f.endswith('.dsc'):
                debian_files.append(('dsc', os.path.join(pathname, f)))

    return pd.DataFrame(debian_files,
                        columns=['type', 'filename'])

def build_package_tables(debian_files):
    """Reads all the debian package directories in the file list

    Returns a tuple of data frames for all the packages
      source   - information about the source packages
      needs    - the build-depends for the source packages
      provides - information about binary packages
    """
    sources = []
    needs = []
    binaries = []
    for pathname in debian_files[debian_files.type == 'package'].filename:
        s, n, b = read_debian_dir(pathname)
        sources.append(s)
        needs.append(n)
        binaries.append(b)

    sources = pd.DataFrame(sources, columns=sources[0].index)
    needs = pd.concat(needs)
    binaries = pd.concat(binaries)
    return sources, needs, binaries

def read_debian_dir(package_dir):
    """Read one packages debian control files.

    Returns a tuple
      source   - information about the source package
      needs    - the build-depends for the source package
      provides - what binary packages it builds
    Provides does have the source package name attached
    """
    debian_dir = os.path.join(package_dir, 'debian')
    if not os.path.exists(debian_dir):
        raise IOError(
            'Expected a debian directory in {}'.format(package_dir))

    control_filename = os.path.join(debian_dir, 'control')
    changelog_filename = os.path.join(debian_dir, 'changelog')
    watch_filename = os.path.join(debian_dir, 'watch')

    package_version = None
    with open(changelog_filename, 'r') as stream:
        log = OrderedChangelog()
        try:
                log.parse_changelog(stream)
                package_version = log
        except ChangelogParseError as e:
                # really log
                print ('WARNING:', changelog_filename, e)


    watch = None
    if os.path.exists(watch_filename):
        with open(watch_filename) as stream:
            watch = Watch(stream)

    control = Control()
    with open(control_filename, 'r') as stream:
        p = list(control.iter_paragraphs(stream))
        source = {k: p[0][k] for k in p[0] if k != 'Build-Depends'}
        source['Version'] =  package_version
        source['Watch'] = watch
        source = pd.Series(source)
        needs = [ x[0] for x in p[0].relations['build-depends']]
        needs = pd.DataFrame(needs)
        needs['Source'] = source['Source']
        provides = pd.DataFrame([dict(x) for x in p[1:]])
        provides['Source'] = source['Source']
        return source, needs, provides

def build_dsc_tables(debian_files):
    dscs = []
    files = []
    for pathname in debian_files[debian_files.type == 'dsc'].filename:
        d, f = read_dsc(pathname)
        dscs.append(d)
        files.append(f)

    return pd.DataFrame(dscs), pd.concat(files)

def read_dsc(filename):
    """Read a dsc file and return package and file metadata
    """
    with open(filename) as stream:
        debdsc = Dsc(stream)
        dsc = {}
        files = {}
        for k in debdsc:
            value = debdsc[k]
            if isinstance(value, list):
                for file_rec in debdsc[k]:
                    file_name = file_rec['name']
                    files.setdefault(file_name, {}).update(file_rec)
                    files[file_name]['Source'] = debdsc['Source']
            else:
                dsc[k] = value
    return pd.Series(dsc), pd.DataFrame(list(files.values()))

def build_repository_table(package_file):
    with open(package_file) as stream:
        repository = Packages().iter_paragraphs(stream)

        return pd.DataFrame([dict(x) for x in repository])

def find_newer_source(source, repository):
    sr = pd.merge(source,
                  repository,
                  on=['Source'],
                  suffixes=['_src', '_repo'],
        )
    return sr[sr.Version_src > sr.Version_repo]

def add_local_versions(source, downloads):
    files = os.listdir(downloads)
