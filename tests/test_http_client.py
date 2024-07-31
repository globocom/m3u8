import gzip
import unittest
from http.client import HTTPResponse
from unittest.mock import Mock, patch

from m3u8.httpclient import DefaultHTTPClient


class MockHeaders:
    def __init__(self, encoding=None):
        self.encoding = encoding

    def get_content_charset(self, failobj="utf-8"):
        return self.encoding or failobj


class TestDefaultHTTPClient(unittest.TestCase):
    @patch("urllib.request.OpenerDirector.open")
    def test_download_normal_content(self, mock_open):
        client = DefaultHTTPClient()
        mock_response = Mock(spec=HTTPResponse)
        mock_response.read.return_value = b"playlist content"
        mock_response.info.return_value = {}
        mock_response.geturl.return_value = "http://example.com/index.m3u8"
        mock_response.headers = MockHeaders()
        mock_open.return_value = mock_response

        content, base_uri = client.download("http://example.com/index.m3u8")

        self.assertEqual(content, "playlist content")
        self.assertEqual(base_uri, "http://example.com/")

    @patch("urllib.request.OpenerDirector.open")
    def test_download_gzipped_content(self, mock_open):
        client = DefaultHTTPClient()
        original_content = "playlist gzipped content"
        gzipped_content = gzip.compress(original_content.encode("utf-8"))
        mock_response = Mock(spec=HTTPResponse)
        mock_response.read.return_value = gzipped_content
        mock_response.info.return_value = {"Content-Encoding": "gzip"}
        mock_response.geturl.return_value = "http://example.com/index.m3u8"
        mock_response.headers = MockHeaders("utf-8")
        mock_open.return_value = mock_response

        content, base_uri = client.download("http://example.com/index.m3u8")

        self.assertEqual(content, original_content)
        self.assertEqual(base_uri, "http://example.com/")

    @patch("urllib.request.OpenerDirector.open")
    def test_download_with_proxy(self, mock_open):
        client = DefaultHTTPClient(proxies={"http": "http://proxy.example.com"})
        mock_response = Mock(spec=HTTPResponse)
        mock_response.read.return_value = b"playlist proxied content"
        mock_response.info.return_value = {}
        mock_response.geturl.return_value = "http://example.com/index.m3u8"
        mock_response.headers = MockHeaders()
        mock_open.return_value = mock_response

        content, base_uri = client.download("http://example.com/index.m3u8")

        self.assertEqual(content, "playlist proxied content")
        self.assertEqual(base_uri, "http://example.com/")
