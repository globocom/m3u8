
import os
from m3u8.parser import is_url

try:
    import urlparse as url_parser
except ImportError:
    import urllib.parse as url_parser


def _urijoin(base_uri, path):
    if is_url(base_uri):
        return url_parser.urljoin(base_uri, path)
    else:
        return os.path.normpath(os.path.join(base_uri, path.strip('/')))


class BasePathMixin(object):

    @property
    def absolute_uri(self):
        if self.uri is None:
            return None
        if is_url(self.uri):
            return self.uri
        else:
            if self.base_uri is None:
                raise ValueError('There can not be `absolute_uri` with no `base_uri` set')
            return _urijoin(self.base_uri, self.uri)

    @property
    def base_path(self):
        if self.uri is None:
            return None
        return os.path.dirname(self.get_path_from_uri())

    def get_path_from_uri(self):
        """Some URIs have a slash in the query string."""
        return self.uri.split("?")[0]

    @base_path.setter
    def base_path(self, newbase_path):
        if self.uri is not None:
            if not self.base_path:
                self.uri = "%s/%s" % (newbase_path, self.uri)
            else:
                self.uri = self.uri.replace(self.base_path, newbase_path)


class GroupedBasePathMixin(object):

    def _set_base_uri(self, new_base_uri):
        for item in self:
            item.base_uri = new_base_uri

    base_uri = property(None, _set_base_uri)

    def _set_base_path(self, newbase_path):
        for item in self:
            item.base_path = newbase_path

    base_path = property(None, _set_base_path)
