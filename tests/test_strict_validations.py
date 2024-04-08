# Copyright 2014 Globo.com Player authors. All rights reserved.
# Use of this source code is governed by a MIT License
# license that can be found in the LICENSE file.

import invalid_versioned_playlists
import pytest

import m3u8
import m3u8.version_matching_rules


@pytest.mark.xfail
def test_should_fail_if_first_line_not_EXTM3U():
    assert 0


@pytest.mark.xfail
def test_should_fail_if_expected_ts_segment_line_is_not_valid():
    assert 0


@pytest.mark.xfail
def test_should_fail_if_EXT_X_MEDIA_SEQUENCE_is_diffent_from_sequence_number_of_first_uri():
    assert 0


@pytest.mark.xfail
def test_should_fail_if_more_than_one_EXT_X_MEDIA_SEQUENCE():
    assert 0


@pytest.mark.xfail
def test_should_fail_if_EXT_X_MEDIA_SEQUENCE_is_not_a_number():
    assert 0


def test_should_validate_supported_EXT_X_VERSION():
    with pytest.raises(
        Exception,
    ):
        m3u8.parse(invalid_versioned_playlists.M3U8_RULE_IV, strict=True)


@pytest.mark.xfail
def test_should_fail_if_any_EXTINF_duration_is_greater_than_TARGET_DURATION():
    assert 0


@pytest.mark.xfail
def test_should_fail_if_TARGET_DURATION_not_found():
    assert 0


@pytest.mark.xfail
def test_should_fail_if_invalid_m3u8_url_after_EXT_X_STREAM_INF():
    assert 0
