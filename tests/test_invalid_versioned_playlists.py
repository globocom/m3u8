# coding: utf-8
# Copyright 2014 Globo.com Player authors. All rights reserved.
# Use of this source code is governed by a MIT License
# license that can be found in the LICENSE file.

import invalid_versioned_playlists
import pytest

import m3u8


@pytest.mark.xfail
def test_should_fail_if_iv_in_EXT_X_KEY_and_version_less_than_2():
    m3u8.parse(invalid_versioned_playlists.M3U8_RULE_IV)


@pytest.mark.xfail
def test_should_fail_if_floating_point_EXTINF_and_version_less_than_3():
    m3u8.parse(invalid_versioned_playlists.M3U8_RULE_FLOATING_POINT)


@pytest.mark.xfail
def test_should_fail_if_EXT_X_BYTERANGE_or_EXT_X_I_FRAMES_ONLY_and_version_less_than_4():
    m3u8.parse(invalid_versioned_playlists.M3U8_RULE_BYTE_RANGE)
