import ssl
import sys
import urllib
from urllib.error import HTTPError
from urllib.parse import SplitResult, urlsplit
import urllib.request


def _parsed_url(url):
    parsed_url = urlsplit(url)
    base_path = parsed_url.path.rpartition('/')[0] + '/'
    return SplitResult(parsed_url.scheme, parsed_url.netloc, base_path, '', '').geturl()


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
        content = resource.read().decode(
            resource.headers.get_content_charset(failobj="utf-8")
        )
        return content, base_uri


class HTTPSHandler:

    def __new__(self, verify_ssl=True):
        context = ssl.create_default_context()
        if not verify_ssl:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        return urllib.request.HTTPSHandler(context=context)
