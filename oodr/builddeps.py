#!/usr/bin/python3
"""Build dependency lists.
"""
import os, sys
from glob import glob
from pprint import pprint

import networkx as nx

from debian.deb822 import Deb822, _PkgRelationMixin, Dsc, Packages
from debian.changelog import Changelog
from apt.cache import Cache

class Control(Deb822, _PkgRelationMixin):
    _relationship_fields = ['build-depends',]
    def __init__(self, *args, **kwargs):
        Deb822.__init__(self, *args, **kwargs)
        _PkgRelationMixin.__init__(self, *args, **kwargs)

class SourcePackage(object):
    def __init__(self, package_list, version, package_dir):
        self.source = package_list[0]
        self.binaries = package_list[1:]
        self.version = version
        self.package_dir = package_dir
        self.dsc = []
        self.repository = []

    def _get_name(self):
        return self.source['Source']
    name = property(_get_name)

    def _get_needs(self):
        for build_deps in self.source.relations['build-depends']:
            for dep in build_deps:
                yield Needs(dep['name'], dep['version'], dep)
    needs = property(_get_needs)
                    
    def _get_provides(self):
        for p in self.binaries:
            yield Provides(p['package'], None, p)
    provides = property(_get_provides)

    def _get_dscoutdated(self):
        if self.dsc:
            return self.version > self.dsc[0]['Version']
        return True
    dscoutdated = property(_get_dscoutdated)

    def _get_outdated(self):
        if self.repository:
            for pkg in self.repository:
                if self.version > pkg['Version']:
                    return True
            return False
        elif self.dsc:
            return self.dscoutdated
    outdated = property(_get_outdated)
        
    def __repr__(self):
        return self.source['Source']
        
class Provides(object):
    def __init__(self, binary, version, source):
        self.binary = binary
        self.version = version
        self.source = source

class Needs(object):
    def __init__(self, binary, version_expression, source):
        self.binary = binary
        self.version_expression = version_expression
        self.source = source

def read_debian_dir(package_dir):
    '''Read the debian directory contained in package_dir'''
    debian_dir = os.path.join(package_dir, 'debian')
    if not os.path.exists(debian_dir):
        raise IOError(
            'Expected a debian directory in {}'.format(package_dir))
        
    control_filename = os.path.join(debian_dir, 'control')
    changelog_filename = os.path.join(debian_dir, 'changelog')

    with open(changelog_filename, 'r') as stream:
        package_version = read_changelog(stream)

    control = Control()
    with open(control_filename, 'r') as stream:
        package = list(control.iter_paragraphs(stream))
        return SourcePackage(package, package_version, package_dir)

def read_changelog(stream):
    """Find current version
    """
    log = Changelog(stream)
    return log.get_version()

def scan_project_tree(root):
    """Look through a project tree for debian control files
    """
    sources = {}
    dscs = {}
    for dirpath, dirnames, filenames in os.walk(root, topdown=True):
        indexes_to_delete =[]
        for i, d in enumerate(dirnames):
            if d == 'debian':
                source_pkg = read_debian_dir(dirpath)
                sources[source_pkg.name] = source_pkg
            elif d in ('.git', '.bzr'):
                indexes_to_delete.append(i)
        for i in indexes_to_delete[::-1]:
            del dirnames[i]
        for f in filenames:
            if f.endswith('.dsc'):
                with open(os.path.join(dirpath, f)) as stream:
                    dsc_pkg = Dsc(stream)
                    dscs.setdefault(dsc_pkg['Source'], []).append(dsc_pkg)

    for dsc_name in dscs:
        source_pkg = sources.get(dsc_name, None)
        if source_pkg:
            source_pkg.dsc = sorted(dscs[dsc_name], 
                                    key=lambda x: x['Version'],
                                    reverse=True)
    return sources

def add_repository_data(packages, package_path):
    source_from_bin = build_source_from_bin(packages)

    with open(package_path) as stream:
        repository = Packages().iter_paragraphs(stream)

        for r in repository:
            bin_pkg_name = r.get('Package')
            if bin_pkg_name:
                source = source_from_bin.get(bin_pkg_name)
                if source:
                    source.repository.append(r)

def build_source_from_bin(packages):
    source_from_bin = {}
    for pkg_name in packages:
        pkg = packages[pkg_name]
        for provided in pkg.provides:
            source_from_bin[provided.binary] = pkg
    return source_from_bin
    
def build_package_graph(packages):
    # map provided binary packages to source packages
    source_from_bin = build_source_from_bin(packages)
    
    deps = nx.DiGraph()
    for pkg_name in packages:
        pkg = packages[pkg_name]
        for need in pkg.needs:
            source = source_from_bin.get(need.binary)
            if source:
                    deps.add_edge(source, pkg)

    return deps
    
def find_build_order(root, packages_path=None):
    """Scan through a tree
    """
            
    packages = scan_project_tree(root)
    add_repository_data(packages, packages_path)
    return build_package_graph(packages)
    

def print_digraph(needs, source):
    print("digraph {")
    for n in needs:
        deps.add_node(n.source)
        source = bin_from_source.get(n.binary)
        if source:
            print('"{0}" -> "{1}";'.format(n.source, source.source))
            
        else:
            # is the binary installable?
            if n.binary not in known:
                #print >>sys.stderr, "Need to find", n.binary
                print('NA -> "{0}";'.format(n.binary))
    print("}")

def compute_orig(source):
    name = source.name
    version = source.version.upstream_version
    pathname = os.path.normpath(os.path.join(source.package_dir, '..'))

    orig_pattern = name + '_' + version + '.orig.*'
    orig_files = glob(os.path.join(pathname, orig_pattern))
    if orig_files:
        return orig_files[0]

def main(cmdline=None):
    deps = find_build_order('/home/diane/kde/src/kde-sc')
    pprint( [ d for d in nx.topological_sort(deps) if d.outdated ] )
    
if __name__ == "__main__":
    main()
