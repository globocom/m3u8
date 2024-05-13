import invalid_versioned_playlists
import pytest

import m3u8


def test_should_fail_if_iv_in_EXT_X_KEY_and_version_less_than_2():
    with pytest.raises(Exception) as exc_info:
        m3u8.parse(invalid_versioned_playlists.M3U8_RULE_IV, strict=True)

    assert "Change the protocol version to 2 or higher." in str(exc_info.value)


def test_should_fail_if_floating_point_EXTINF_and_version_less_than_3():
    with pytest.raises(Exception) as exc_info:
        m3u8.parse(invalid_versioned_playlists.M3U8_RULE_FLOATING_POINT, strict=True)

    assert "Change the protocol version to 3 or higher." in str(exc_info.value)


def test_should_fail_if_EXT_X_BYTERANGE_or_EXT_X_I_FRAMES_ONLY_and_version_less_than_4():
    with pytest.raises(Exception) as exc_info:
        m3u8.parse(invalid_versioned_playlists.M3U8_RULE_BYTE_RANGE, strict=True)

    assert "Change the protocol version to 4 or higher." in str(exc_info.value)
