# Copyright 2014 Globo.com Player authors. All rights reserved.
# Use of this source code is governed by a MIT License
# license that can be found in the LICENSE file.

import os
import socket
import urllib.parse
import m3u8
import pytest
import playlists


def test_loads_should_create_object_from_string():
    obj = m3u8.loads(playlists.SIMPLE_PLAYLIST)
    assert isinstance(obj, m3u8.M3U8)
    assert 5220 == obj.target_duration
    assert "http://media.example.com/entire.ts" == obj.segments[0].uri


def test_load_should_create_object_from_file():
    obj = m3u8.load(playlists.SIMPLE_PLAYLIST_FILENAME)
    assert isinstance(obj, m3u8.M3U8)
    assert 5220 == obj.target_duration
    assert "http://media.example.com/entire.ts" == obj.segments[0].uri


def test_load_should_create_object_from_uri():
    obj = m3u8.load(playlists.SIMPLE_PLAYLIST_URI)
    assert isinstance(obj, m3u8.M3U8)
    assert 5220 == obj.target_duration
    assert "http://media.example.com/entire.ts" == obj.segments[0].uri


def test_load_should_remember_redirect():
    obj = m3u8.load(playlists.REDIRECT_PLAYLIST_URI)
    urlparsed = urllib.parse.urlparse(playlists.SIMPLE_PLAYLIST_URI)
    assert urlparsed.scheme + "://" + urlparsed.netloc + "/" == obj.base_uri


def test_load_should_create_object_from_file_with_relative_segments():
    base_uri = os.path.dirname(playlists.RELATIVE_PLAYLIST_FILENAME)
    obj = m3u8.load(playlists.RELATIVE_PLAYLIST_FILENAME)
    expected_key_abspath = "%s/key.bin" % os.path.dirname(base_uri)
    expected_key_path = "../key.bin"
    expected_ts1_abspath = "/entire1.ts"
    expected_ts1_path = "/entire1.ts"
    expected_ts2_abspath = "%s/entire2.ts" % os.path.dirname(base_uri)
    expected_ts2_path = "../entire2.ts"
    expected_ts3_abspath = "%s/entire3.ts" % os.path.dirname(os.path.dirname(base_uri))
    expected_ts3_path = "../../entire3.ts"
    expected_ts4_abspath = "%s/entire4.ts" % base_uri
    expected_ts4_path = "entire4.ts"
    expected_ts5_abspath = "%s/entire5.ts" % base_uri
    expected_ts5_path = "./entire5.ts"
    expected_ts6_abspath = "%s/entire6.ts" % base_uri
    expected_ts6_path = ".//entire6.ts"

    assert isinstance(obj, m3u8.M3U8)
    assert expected_key_path == obj.keys[0].uri
    assert expected_key_abspath == obj.keys[0].absolute_uri
    assert expected_ts1_path == obj.segments[0].uri
    assert expected_ts1_abspath == obj.segments[0].absolute_uri
    assert expected_ts2_path == obj.segments[1].uri
    assert expected_ts2_abspath == obj.segments[1].absolute_uri
    assert expected_ts3_path == obj.segments[2].uri
    assert expected_ts3_abspath == obj.segments[2].absolute_uri
    assert expected_ts4_path == obj.segments[3].uri
    assert expected_ts4_abspath == obj.segments[3].absolute_uri
    assert expected_ts5_path == obj.segments[4].uri
    assert expected_ts5_abspath == obj.segments[4].absolute_uri
    assert expected_ts6_path == obj.segments[5].uri
    assert expected_ts6_abspath == obj.segments[5].absolute_uri


def test_load_should_create_object_from_uri_with_relative_segments():
    obj = m3u8.load(playlists.RELATIVE_PLAYLIST_URI)
    urlparsed = urllib.parse.urlparse(playlists.RELATIVE_PLAYLIST_URI)
    base_uri = os.path.normpath(urlparsed.path + "/..")
    prefix = urlparsed.scheme + "://" + urlparsed.netloc
    expected_key_abspath = "{}{}key.bin".format(
        prefix,
        os.path.normpath(base_uri + "/..") + "/",
    )
    expected_key_path = "../key.bin"
    expected_ts1_abspath = "{}{}entire1.ts".format(prefix, "/")
    expected_ts1_path = "/entire1.ts"
    expected_ts2_abspath = "{}{}entire2.ts".format(
        prefix,
        os.path.normpath(base_uri + "/..") + "/",
    )
    expected_ts2_path = "../entire2.ts"
    expected_ts3_abspath = "{}{}entire3.ts".format(
        prefix,
        os.path.normpath(base_uri + "/../.."),
    )
    expected_ts3_path = "../../entire3.ts"
    expected_ts4_abspath = "{}{}entire4.ts".format(prefix, base_uri + "/")
    expected_ts4_path = "entire4.ts"
    expected_ts5_abspath = "{}{}entire5.ts".format(prefix, base_uri + "/")
    expected_ts5_path = "./entire5.ts"
    expected_ts6_abspath = "{}{}entire6.ts".format(prefix, base_uri + "/")
    expected_ts6_path = ".//entire6.ts"

    assert isinstance(obj, m3u8.M3U8)
    assert expected_key_path == obj.keys[0].uri
    assert expected_key_abspath == obj.keys[0].absolute_uri
    assert expected_ts1_path == obj.segments[0].uri
    assert expected_ts1_abspath == obj.segments[0].absolute_uri
    assert expected_ts2_path == obj.segments[1].uri
    assert expected_ts2_abspath == obj.segments[1].absolute_uri
    assert expected_ts3_path == obj.segments[2].uri
    assert expected_ts3_abspath == obj.segments[2].absolute_uri
    assert expected_ts4_path == obj.segments[3].uri
    assert expected_ts4_abspath == obj.segments[3].absolute_uri
    assert expected_ts5_path == obj.segments[4].uri
    assert expected_ts5_abspath == obj.segments[4].absolute_uri
    assert expected_ts6_path == obj.segments[5].uri
    assert expected_ts6_abspath == obj.segments[5].absolute_uri


def test_there_should_not_be_absolute_uris_with_loads():
    with open(playlists.RELATIVE_PLAYLIST_FILENAME) as f:
        content = f.read()
    obj = m3u8.loads(content)
    with pytest.raises(ValueError) as e:
        obj.keys[0].absolute_uri
    assert str(e.value) == "There can not be `absolute_uri` with no `base_uri` set"


def test_absolute_uri_should_handle_empty_base_uri_path():
    key = m3u8.model.Key(method="AES", uri="/key.bin", base_uri="http://example.com")
    assert "http://example.com/key.bin" == key.absolute_uri


def test_presence_of_base_uri_if_provided_when_loading_from_string():
    with open(playlists.RELATIVE_PLAYLIST_FILENAME) as f:
        content = f.read()
    obj = m3u8.loads(content, uri="http://media.example.com/path/playlist.m3u8")
    assert obj.base_uri == "http://media.example.com/path/"


def test_raise_timeout_exception_if_timeout_happens_when_loading_from_uri():
    try:
        m3u8.load(playlists.TIMEOUT_SIMPLE_PLAYLIST_URI, timeout=1)
    except socket.timeout:
        assert True
    else:
        assert False
