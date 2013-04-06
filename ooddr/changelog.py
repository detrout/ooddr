import debian.changelog
from debian.debian_support import BaseVersion

from debian.changelog import ChangelogParseError

class OrderedChangelog(debian.changelog.Changelog, BaseVersion):
    """Changelog class that can be compared to Versions.

    It inherits from debian.changelog.Changelog and adds
    a bit to be comparable to debian.debian_support.BaseVersions.
    """
    def __repr__(self):
        return "%s('%s')" % (self.__class__.__name__, self.get_version())

    def _compare(self, other):
        if self is other:
            return 0

        # anything is greater than None
        if other is None:
            return 1

        if isinstance(other, OrderedChangelog):
            other = other.get_version()

        return self.get_version()._compare(other)
