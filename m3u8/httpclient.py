import posixpath
import ssl
import sys

try:
    import urllib
    from urllib.error import HTTPError
    from urllib.parse import urlparse, urljoin
except ImportError:  # Python 2.x
    from urllib2 import urlopen, Request, HTTPError
    from urlparse import urlparse, urljoin


PYTHON_MAJOR_VERSION = sys.version_info


def _parsed_url(url):
    parsed_url = urlparse(url)
    prefix = parsed_url.scheme + '://' + parsed_url.netloc
    base_path = posixpath.normpath(parsed_url.path + '/..')
    return urljoin(prefix, base_path)

def _read_python2x(resource):
    return resource.read().strip()


def _read_python3x(resource):
    return resource.read().decode(
        resource.headers.get_content_charset(failobj="utf-8")
    )


class DefaultHTTPClient:

    def __init__(self, proxies=None):
        self.proxies = proxies

    def download(self, uri, timeout=None, headers={}, verify_ssl=True):
        proxy_handler = urllib.request.ProxyHandler(self.proxies)
        https_handler = HTTPSHandler(verify_ssl=verify_ssl)
        opener = urllib.request.build_opener(proxy_handler, https_handler)
        opener.addheaders = headers.items()
        resource = opener.open(uri, timeout=timeout)
        base_uri = _parsed_url(resource.geturl())
        if PYTHON_MAJOR_VERSION < (3,):
            content = _read_python2x(resource)
        else:
            content = _read_python3x(resource)
        return content, base_uri


class HTTPSHandler:

    def __new__(self, verify_ssl=True):
        context = ssl.create_default_context()
        if not verify_ssl:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        return urllib.request.HTTPSHandler(context=context)
