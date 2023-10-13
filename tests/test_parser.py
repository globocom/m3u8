# Copyright 2014 Globo.com Player authors. All rights reserved.
# Use of this source code is governed by a MIT License
# license that can be found in the LICENSE file.
import re

import playlists
import pytest

import m3u8
from m3u8.parser import (
    ParseError,
    _parse_simple_parameter_raw_value,
    cast_date_time,
    get_segment_custom_value,
    save_segment_custom_value,
)


def test_should_parse_simple_playlist_from_string():
    data = m3u8.parse(playlists.SIMPLE_PLAYLIST)
    assert data["targetduration"] == 5220
    assert data["media_sequence"] == 0
    assert ["http://media.example.com/entire.ts"] == [
        c["uri"] for c in data["segments"]
    ]
    assert [5220] == [c["duration"] for c in data["segments"]]


def test_should_parse_non_integer_duration_from_playlist_string():
    data = m3u8.parse(playlists.PLAYLIST_WITH_NON_INTEGER_DURATION)
    assert data["targetduration"] == 5220.5
    assert [5220.5] == [c["duration"] for c in data["segments"]]


def test_should_parse_comma_in_title():
    data = m3u8.parse(playlists.SIMPLE_PLAYLIST_TITLE_COMMA)
    assert ["Title with a comma, end"] == [c["title"] for c in data["segments"]]


def test_should_parse_simple_playlist_from_string_with_different_linebreaks():
    data = m3u8.parse(playlists.SIMPLE_PLAYLIST.replace("\n", "\r\n"))
    assert data["targetduration"] == 5220
    assert ["http://media.example.com/entire.ts"] == [
        c["uri"] for c in data["segments"]
    ]
    assert [5220] == [c["duration"] for c in data["segments"]]


def test_should_parse_sliding_window_playlist_from_string():
    data = m3u8.parse(playlists.SLIDING_WINDOW_PLAYLIST)
    assert data["targetduration"] == 8
    assert data["media_sequence"] == 2680
    assert [
        "https://priv.example.com/fileSequence2680.ts",
        "https://priv.example.com/fileSequence2681.ts",
        "https://priv.example.com/fileSequence2682.ts",
    ] == [c["uri"] for c in data["segments"]]
    assert [8, 8, 8] == [c["duration"] for c in data["segments"]]


def test_should_parse_playlist_with_encrypted_segments_from_string():
    data = m3u8.parse(playlists.PLAYLIST_WITH_ENCRYPTED_SEGMENTS)
    assert data["media_sequence"] == 7794
    assert data["targetduration"] == 15
    assert data["keys"][0]["method"] == "AES-128"
    assert data["keys"][0]["uri"] == "https://priv.example.com/key.php?r=52"
    assert [
        "http://media.example.com/fileSequence52-1.ts",
        "http://media.example.com/fileSequence52-2.ts",
        "http://media.example.com/fileSequence52-3.ts",
    ] == [c["uri"] for c in data["segments"]]
    assert [15, 15, 15] == [c["duration"] for c in data["segments"]]


def test_should_load_playlist_with_iv_from_string():
    data = m3u8.parse(playlists.PLAYLIST_WITH_ENCRYPTED_SEGMENTS_AND_IV)
    assert data["keys"][0]["uri"] == "/hls-key/key.bin"
    assert data["keys"][0]["method"] == "AES-128"
    assert data["keys"][0]["iv"] == "0X10ef8f758ca555115584bb5b3c687f52"


def test_should_add_key_attribute_to_segment_from_playlist():
    data = m3u8.parse(
        playlists.PLAYLIST_WITH_ENCRYPTED_SEGMENTS_AND_IV_WITH_MULTIPLE_KEYS
    )
    first_segment_key = data["segments"][0]["key"]
    assert first_segment_key["uri"] == "/hls-key/key.bin"
    assert first_segment_key["method"] == "AES-128"
    assert first_segment_key["iv"] == "0X10ef8f758ca555115584bb5b3c687f52"
    last_segment_key = data["segments"][-1]["key"]
    assert last_segment_key["uri"] == "/hls-key/key2.bin"
    assert last_segment_key["method"] == "AES-128"
    assert last_segment_key["iv"] == "0Xcafe8f758ca555115584bb5b3c687f52"


def test_should_add_non_key_for_multiple_keys_unencrypted_and_encrypted():
    data = m3u8.parse(playlists.PLAYLIST_WITH_MULTIPLE_KEYS_UNENCRYPTED_AND_ENCRYPTED)
    # First two segments have no Key, so it's not in the dictionary
    assert "key" not in data["segments"][0]
    assert "key" not in data["segments"][1]
    third_segment_key = data["segments"][2]["key"]
    assert third_segment_key["uri"] == "/hls-key/key.bin"
    assert third_segment_key["method"] == "AES-128"
    assert third_segment_key["iv"] == "0X10ef8f758ca555115584bb5b3c687f52"
    last_segment_key = data["segments"][-1]["key"]
    assert last_segment_key["uri"] == "/hls-key/key2.bin"
    assert last_segment_key["method"] == "AES-128"
    assert last_segment_key["iv"] == "0Xcafe8f758ca555115584bb5b3c687f52"


def test_should_handle_key_method_none_and_no_uri_attr():
    data = m3u8.parse(
        playlists.PLAYLIST_WITH_MULTIPLE_KEYS_UNENCRYPTED_AND_ENCRYPTED_NONE_AND_NO_URI_ATTR
    )
    assert "key" not in data["segments"][0]
    assert "key" not in data["segments"][1]
    third_segment_key = data["segments"][2]["key"]
    assert third_segment_key["uri"] == "/hls-key/key.bin"
    assert third_segment_key["method"] == "AES-128"
    assert third_segment_key["iv"] == "0X10ef8f758ca555115584bb5b3c687f52"
    assert data["segments"][6]["key"]["method"] == "NONE"


def test_should_parse_playlist_with_session_encrypted_segments_from_string():
    data = m3u8.parse(playlists.PLAYLIST_WITH_SESSION_ENCRYPTED_SEGMENTS)
    assert data["media_sequence"] == 7794
    assert data["targetduration"] == 15
    assert data["session_keys"][0]["method"] == "AES-128"
    assert data["session_keys"][0]["uri"] == "https://priv.example.com/key.php?r=52"
    assert [
        "http://media.example.com/fileSequence52-1.ts",
        "http://media.example.com/fileSequence52-2.ts",
        "http://media.example.com/fileSequence52-3.ts",
    ] == [c["uri"] for c in data["segments"]]
    assert [15, 15, 15] == [c["duration"] for c in data["segments"]]


def test_should_load_playlist_with_session_iv_from_string():
    data = m3u8.parse(playlists.PLAYLIST_WITH_SESSION_ENCRYPTED_SEGMENTS_AND_IV)
    assert data["session_keys"][0]["uri"] == "/hls-key/key.bin"
    assert data["session_keys"][0]["method"] == "AES-128"
    assert data["session_keys"][0]["iv"] == "0X10ef8f758ca555115584bb5b3c687f52"


def test_should_parse_quoted_title_from_playlist():
    data = m3u8.parse(playlists.SIMPLE_PLAYLIST_WITH_QUOTED_TITLE)
    assert len(data["segments"]) == 1
    assert data["segments"][0]["duration"] == 5220
    assert data["segments"][0]["title"] == '"A sample title"'
    assert data["segments"][0]["uri"] == "http://media.example.com/entire.ts"


def test_should_parse_unquoted_title_from_playlist():
    data = m3u8.parse(playlists.SIMPLE_PLAYLIST_WITH_UNQUOTED_TITLE)
    assert len(data["segments"]) == 1
    assert data["segments"][0]["duration"] == 5220
    assert data["segments"][0]["title"] == "A sample unquoted title"
    assert data["segments"][0]["uri"] == "http://media.example.com/entire.ts"


def test_should_parse_variant_playlist():
    data = m3u8.parse(playlists.VARIANT_PLAYLIST)
    playlists_list = list(data["playlists"])

    assert True is data["is_variant"]
    assert None is data["media_sequence"]
    assert len(playlists_list) == 4

    assert playlists_list[0]["uri"] == "http://example.com/low.m3u8"
    assert playlists_list[0]["stream_info"]["program_id"] == 1
    assert playlists_list[0]["stream_info"]["bandwidth"] == 1280000

    assert playlists_list[-1]["uri"] == "http://example.com/audio-only.m3u8"
    assert playlists_list[-1]["stream_info"]["program_id"] == 1
    assert playlists_list[-1]["stream_info"]["bandwidth"] == 65000
    assert playlists_list[-1]["stream_info"]["codecs"] == "mp4a.40.5,avc1.42801e"


def test_should_parse_variant_playlist_with_cc_subtitles_and_audio():
    data = m3u8.parse(playlists.VARIANT_PLAYLIST_WITH_CC_SUBS_AND_AUDIO)
    playlists_list = list(data["playlists"])

    assert True is data["is_variant"]
    assert None is data["media_sequence"]
    assert len(playlists_list) == 2

    assert playlists_list[0]["uri"] == "http://example.com/with-cc-hi.m3u8"
    assert playlists_list[0]["stream_info"]["program_id"] == 1
    assert playlists_list[0]["stream_info"]["bandwidth"] == 7680000
    assert playlists_list[0]["stream_info"]["closed_captions"] == '"cc"'
    assert playlists_list[0]["stream_info"]["subtitles"] == "sub"
    assert playlists_list[0]["stream_info"]["audio"] == "aud"

    assert playlists_list[-1]["uri"] == "http://example.com/with-cc-low.m3u8"
    assert playlists_list[-1]["stream_info"]["program_id"] == 1
    assert playlists_list[-1]["stream_info"]["bandwidth"] == 65000
    assert playlists_list[-1]["stream_info"]["closed_captions"] == '"cc"'
    assert playlists_list[-1]["stream_info"]["subtitles"] == "sub"
    assert playlists_list[-1]["stream_info"]["audio"] == "aud"


def test_should_parse_variant_playlist_with_none_cc_and_audio():
    data = m3u8.parse(playlists.VARIANT_PLAYLIST_WITH_NONE_CC_AND_AUDIO)
    playlists_list = list(data["playlists"])

    assert playlists_list[0]["stream_info"]["closed_captions"] == "NONE"
    assert playlists_list[-1]["stream_info"]["closed_captions"] == "NONE"


def test_should_parse_variant_playlist_with_average_bandwidth():
    data = m3u8.parse(playlists.VARIANT_PLAYLIST_WITH_AVERAGE_BANDWIDTH)
    playlists_list = list(data["playlists"])
    assert playlists_list[0]["stream_info"]["bandwidth"] == 1280000
    assert playlists_list[0]["stream_info"]["average_bandwidth"] == 1252345
    assert playlists_list[1]["stream_info"]["bandwidth"] == 2560000
    assert playlists_list[1]["stream_info"]["average_bandwidth"] == 2466570
    assert playlists_list[2]["stream_info"]["bandwidth"] == 7680000
    assert playlists_list[2]["stream_info"]["average_bandwidth"] == 7560423
    assert playlists_list[3]["stream_info"]["bandwidth"] == 65000
    assert playlists_list[3]["stream_info"]["average_bandwidth"] == 63005


def test_should_parse_variant_playlist_with_video_range():
    data = m3u8.parse(playlists.VARIANT_PLAYLIST_WITH_VIDEO_RANGE)
    playlists_list = list(data["playlists"])
    assert playlists_list[0]["stream_info"]["video_range"] == "SDR"
    assert playlists_list[1]["stream_info"]["video_range"] == "PQ"


def test_should_parse_variant_playlist_with_hdcp_level():
    data = m3u8.parse(playlists.VARIANT_PLAYLIST_WITH_HDCP_LEVEL)
    playlists_list = list(data["playlists"])
    assert playlists_list[0]["stream_info"]["hdcp_level"] == "NONE"
    assert playlists_list[1]["stream_info"]["hdcp_level"] == "TYPE-0"
    assert playlists_list[2]["stream_info"]["hdcp_level"] == "TYPE-1"


# This is actually not according to specification but as for example Twitch.tv
# is producing master playlists that have bandwidth as floats (issue 72)
# this tests that this situation does not break the parser and will just
# truncate to a decimal-integer according to specification
def test_should_parse_variant_playlist_with_bandwidth_as_float():
    data = m3u8.parse(playlists.VARIANT_PLAYLIST_WITH_BANDWIDTH_FLOAT)
    playlists_list = list(data["playlists"])
    assert playlists_list[0]["stream_info"]["bandwidth"] == 1280000
    assert playlists_list[1]["stream_info"]["bandwidth"] == 2560000
    assert playlists_list[2]["stream_info"]["bandwidth"] == 7680000
    assert playlists_list[3]["stream_info"]["bandwidth"] == 65000


def test_should_parse_variant_playlist_with_iframe_playlists():
    data = m3u8.parse(playlists.VARIANT_PLAYLIST_WITH_IFRAME_PLAYLISTS)
    iframe_playlists = list(data["iframe_playlists"])

    assert True is data["is_variant"]

    assert len(iframe_playlists) == 4

    assert iframe_playlists[0]["iframe_stream_info"]["program_id"] == 1
    assert iframe_playlists[0]["iframe_stream_info"]["bandwidth"] == 151288
    assert iframe_playlists[0]["iframe_stream_info"]["resolution"] == "624x352"
    assert iframe_playlists[0]["iframe_stream_info"]["codecs"] == "avc1.4d001f"
    assert iframe_playlists[0]["uri"] == "video-800k-iframes.m3u8"

    assert iframe_playlists[-1]["iframe_stream_info"]["bandwidth"] == 38775
    assert (iframe_playlists[-1]["iframe_stream_info"]["codecs"]) == "avc1.4d001f"
    assert iframe_playlists[-1]["uri"] == "video-150k-iframes.m3u8"


def test_should_parse_variant_playlist_with_alt_iframe_playlists_layout():
    data = m3u8.parse(playlists.VARIANT_PLAYLIST_WITH_ALT_IFRAME_PLAYLISTS_LAYOUT)
    iframe_playlists = list(data["iframe_playlists"])

    assert True is data["is_variant"]

    assert len(iframe_playlists) == 4

    assert iframe_playlists[0]["iframe_stream_info"]["program_id"] == 1
    assert iframe_playlists[0]["iframe_stream_info"]["bandwidth"] == 151288
    assert iframe_playlists[0]["iframe_stream_info"]["resolution"] == "624x352"
    assert iframe_playlists[0]["iframe_stream_info"]["codecs"] == "avc1.4d001f"
    assert iframe_playlists[0]["uri"] == "video-800k-iframes.m3u8"

    assert iframe_playlists[-1]["iframe_stream_info"]["bandwidth"] == 38775
    assert (iframe_playlists[-1]["iframe_stream_info"]["codecs"]) == "avc1.4d001f"
    assert iframe_playlists[-1]["uri"] == "video-150k-iframes.m3u8"


def test_should_parse_iframe_playlist():
    data = m3u8.parse(playlists.IFRAME_PLAYLIST)

    assert True is data["is_i_frames_only"]
    assert data["segments"][0]["duration"] == 4.12
    assert data["segments"][0]["byterange"] == "9400@376"
    assert data["segments"][0]["uri"] == "segment1.ts"


def test_should_parse_variant_playlist_with_image_playlists():
    data = m3u8.parse(playlists.VARIANT_PLAYLIST_WITH_IMAGE_PLAYLISTS)
    image_playlists = list(data['image_playlists'])

    assert True is data['is_variant']
    assert len(image_playlists) == 2
    assert image_playlists[0]['image_stream_info']['resolution'] == '320x180'
    assert image_playlists[0]['image_stream_info']['codecs'] == 'jpeg'
    assert image_playlists[0]['uri'] == '5x2_320x180/320x180-5x2.m3u8'
    assert image_playlists[1]['image_stream_info']['resolution'] == '640x360'
    assert image_playlists[1]['image_stream_info']['codecs'] == 'jpeg'
    assert image_playlists[1]['uri'] == '5x2_640x360/640x360-5x2.m3u8'

def test_should_parse_vod_image_playlist():
    data = m3u8.parse(playlists.VOD_IMAGE_PLAYLIST)

    assert True is data['is_images_only']
    assert len(data['tiles']) == 8
    assert data['segments'][0]['uri'] == 'preroll-ad-1.jpg'
    assert data['tiles'][0]['resolution'] == '640x360'
    assert data['tiles'][0]['layout'] == '5x2'
    assert data['tiles'][0]['duration'] == 6.006
    assert 'byterange' not in data['tiles'][0]

def test_should_parse_vod_image_playlist2():
    data = m3u8.parse(playlists.VOD_IMAGE_PLAYLIST2)

    assert True is data['is_images_only']
    assert data['tiles'][0]['resolution'] == '640x360'
    assert data['tiles'][0]['layout'] == '4x3'
    assert data['tiles'][0]['duration'] == 2.002
    assert len(data['tiles']) == 6
    assert data['segments'][0]['uri'] == 'promo_1.jpg'

def test_should_parse_live_image_playlist():
    data = m3u8.parse(playlists.LIVE_IMAGE_PLAYLIST)

    assert True is data['is_images_only']
    assert len(data['segments']) == 10
    assert data['segments'][0]['uri'] == 'content-123.jpg'
    assert data['segments'][1]['uri'] == 'content-124.jpg'
    assert data['segments'][2]['uri'] == 'content-125.jpg'
    assert data['segments'][3]['uri'] == 'missing-midroll.jpg'
    assert data['segments'][4]['uri'] == 'missing-midroll.jpg'
    assert data['segments'][5]['uri'] == 'missing-midroll.jpg'
    assert data['segments'][6]['uri'] == 'content-128.jpg'
    assert data['segments'][7]['uri'] == 'content-129.jpg'
    assert data['segments'][8]['uri'] == 'content-130.jpg'
    assert data['segments'][9]['uri'] == 'content-131.jpg'

def test_should_parse_playlist_using_byteranges():
    data = m3u8.parse(playlists.PLAYLIST_USING_BYTERANGES)

    assert False is data["is_i_frames_only"]
    assert data["segments"][0]["duration"] == 10
    assert data["segments"][0]["byterange"] == "76242@0"
    assert data["segments"][0]["uri"] == "segment.ts"


def test_should_parse_endlist_playlist():
    data = m3u8.parse(playlists.SIMPLE_PLAYLIST)
    assert True is data["is_endlist"]

    data = m3u8.parse(playlists.SLIDING_WINDOW_PLAYLIST)
    assert False is data["is_endlist"]


def test_should_parse_ALLOW_CACHE():
    data = m3u8.parse(playlists.PLAYLIST_WITH_ENCRYPTED_SEGMENTS_AND_IV)
    assert data["allow_cache"] == "no"


def test_should_parse_VERSION():
    data = m3u8.parse(playlists.PLAYLIST_WITH_ENCRYPTED_SEGMENTS_AND_IV)
    assert data["version"] == 2


def test_should_parse_program_date_time_from_playlist():
    data = m3u8.parse(playlists.SIMPLE_PLAYLIST_WITH_PROGRAM_DATE_TIME)
    assert cast_date_time("2014-08-13T13:36:33+00:00") == data["program_date_time"]


def test_should_parse_scte35_from_playlist():
    data = m3u8.parse(playlists.CUE_OUT_ELEMENTAL_PLAYLIST)

    # cue_out should be maintained from [EXT-X-CUE-OUT, EXT-X-CUE-IN)
    actual_cue_status = [s["cue_out"] for s in data["segments"]]
    expected_cue_status = [
        False,
        False,
        False,
        True,
        True,
        True,
        True,
        True,
        True,
        False,
        False,
    ]
    assert actual_cue_status == expected_cue_status

    # scte35 should be maintained from [EXT-X-CUE-OUT, EXT-X-CUE-IN]
    cue = "/DAlAAAAAAAAAP/wFAUAAAABf+//wpiQkv4ARKogAAEBAQAAQ6sodg=="
    actual_scte35 = [s["scte35"] for s in data["segments"]]
    expected_scte35 = [None, None, None, cue, cue, cue, cue, cue, cue, cue, None]
    assert actual_scte35 == expected_scte35

    # oatcls_scte35 should be maintained from [EXT-X-CUE-OUT, EXT-X-CUE-IN]
    actual_oatcls_scte35 = [s["oatcls_scte35"] for s in data["segments"]]
    expected_oatcls_scte35 = [None, None, None, cue, cue, cue, cue, cue, cue, cue, None]
    assert actual_oatcls_scte35 == expected_oatcls_scte35

    # durations should be maintained from  from [EXT-X-CUE-OUT, EXT-X-CUE-IN]
    actual_scte35_duration = [s["scte35_duration"] for s in data["segments"]]
    expected_scte35_duration = [
        None,
        None,
        None,
        "50.000",
        "50",
        "50",
        "50",
        "50",
        "50",
        "50",
        None,
    ]
    assert actual_scte35_duration == expected_scte35_duration


def test_should_parse_envivio_cue_playlist():
    data = m3u8.parse(playlists.CUE_OUT_ENVIVIO_PLAYLIST)
    assert data["segments"][3]["scte35"]
    assert data["segments"][3]["cue_out"]
    assert (
        data["segments"][3]["scte35"]
        == "/DAlAAAENOOQAP/wFAUBAABrf+//N25XDf4B9p/gAAEBAQAAxKni9A=="
    )
    assert data["segments"][3]["scte35_duration"] == "366"
    assert data["segments"][4]["cue_out"]
    assert (
        data["segments"][4]["scte35"]
        == "/DAlAAAENOOQAP/wFAUBAABrf+//N25XDf4B9p/gAAEBAQAAxKni9A=="
    )
    assert (
        data["segments"][5]["scte35"]
        == "/DAlAAAENOOQAP/wFAUBAABrf+//N25XDf4B9p/gAAEBAQAAxKni9A=="
    )


def test_should_parse_no_duration_cue_playlist():
    data = m3u8.parse(playlists.CUE_OUT_NO_DURATION_PLAYLIST)
    assert data["segments"][0]["cue_out_start"]
    assert data["segments"][2]["cue_in"]


def test_parse_simple_playlist_messy():
    data = m3u8.parse(playlists.SIMPLE_PLAYLIST_MESSY)
    assert data["targetduration"] == 5220
    assert data["media_sequence"] == 0
    assert ["http://media.example.com/entire.ts"] == [
        c["uri"] for c in data["segments"]
    ]
    assert [5220] == [c["duration"] for c in data["segments"]]


def test_parse_simple_playlist_messy_strict():
    with pytest.raises(ParseError) as catch:
        m3u8.parse(playlists.SIMPLE_PLAYLIST_MESSY, strict=True)
    assert str(catch.value) == "Syntax error in manifest on line 5: JUNK"


def test_commaless_extinf():
    data = m3u8.parse(playlists.SIMPLE_PLAYLIST_COMMALESS_EXTINF)
    assert data["targetduration"] == 5220
    assert data["media_sequence"] == 0
    assert ["http://media.example.com/entire.ts"] == [
        c["uri"] for c in data["segments"]
    ]
    assert [5220] == [c["duration"] for c in data["segments"]]


def test_commaless_extinf_strict():
    with pytest.raises(ParseError) as e:
        m3u8.parse(playlists.SIMPLE_PLAYLIST_COMMALESS_EXTINF, strict=True)
    assert str(e.value) == "Syntax error in manifest on line 3: #EXTINF:5220"


def test_should_parse_segment_map_uri():
    data = m3u8.parse(playlists.MAP_URI_PLAYLIST)
    assert data["segment_map"][0]["uri"] == "fileSequence0.mp4"


def test_should_parse_segment_map_uri_with_byterange():
    data = m3u8.parse(playlists.MAP_URI_PLAYLIST_WITH_BYTERANGE)
    assert data["segment_map"][0]["uri"] == "main.mp4"


def test_should_parse_multiple_map_attributes():
    data = m3u8.parse(playlists.MULTIPLE_MAP_URI_PLAYLIST)

    assert data["segments"][0]["init_section"]["uri"] == "init1.mp4"
    assert data["segments"][1]["init_section"]["uri"] == "init1.mp4"
    assert data["segments"][2]["init_section"]["uri"] == "init3.mp4"


def test_should_parse_empty_uri_with_base_path():
    data = m3u8.M3U8(
        playlists.MEDIA_WITHOUT_URI_PLAYLIST, base_path="base_path", base_uri="base_uri"
    )
    media = data.media[0]
    assert media.uri is None
    assert media.base_path is None
    assert media.base_uri == "base_uri/"


def test_should_parse_audio_channels():
    data = m3u8.M3U8(
        playlists.MEDIA_WITHOUT_URI_PLAYLIST, base_path="base_path", base_uri="base_uri"
    )
    media = data.media[0]
    assert media.channels == "2"


def test_should_parse_start_with_negative_time_offset():
    data = m3u8.parse(playlists.SIMPLE_PLAYLIST_WITH_START_NEGATIVE_OFFSET)
    assert data["start"]["time_offset"] == -2.0
    assert not hasattr(data["start"], "precise")


def test_should_parse_start_with_precise():
    data = m3u8.parse(playlists.SIMPLE_PLAYLIST_WITH_START_PRECISE)
    assert data["start"]["time_offset"] == 10.5
    assert data["start"]["precise"] == "YES"


def test_should_parse_session_data():
    data = m3u8.parse(playlists.SESSION_DATA_PLAYLIST)
    assert data["session_data"][0]["data_id"] == "com.example.value"
    assert data["session_data"][0]["value"] == "example"
    assert data["session_data"][0]["language"] == "en"


def test_should_parse_multiple_session_data():
    data = m3u8.parse(playlists.MULTIPLE_SESSION_DATA_PLAYLIST)

    assert len(data["session_data"]) == 4

    assert data["session_data"][0]["data_id"] == "com.example.value"
    assert data["session_data"][0]["value"] == "example"
    assert data["session_data"][0]["language"] == "en"

    assert data["session_data"][1]["data_id"] == "com.example.value"
    assert data["session_data"][1]["value"] == "example"
    assert data["session_data"][1]["language"] == "ru"

    assert data["session_data"][2]["data_id"] == "com.example.value"
    assert data["session_data"][2]["value"] == "example"
    assert data["session_data"][2]["language"] == "de"

    assert data["session_data"][3]["data_id"] == "com.example.title"
    assert data["session_data"][3]["uri"] == "title.json"


def test_simple_playlist_with_discontinuity_sequence():
    data = m3u8.parse(playlists.SIMPLE_PLAYLIST_WITH_DISCONTINUITY_SEQUENCE)
    assert data["discontinuity_sequence"] == 123


def test_simple_playlist_with_custom_tags():
    def get_movie(line, lineno, data, segment):
        if line.startswith("#EXT-X-MOVIE"):
            custom_tag = line.split(":")
            if len(custom_tag) == 2:
                data["movie"] = custom_tag[1].strip()
                return True

    data = m3u8.parse(
        playlists.SIMPLE_PLAYLIST_WITH_CUSTOM_TAGS,
        strict=False,
        custom_tags_parser=get_movie,
    )
    assert data["movie"] == "million dollar baby"
    assert data["targetduration"] == 5220
    assert data["media_sequence"] == 0
    assert ["http://media.example.com/entire.ts"] == [
        c["uri"] for c in data["segments"]
    ]
    assert [5220] == [c["duration"] for c in data["segments"]]


def test_iptv_playlist_with_custom_tags():
    def parse_iptv_attributes(line, lineno, data, state):
        # Customize parsing #EXTINF
        if line.startswith("#EXTINF"):
            chunks = line.replace("#EXTINF" + ":", "").split(",", 1)
            if len(chunks) == 2:
                duration_and_props, title = chunks
            elif len(chunks) == 1:
                duration_and_props = chunks[0]
                title = ""

            additional_props = {}
            chunks = duration_and_props.strip().split(" ", 1)
            if len(chunks) == 2:
                duration, raw_props = chunks
                matched_props = re.finditer(r'([\w\-]+)="([^"]*)"', raw_props)
                for match in matched_props:
                    additional_props[match.group(1)] = match.group(2)
            else:
                duration = duration_and_props

            if "segment" not in state:
                state["segment"] = {}
            state["segment"]["duration"] = float(duration)
            state["segment"]["title"] = title

            save_segment_custom_value(state, "extinf_props", additional_props)

            state["expect_segment"] = True
            return True

        # Parse #EXTGRP
        if line.startswith("#EXTGRP"):
            _, value = _parse_simple_parameter_raw_value(line, str)
            save_segment_custom_value(state, "extgrp", value)
            state["expect_segment"] = True
            return True

        # Parse #EXTVLCOPT
        if line.startswith("#EXTVLCOPT"):
            _, value = _parse_simple_parameter_raw_value(line, str)

            existing_opts = get_segment_custom_value(state, "vlcopt", [])
            existing_opts.append(value)
            save_segment_custom_value(state, "vlcopt", existing_opts)

            state["expect_segment"] = True
            return True

    data = m3u8.parse(
        playlists.IPTV_PLAYLIST_WITH_CUSTOM_TAGS,
        strict=False,
        custom_tags_parser=parse_iptv_attributes,
    )

    assert ["Channel1"] == [c["title"] for c in data["segments"]]
    assert (
        data["segments"][0]["uri"]
        == "http://str00.iptv.domain/7331/mpegts?token=longtokenhere"
    )
    assert (
        data["segments"][0]["custom_parser_values"]["extinf_props"]["tvg-id"]
        == "channel1"
    )
    assert (
        data["segments"][0]["custom_parser_values"]["extinf_props"]["group-title"]
        == "Group1"
    )
    assert (
        data["segments"][0]["custom_parser_values"]["extinf_props"]["catchup-days"]
        == "7"
    )
    assert (
        data["segments"][0]["custom_parser_values"]["extinf_props"]["catchup-type"]
        == "flussonic"
    )
    assert data["segments"][0]["custom_parser_values"]["extgrp"] == "ExtGroup1"
    assert data["segments"][0]["custom_parser_values"]["vlcopt"] == [
        "video-filter=invert",
        "param2=value2",
    ]


def test_tag_after_extinf():
    parsed_playlist = m3u8.loads(playlists.IPTV_PLAYLIST_WITH_EARLY_EXTINF)
    actual = parsed_playlist.segments[0].uri
    expected = 'http://str00.iptv.domain/7331/mpegts?token=longtokenhere'
    assert actual == expected


def test_master_playlist_with_frame_rate():
    data = m3u8.parse(playlists.VARIANT_PLAYLIST_WITH_FRAME_RATE)
    playlists_list = list(data["playlists"])
    assert playlists_list[0]["stream_info"]["frame_rate"] == 25
    assert playlists_list[1]["stream_info"]["frame_rate"] == 50
    assert playlists_list[2]["stream_info"]["frame_rate"] == 60
    assert playlists_list[3]["stream_info"]["frame_rate"] == 12.5


def test_master_playlist_with_unrounded_frame_rate():
    data = m3u8.parse(playlists.VARIANT_PLAYLIST_WITH_ROUNDABLE_FRAME_RATE)
    playlists_list = list(data["playlists"])
    assert playlists_list[0]["stream_info"]["frame_rate"] == 12.54321


def test_low_latency_playlist():
    data = m3u8.parse(playlists.LOW_LATENCY_DELTA_UPDATE_PLAYLIST)
    assert data["server_control"]["can_block_reload"] == "YES"
    assert data["server_control"]["can_skip_until"] == 12.0
    assert data["server_control"]["part_hold_back"] == 1.0
    assert data["part_inf"]["part_target"] == 0.33334
    assert data["skip"]["skipped_segments"] == 3
    assert len(data["segments"][2]["parts"]) == 12
    assert data["segments"][2]["parts"][0]["duration"] == 0.33334
    assert data["segments"][2]["parts"][0]["uri"] == "filePart271.0.ts"
    assert len(data["rendition_reports"]) == 2
    assert data["rendition_reports"][0]["uri"] == "../1M/waitForMSN.php"
    assert data["rendition_reports"][0]["last_msn"] == 273
    assert data["rendition_reports"][0]["last_part"] == 3


def test_low_latency_with_preload_and_byteranges_playlist():
    data = m3u8.parse(playlists.LOW_LATENCY_WITH_PRELOAD_AND_BYTERANGES_PLAYLIST)
    assert data["segments"][1]["parts"][2]["byterange"] == "18000@43000"
    assert data["preload_hint"]["type"] == "PART"
    assert data["preload_hint"]["uri"] == "fs271.mp4"
    assert data["preload_hint"]["byterange_start"] == 61000
    assert data["preload_hint"]["byterange_length"] == 20000


def test_negative_media_sequence():
    data = m3u8.parse(playlists.PLAYLIST_WITH_NEGATIVE_MEDIA_SEQUENCE)
    assert data["media_sequence"] == -2680


def test_daterange_simple():
    data = m3u8.parse(playlists.DATERANGE_SIMPLE_PLAYLIST)

    assert data["segments"][0]["dateranges"][0]["id"] == "ad3"
    assert data["segments"][0]["dateranges"][0]["start_date"] == "2016-06-13T11:15:00Z"
    assert data["segments"][0]["dateranges"][0]["duration"] == 20
    assert data["segments"][0]["dateranges"][0]["x_ad_id"] == '"1234"'
    assert (
        data["segments"][0]["dateranges"][0]["x_ad_url"]
        == '"http://ads.example.com/beacon3"'
    )


def test_date_range_with_scte_out_and_in():
    data = m3u8.parse(playlists.DATERANGE_SCTE35_OUT_AND_IN_PLAYLIST)

    assert data["segments"][0]["dateranges"][0]["id"] == "splice-6FFFFFF0"
    assert data["segments"][0]["dateranges"][0]["planned_duration"] == 59.993
    assert (
        data["segments"][0]["dateranges"][0]["scte35_out"]
        == "0xFC002F0000000000FF000014056FFFFFF000E011622DCAFF000052636200000000000A0008029896F50000008700000000"
    )

    assert data["segments"][6]["dateranges"][0]["id"] == "splice-6FFFFFF0"
    assert data["segments"][6]["dateranges"][0]["duration"] == 59.993
    assert (
        data["segments"][6]["dateranges"][0]["scte35_in"]
        == "0xFC002A0000000000FF00000F056FFFFFF000401162802E6100000000000A0008029896F50000008700000000"
    )


def test_date_range_in_parts():
    data = m3u8.parse(playlists.DATERANGE_IN_PART_PLAYLIST)

    assert data["segments"][0]["parts"][2]["dateranges"][0]["id"] == "test_id"
    assert (
        data["segments"][0]["parts"][2]["dateranges"][0]["start_date"]
        == "2020-03-10T07:48:02Z"
    )
    assert data["segments"][0]["parts"][2]["dateranges"][0]["class"] == "test_class"
    assert data["segments"][0]["parts"][2]["dateranges"][0]["end_on_next"] == "YES"


def test_gap():
    data = m3u8.parse(playlists.GAP_PLAYLIST)

    assert data["segments"][0]["gap_tag"] is None
    assert data["segments"][1]["gap_tag"] is True
    assert data["segments"][2]["gap_tag"] is True
    assert data["segments"][3]["gap_tag"] is None


def test_gap_in_parts():
    data = m3u8.parse(playlists.GAP_IN_PARTS_PLAYLIST)

    assert data["segments"][0]["parts"][0]["gap_tag"] is None
    assert data["segments"][0]["parts"][0].get("gap", None) is None
    assert data["segments"][0]["parts"][1]["gap_tag"] is None
    assert data["segments"][0]["parts"][1]["gap"] == "YES"
    assert data["segments"][0]["parts"][2]["gap_tag"] is True
    assert data["segments"][0]["parts"][2].get("gap", None) is None


def test_should_parse_variant_playlist_with_iframe_with_average_bandwidth():
    data = m3u8.parse(playlists.VARIANT_PLAYLIST_WITH_IFRAME_AVERAGE_BANDWIDTH)
    iframe_playlists = list(data["iframe_playlists"])

    assert True is data["is_variant"]

    assert len(iframe_playlists) == 4

    assert iframe_playlists[0]["iframe_stream_info"]["bandwidth"] == 151288
    # Check for absence of average_bandwidth if not given in the playlist
    assert "average_bandwidth" not in iframe_playlists[0]["iframe_stream_info"]
    assert iframe_playlists[0]["iframe_stream_info"]["resolution"] == "624x352"
    assert iframe_playlists[0]["iframe_stream_info"]["codecs"] == "avc1.4d001f"
    assert iframe_playlists[0]["uri"] == "video-800k-iframes.m3u8"

    assert iframe_playlists[-1]["iframe_stream_info"]["bandwidth"] == 38775
    assert (iframe_playlists[-1]["iframe_stream_info"]["codecs"]) == "avc1.4d001f"
    assert iframe_playlists[-1]["uri"] == "video-150k-iframes.m3u8"
    assert iframe_playlists[1]["iframe_stream_info"]["average_bandwidth"] == 155000
    assert iframe_playlists[2]["iframe_stream_info"]["average_bandwidth"] == 65000
    assert iframe_playlists[3]["iframe_stream_info"]["average_bandwidth"] == 30000


def test_should_parse_variant_playlist_with_iframe_with_video_range():
    data = m3u8.parse(playlists.VARIANT_PLAYLIST_WITH_IFRAME_VIDEO_RANGE)
    iframe_playlists = list(data["iframe_playlists"])

    assert True is data["is_variant"]

    assert len(iframe_playlists) == 4

    assert iframe_playlists[0]["uri"] == "http://example.com/sdr-iframes.m3u8"
    assert iframe_playlists[0]["iframe_stream_info"]["video_range"] == "SDR"
    assert iframe_playlists[1]["uri"] == "http://example.com/hdr-pq-iframes.m3u8"
    assert iframe_playlists[1]["iframe_stream_info"]["video_range"] == "PQ"
    assert iframe_playlists[2]["uri"] == "http://example.com/hdr-hlg-iframes.m3u8"
    assert iframe_playlists[2]["iframe_stream_info"]["video_range"] == "HLG"
    assert iframe_playlists[3]["uri"] == "http://example.com/unknown-iframes.m3u8"
    assert "video_range" not in iframe_playlists[3]["iframe_stream_info"]


def test_should_parse_variant_playlist_with_iframe_with_hdcp_level():
    data = m3u8.parse(playlists.VARIANT_PLAYLIST_WITH_IFRAME_HDCP_LEVEL)
    iframe_playlists = list(data["iframe_playlists"])

    assert True is data["is_variant"]

    assert len(iframe_playlists) == 4

    assert iframe_playlists[0]["uri"] == "http://example.com/none-iframes.m3u8"
    assert iframe_playlists[0]["iframe_stream_info"]["hdcp_level"] == "NONE"
    assert iframe_playlists[1]["uri"] == "http://example.com/type0-iframes.m3u8"
    assert iframe_playlists[1]["iframe_stream_info"]["hdcp_level"] == "TYPE-0"
    assert iframe_playlists[2]["uri"] == "http://example.com/type1-iframes.m3u8"
    assert iframe_playlists[2]["iframe_stream_info"]["hdcp_level"] == "TYPE-1"
    assert iframe_playlists[3]["uri"] == "http://example.com/unknown-iframes.m3u8"
    assert "hdcp_level" not in iframe_playlists[3]["iframe_stream_info"]


def test_delta_playlist_daterange_skipping():
    data = m3u8.parse(playlists.DELTA_UPDATE_SKIP_DATERANGES_PLAYLIST)
    assert data["skip"]["recently_removed_dateranges"] == "1"
    assert data["server_control"]["can_skip_dateranges"] == "YES"


def test_bitrate():
    data = m3u8.parse(playlists.BITRATE_PLAYLIST)
    assert data["segments"][0]["bitrate"] == "1674"
    assert data["segments"][1]["bitrate"] == "1625"


def test_content_steering():
    data = m3u8.parse(playlists.CONTENT_STEERING_PLAYLIST)
    assert data["content_steering"]["server_uri"] == "/steering?video=00012"
    assert data["content_steering"]["pathway_id"] == "CDN-A"
    assert data["playlists"][0]["stream_info"]["pathway_id"] == "CDN-A"
    assert data["playlists"][1]["stream_info"]["pathway_id"] == "CDN-A"
    assert data["playlists"][2]["stream_info"]["pathway_id"] == "CDN-B"
    assert data["playlists"][3]["stream_info"]["pathway_id"] == "CDN-B"


def test_cue_in_pops_scte35_data_and_duration():
    data = m3u8.parse(playlists.CUE_OUT_ELEMENTAL_PLAYLIST)
    assert data["segments"][9]["cue_in"] is True
    assert (
        data["segments"][9]["scte35"]
        == "/DAlAAAAAAAAAP/wFAUAAAABf+//wpiQkv4ARKogAAEBAQAAQ6sodg=="
    )
    assert data["segments"][9]["scte35_duration"] == "50"
    assert data["segments"][10]["cue_in"] is False
    assert data["segments"][10]["scte35"] is None
    assert data["segments"][10]["scte35_duration"] is None


def test_playlist_with_stable_variant_id():
    data = m3u8.parse(playlists.VARIANT_PLAYLIST_WITH_STABLE_VARIANT_ID)
    assert (
        data["playlists"][0]["stream_info"]["stable_variant_id"]
        == "eb9c6e4de930b36d9a67fbd38a30b39f865d98f4a203d2140bbf71fd58ad764e"
    )


def test_iframe_with_stable_variant_id():
    data = m3u8.parse(playlists.VARIANT_PLAYLIST_WITH_IFRAME_STABLE_VARIANT_ID)
    assert (
        data["iframe_playlists"][0]["iframe_stream_info"]["stable_variant_id"]
        == "415901312adff69b967a0644a54f8d00dc14004f36bc8293737e6b4251f60f3f"
    )


def test_media_with_stable_rendition_id():
    data = m3u8.parse(playlists.VARIANT_PLAYLIST_WITH_STABLE_RENDITION_ID)
    assert (
        data["media"][0]["stable_rendition_id"]
        == "a8213e27c12a158ea8660e0fe8bdcac6072ca26d984e7e8603652bc61fdceffa"
    )
