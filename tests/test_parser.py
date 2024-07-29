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
    assert 5220 == data["targetduration"]
    assert 0 == data["media_sequence"]
    assert ["http://media.example.com/entire.ts"] == [
        c["uri"] for c in data["segments"]
    ]
    assert [5220] == [c["duration"] for c in data["segments"]]


def test_should_parse_non_integer_duration_from_playlist_string():
    data = m3u8.parse(playlists.PLAYLIST_WITH_NON_INTEGER_DURATION)
    assert 5221 == data["targetduration"]
    assert [5220.5] == [c["duration"] for c in data["segments"]]


def test_should_parse_comma_in_title():
    data = m3u8.parse(playlists.SIMPLE_PLAYLIST_TITLE_COMMA)
    assert ["Title with a comma, end"] == [c["title"] for c in data["segments"]]


def test_should_parse_simple_playlist_from_string_with_different_linebreaks():
    data = m3u8.parse(playlists.SIMPLE_PLAYLIST.replace("\n", "\r\n"))
    assert 5220 == data["targetduration"]
    assert ["http://media.example.com/entire.ts"] == [
        c["uri"] for c in data["segments"]
    ]
    assert [5220] == [c["duration"] for c in data["segments"]]


def test_should_parse_sliding_window_playlist_from_string():
    data = m3u8.parse(playlists.SLIDING_WINDOW_PLAYLIST)
    assert 8 == data["targetduration"]
    assert 2680 == data["media_sequence"]
    assert [
        "https://priv.example.com/fileSequence2680.ts",
        "https://priv.example.com/fileSequence2681.ts",
        "https://priv.example.com/fileSequence2682.ts",
    ] == [c["uri"] for c in data["segments"]]
    assert [8, 8, 8] == [c["duration"] for c in data["segments"]]


def test_should_parse_playlist_with_encrypted_segments_from_string():
    data = m3u8.parse(playlists.PLAYLIST_WITH_ENCRYPTED_SEGMENTS)
    assert 7794 == data["media_sequence"]
    assert 15 == data["targetduration"]
    assert "AES-128" == data["keys"][0]["method"]
    assert "https://priv.example.com/key.php?r=52" == data["keys"][0]["uri"]
    assert [
        "http://media.example.com/fileSequence52-1.ts",
        "http://media.example.com/fileSequence52-2.ts",
        "http://media.example.com/fileSequence52-3.ts",
    ] == [c["uri"] for c in data["segments"]]
    assert [15, 15, 15] == [c["duration"] for c in data["segments"]]


def test_should_load_playlist_with_iv_from_string():
    data = m3u8.parse(playlists.PLAYLIST_WITH_ENCRYPTED_SEGMENTS_AND_IV)
    assert "/hls-key/key.bin" == data["keys"][0]["uri"]
    assert "AES-128" == data["keys"][0]["method"]
    assert "0X10ef8f758ca555115584bb5b3c687f52" == data["keys"][0]["iv"]


def test_should_add_key_attribute_to_segment_from_playlist():
    data = m3u8.parse(
        playlists.PLAYLIST_WITH_ENCRYPTED_SEGMENTS_AND_IV_WITH_MULTIPLE_KEYS
    )
    first_segment_key = data["segments"][0]["key"]
    assert "/hls-key/key.bin" == first_segment_key["uri"]
    assert "AES-128" == first_segment_key["method"]
    assert "0X10ef8f758ca555115584bb5b3c687f52" == first_segment_key["iv"]
    last_segment_key = data["segments"][-1]["key"]
    assert "/hls-key/key2.bin" == last_segment_key["uri"]
    assert "AES-128" == last_segment_key["method"]
    assert "0Xcafe8f758ca555115584bb5b3c687f52" == last_segment_key["iv"]


def test_should_add_non_key_for_multiple_keys_unencrypted_and_encrypted():
    data = m3u8.parse(playlists.PLAYLIST_WITH_MULTIPLE_KEYS_UNENCRYPTED_AND_ENCRYPTED)
    # First two segments have no Key, so it's not in the dictionary
    assert "key" not in data["segments"][0]
    assert "key" not in data["segments"][1]
    third_segment_key = data["segments"][2]["key"]
    assert "/hls-key/key.bin" == third_segment_key["uri"]
    assert "AES-128" == third_segment_key["method"]
    assert "0X10ef8f758ca555115584bb5b3c687f52" == third_segment_key["iv"]
    last_segment_key = data["segments"][-1]["key"]
    assert "/hls-key/key2.bin" == last_segment_key["uri"]
    assert "AES-128" == last_segment_key["method"]
    assert "0Xcafe8f758ca555115584bb5b3c687f52" == last_segment_key["iv"]


def test_should_handle_key_method_none_and_no_uri_attr():
    data = m3u8.parse(
        playlists.PLAYLIST_WITH_MULTIPLE_KEYS_UNENCRYPTED_AND_ENCRYPTED_NONE_AND_NO_URI_ATTR
    )
    assert "key" not in data["segments"][0]
    assert "key" not in data["segments"][1]
    third_segment_key = data["segments"][2]["key"]
    assert "/hls-key/key.bin" == third_segment_key["uri"]
    assert "AES-128" == third_segment_key["method"]
    assert "0X10ef8f758ca555115584bb5b3c687f52" == third_segment_key["iv"]
    assert "NONE" == data["segments"][6]["key"]["method"]


def test_should_parse_playlist_with_session_encrypted_segments_from_string():
    data = m3u8.parse(playlists.PLAYLIST_WITH_SESSION_ENCRYPTED_SEGMENTS)
    assert 7794 == data["media_sequence"]
    assert 15 == data["targetduration"]
    assert "AES-128" == data["session_keys"][0]["method"]
    assert "https://priv.example.com/key.php?r=52" == data["session_keys"][0]["uri"]
    assert [
        "http://media.example.com/fileSequence52-1.ts",
        "http://media.example.com/fileSequence52-2.ts",
        "http://media.example.com/fileSequence52-3.ts",
    ] == [c["uri"] for c in data["segments"]]
    assert [15, 15, 15] == [c["duration"] for c in data["segments"]]


def test_should_load_playlist_with_session_iv_from_string():
    data = m3u8.parse(playlists.PLAYLIST_WITH_SESSION_ENCRYPTED_SEGMENTS_AND_IV)
    assert "/hls-key/key.bin" == data["session_keys"][0]["uri"]
    assert "AES-128" == data["session_keys"][0]["method"]
    assert "0X10ef8f758ca555115584bb5b3c687f52" == data["session_keys"][0]["iv"]


def test_should_parse_quoted_title_from_playlist():
    data = m3u8.parse(playlists.SIMPLE_PLAYLIST_WITH_QUOTED_TITLE)
    assert 1 == len(data["segments"])
    assert 5220 == data["segments"][0]["duration"]
    assert '"A sample title"' == data["segments"][0]["title"]
    assert "http://media.example.com/entire.ts" == data["segments"][0]["uri"]


def test_should_parse_unquoted_title_from_playlist():
    data = m3u8.parse(playlists.SIMPLE_PLAYLIST_WITH_UNQUOTED_TITLE)
    assert 1 == len(data["segments"])
    assert 5220 == data["segments"][0]["duration"]
    assert "A sample unquoted title" == data["segments"][0]["title"]
    assert "http://media.example.com/entire.ts" == data["segments"][0]["uri"]


def test_should_parse_variant_playlist():
    data = m3u8.parse(playlists.VARIANT_PLAYLIST)
    playlists_list = list(data["playlists"])

    assert True is data["is_variant"]
    assert None is data["media_sequence"]
    assert 4 == len(playlists_list)

    assert "http://example.com/low.m3u8" == playlists_list[0]["uri"]
    assert 1 == playlists_list[0]["stream_info"]["program_id"]
    assert 1280000 == playlists_list[0]["stream_info"]["bandwidth"]

    assert "http://example.com/audio-only.m3u8" == playlists_list[-1]["uri"]
    assert 1 == playlists_list[-1]["stream_info"]["program_id"]
    assert 65000 == playlists_list[-1]["stream_info"]["bandwidth"]
    assert "mp4a.40.5,avc1.42801e" == playlists_list[-1]["stream_info"]["codecs"]


def test_should_parse_variant_playlist_with_cc_subtitles_and_audio():
    data = m3u8.parse(playlists.VARIANT_PLAYLIST_WITH_CC_SUBS_AND_AUDIO)
    playlists_list = list(data["playlists"])

    assert True is data["is_variant"]
    assert None is data["media_sequence"]
    assert 2 == len(playlists_list)

    assert "http://example.com/with-cc-hi.m3u8" == playlists_list[0]["uri"]
    assert 1 == playlists_list[0]["stream_info"]["program_id"]
    assert 7680000 == playlists_list[0]["stream_info"]["bandwidth"]
    assert '"cc"' == playlists_list[0]["stream_info"]["closed_captions"]
    assert "sub" == playlists_list[0]["stream_info"]["subtitles"]
    assert "aud" == playlists_list[0]["stream_info"]["audio"]

    assert "http://example.com/with-cc-low.m3u8" == playlists_list[-1]["uri"]
    assert 1 == playlists_list[-1]["stream_info"]["program_id"]
    assert 65000 == playlists_list[-1]["stream_info"]["bandwidth"]
    assert '"cc"' == playlists_list[-1]["stream_info"]["closed_captions"]
    assert "sub" == playlists_list[-1]["stream_info"]["subtitles"]
    assert "aud" == playlists_list[-1]["stream_info"]["audio"]


def test_should_parse_variant_playlist_with_none_cc_and_audio():
    data = m3u8.parse(playlists.VARIANT_PLAYLIST_WITH_NONE_CC_AND_AUDIO)
    playlists_list = list(data["playlists"])

    assert "NONE" == playlists_list[0]["stream_info"]["closed_captions"]
    assert "NONE" == playlists_list[-1]["stream_info"]["closed_captions"]


def test_should_parse_variant_playlist_with_average_bandwidth():
    data = m3u8.parse(playlists.VARIANT_PLAYLIST_WITH_AVERAGE_BANDWIDTH)
    playlists_list = list(data["playlists"])
    assert 1280000 == playlists_list[0]["stream_info"]["bandwidth"]
    assert 1252345 == playlists_list[0]["stream_info"]["average_bandwidth"]
    assert 2560000 == playlists_list[1]["stream_info"]["bandwidth"]
    assert 2466570 == playlists_list[1]["stream_info"]["average_bandwidth"]
    assert 7680000 == playlists_list[2]["stream_info"]["bandwidth"]
    assert 7560423 == playlists_list[2]["stream_info"]["average_bandwidth"]
    assert 65000 == playlists_list[3]["stream_info"]["bandwidth"]
    assert 63005 == playlists_list[3]["stream_info"]["average_bandwidth"]


def test_should_parse_variant_playlist_with_video_range():
    data = m3u8.parse(playlists.VARIANT_PLAYLIST_WITH_VIDEO_RANGE)
    playlists_list = list(data["playlists"])
    assert "SDR" == playlists_list[0]["stream_info"]["video_range"]
    assert "PQ" == playlists_list[1]["stream_info"]["video_range"]


def test_should_parse_variant_playlist_with_hdcp_level():
    data = m3u8.parse(playlists.VARIANT_PLAYLIST_WITH_HDCP_LEVEL)
    playlists_list = list(data["playlists"])
    assert "NONE" == playlists_list[0]["stream_info"]["hdcp_level"]
    assert "TYPE-0" == playlists_list[1]["stream_info"]["hdcp_level"]
    assert "TYPE-1" == playlists_list[2]["stream_info"]["hdcp_level"]


# This is actually not according to specification but as for example Twitch.tv
# is producing master playlists that have bandwidth as floats (issue 72)
# this tests that this situation does not break the parser and will just
# truncate to a decimal-integer according to specification
def test_should_parse_variant_playlist_with_bandwidth_as_float():
    data = m3u8.parse(playlists.VARIANT_PLAYLIST_WITH_BANDWIDTH_FLOAT)
    playlists_list = list(data["playlists"])
    assert 1280000 == playlists_list[0]["stream_info"]["bandwidth"]
    assert 2560000 == playlists_list[1]["stream_info"]["bandwidth"]
    assert 7680000 == playlists_list[2]["stream_info"]["bandwidth"]
    assert 65000 == playlists_list[3]["stream_info"]["bandwidth"]


def test_should_parse_variant_playlist_with_iframe_playlists():
    data = m3u8.parse(playlists.VARIANT_PLAYLIST_WITH_IFRAME_PLAYLISTS)
    iframe_playlists = list(data["iframe_playlists"])

    assert True is data["is_variant"]

    assert 4 == len(iframe_playlists)

    assert 1 == iframe_playlists[0]["iframe_stream_info"]["program_id"]
    assert 151288 == iframe_playlists[0]["iframe_stream_info"]["bandwidth"]
    assert "624x352" == iframe_playlists[0]["iframe_stream_info"]["resolution"]
    assert "avc1.4d001f" == iframe_playlists[0]["iframe_stream_info"]["codecs"]
    assert "video-800k-iframes.m3u8" == iframe_playlists[0]["uri"]

    assert 38775 == iframe_playlists[-1]["iframe_stream_info"]["bandwidth"]
    assert "avc1.4d001f" == (iframe_playlists[-1]["iframe_stream_info"]["codecs"])
    assert "video-150k-iframes.m3u8" == iframe_playlists[-1]["uri"]


def test_should_parse_variant_playlist_with_alt_iframe_playlists_layout():
    data = m3u8.parse(playlists.VARIANT_PLAYLIST_WITH_ALT_IFRAME_PLAYLISTS_LAYOUT)
    iframe_playlists = list(data["iframe_playlists"])

    assert True is data["is_variant"]

    assert 4 == len(iframe_playlists)

    assert 1 == iframe_playlists[0]["iframe_stream_info"]["program_id"]
    assert 151288 == iframe_playlists[0]["iframe_stream_info"]["bandwidth"]
    assert "624x352" == iframe_playlists[0]["iframe_stream_info"]["resolution"]
    assert "avc1.4d001f" == iframe_playlists[0]["iframe_stream_info"]["codecs"]
    assert "video-800k-iframes.m3u8" == iframe_playlists[0]["uri"]

    assert 38775 == iframe_playlists[-1]["iframe_stream_info"]["bandwidth"]
    assert "avc1.4d001f" == (iframe_playlists[-1]["iframe_stream_info"]["codecs"])
    assert "video-150k-iframes.m3u8" == iframe_playlists[-1]["uri"]


def test_should_parse_iframe_playlist():
    data = m3u8.parse(playlists.IFRAME_PLAYLIST)

    assert True is data["is_i_frames_only"]
    assert 4.12 == data["segments"][0]["duration"]
    assert "9400@376" == data["segments"][0]["byterange"]
    assert "segment1.ts" == data["segments"][0]["uri"]


def test_should_parse_variant_playlist_with_image_playlists():
    data = m3u8.parse(playlists.VARIANT_PLAYLIST_WITH_IMAGE_PLAYLISTS)
    image_playlists = list(data["image_playlists"])

    assert True is data["is_variant"]
    assert 2 == len(image_playlists)
    assert "320x180" == image_playlists[0]["image_stream_info"]["resolution"]
    assert "jpeg" == image_playlists[0]["image_stream_info"]["codecs"]
    assert "5x2_320x180/320x180-5x2.m3u8" == image_playlists[0]["uri"]
    assert "640x360" == image_playlists[1]["image_stream_info"]["resolution"]
    assert "jpeg" == image_playlists[1]["image_stream_info"]["codecs"]
    assert "5x2_640x360/640x360-5x2.m3u8" == image_playlists[1]["uri"]


def test_should_parse_vod_image_playlist():
    data = m3u8.parse(playlists.VOD_IMAGE_PLAYLIST)

    assert True is data["is_images_only"]
    assert 8 == len(data["tiles"])
    assert "preroll-ad-1.jpg" == data["segments"][0]["uri"]
    assert "640x360" == data["tiles"][0]["resolution"]
    assert "5x2" == data["tiles"][0]["layout"]
    assert 6.006 == data["tiles"][0]["duration"]
    assert "byterange" not in data["tiles"][0]


def test_should_parse_vod_image_playlist2():
    data = m3u8.parse(playlists.VOD_IMAGE_PLAYLIST2)

    assert True is data["is_images_only"]
    assert "640x360" == data["tiles"][0]["resolution"]
    assert "4x3" == data["tiles"][0]["layout"]
    assert 2.002 == data["tiles"][0]["duration"]
    assert 6 == len(data["tiles"])
    assert "promo_1.jpg" == data["segments"][0]["uri"]


def test_should_parse_live_image_playlist():
    data = m3u8.parse(playlists.LIVE_IMAGE_PLAYLIST)

    assert True is data["is_images_only"]
    assert 10 == len(data["segments"])
    assert "content-123.jpg" == data["segments"][0]["uri"]
    assert "content-124.jpg" == data["segments"][1]["uri"]
    assert "content-125.jpg" == data["segments"][2]["uri"]
    assert "missing-midroll.jpg" == data["segments"][3]["uri"]
    assert "missing-midroll.jpg" == data["segments"][4]["uri"]
    assert "missing-midroll.jpg" == data["segments"][5]["uri"]
    assert "content-128.jpg" == data["segments"][6]["uri"]
    assert "content-129.jpg" == data["segments"][7]["uri"]
    assert "content-130.jpg" == data["segments"][8]["uri"]
    assert "content-131.jpg" == data["segments"][9]["uri"]


def test_should_parse_playlist_using_byteranges():
    data = m3u8.parse(playlists.PLAYLIST_USING_BYTERANGES)

    assert False is data["is_i_frames_only"]
    assert 10 == data["segments"][0]["duration"]
    assert "76242@0" == data["segments"][0]["byterange"]
    assert "segment.ts" == data["segments"][0]["uri"]


def test_should_parse_endlist_playlist():
    data = m3u8.parse(playlists.SIMPLE_PLAYLIST)
    assert True is data["is_endlist"]

    data = m3u8.parse(playlists.SLIDING_WINDOW_PLAYLIST)
    assert False is data["is_endlist"]


def test_should_parse_ALLOW_CACHE():
    data = m3u8.parse(playlists.PLAYLIST_WITH_ENCRYPTED_SEGMENTS_AND_IV)
    assert "no" == data["allow_cache"]


def test_should_parse_VERSION():
    data = m3u8.parse(playlists.PLAYLIST_WITH_ENCRYPTED_SEGMENTS_AND_IV)
    assert 2 == data["version"]


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
        True,  # EXT-X-CUE-OUT
        True,
        True,
        True,
        True,
        True,
        False,  # EXT-X-CUE-IN
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
        "/DAlAAAENOOQAP/wFAUBAABrf+//N25XDf4B9p/gAAEBAQAAxKni9A=="
        == data["segments"][3]["scte35"]
    )
    assert "366" == data["segments"][3]["scte35_duration"]
    assert data["segments"][4]["cue_out"]
    assert (
        "/DAlAAAENOOQAP/wFAUBAABrf+//N25XDf4B9p/gAAEBAQAAxKni9A=="
        == data["segments"][4]["scte35"]
    )
    assert (
        "/DAlAAAENOOQAP/wFAUBAABrf+//N25XDf4B9p/gAAEBAQAAxKni9A=="
        == data["segments"][5]["scte35"]
    )


def test_should_parse_no_duration_cue_playlist():
    data = m3u8.parse(playlists.CUE_OUT_NO_DURATION_PLAYLIST)
    assert data["segments"][0]["cue_out_start"]
    assert data["segments"][2]["cue_in"]


def test_parse_simple_playlist_messy():
    data = m3u8.parse(playlists.SIMPLE_PLAYLIST_MESSY)
    assert 5220 == data["targetduration"]
    assert 0 == data["media_sequence"]
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
    assert 5220 == data["targetduration"]
    assert 0 == data["media_sequence"]
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
    assert "base_uri/" == media.base_uri


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
    assert 5220 == data["targetduration"]
    assert 0 == data["media_sequence"]
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
    expected = "http://str00.iptv.domain/7331/mpegts?token=longtokenhere"
    assert actual == expected


def test_master_playlist_with_frame_rate():
    data = m3u8.parse(playlists.VARIANT_PLAYLIST_WITH_FRAME_RATE)
    playlists_list = list(data["playlists"])
    assert 25 == playlists_list[0]["stream_info"]["frame_rate"]
    assert 50 == playlists_list[1]["stream_info"]["frame_rate"]
    assert 60 == playlists_list[2]["stream_info"]["frame_rate"]
    assert 12.5 == playlists_list[3]["stream_info"]["frame_rate"]


def test_master_playlist_with_unrounded_frame_rate():
    data = m3u8.parse(playlists.VARIANT_PLAYLIST_WITH_ROUNDABLE_FRAME_RATE)
    playlists_list = list(data["playlists"])
    assert 12.54321 == playlists_list[0]["stream_info"]["frame_rate"]


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

    assert 4 == len(iframe_playlists)

    assert 151288 == iframe_playlists[0]["iframe_stream_info"]["bandwidth"]
    # Check for absence of average_bandwidth if not given in the playlist
    assert "average_bandwidth" not in iframe_playlists[0]["iframe_stream_info"]
    assert "624x352" == iframe_playlists[0]["iframe_stream_info"]["resolution"]
    assert "avc1.4d001f" == iframe_playlists[0]["iframe_stream_info"]["codecs"]
    assert "video-800k-iframes.m3u8" == iframe_playlists[0]["uri"]

    assert 38775 == iframe_playlists[-1]["iframe_stream_info"]["bandwidth"]
    assert "avc1.4d001f" == (iframe_playlists[-1]["iframe_stream_info"]["codecs"])
    assert "video-150k-iframes.m3u8" == iframe_playlists[-1]["uri"]
    assert 155000 == iframe_playlists[1]["iframe_stream_info"]["average_bandwidth"]
    assert 65000 == iframe_playlists[2]["iframe_stream_info"]["average_bandwidth"]
    assert 30000 == iframe_playlists[3]["iframe_stream_info"]["average_bandwidth"]


def test_should_parse_variant_playlist_with_iframe_with_video_range():
    data = m3u8.parse(playlists.VARIANT_PLAYLIST_WITH_IFRAME_VIDEO_RANGE)
    iframe_playlists = list(data["iframe_playlists"])

    assert True is data["is_variant"]

    assert 4 == len(iframe_playlists)

    assert "http://example.com/sdr-iframes.m3u8" == iframe_playlists[0]["uri"]
    assert "SDR" == iframe_playlists[0]["iframe_stream_info"]["video_range"]
    assert "http://example.com/hdr-pq-iframes.m3u8" == iframe_playlists[1]["uri"]
    assert "PQ" == iframe_playlists[1]["iframe_stream_info"]["video_range"]
    assert "http://example.com/hdr-hlg-iframes.m3u8" == iframe_playlists[2]["uri"]
    assert "HLG" == iframe_playlists[2]["iframe_stream_info"]["video_range"]
    assert "http://example.com/unknown-iframes.m3u8" == iframe_playlists[3]["uri"]
    assert "video_range" not in iframe_playlists[3]["iframe_stream_info"]


def test_should_parse_variant_playlist_with_iframe_with_hdcp_level():
    data = m3u8.parse(playlists.VARIANT_PLAYLIST_WITH_IFRAME_HDCP_LEVEL)
    iframe_playlists = list(data["iframe_playlists"])

    assert True is data["is_variant"]

    assert 4 == len(iframe_playlists)

    assert "http://example.com/none-iframes.m3u8" == iframe_playlists[0]["uri"]
    assert "NONE" == iframe_playlists[0]["iframe_stream_info"]["hdcp_level"]
    assert "http://example.com/type0-iframes.m3u8" == iframe_playlists[1]["uri"]
    assert "TYPE-0" == iframe_playlists[1]["iframe_stream_info"]["hdcp_level"]
    assert "http://example.com/type1-iframes.m3u8" == iframe_playlists[2]["uri"]
    assert "TYPE-1" == iframe_playlists[2]["iframe_stream_info"]["hdcp_level"]
    assert "http://example.com/unknown-iframes.m3u8" == iframe_playlists[3]["uri"]
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


def test_req_video_layout():
    data = m3u8.parse(playlists.VARIANT_PLAYLIST_WITH_REQ_VIDEO_LAYOUT)
    assert data["playlists"][0]["stream_info"]["req_video_layout"] == '"CH-STEREO"'
