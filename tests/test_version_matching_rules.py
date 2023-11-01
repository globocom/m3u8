from m3u8.version_matching_rules import (
    valid_EXT_X_BYTERANGE_or_EXT_X_I_FRAMES_ONLY,
    valid_floating_point_EXTINF,
    valid_iv_in_EXT_X_KEY,
)


def test_invalid_iv_in_EXT_X_KEY():
    result = valid_iv_in_EXT_X_KEY(
        "#EXT-X-KEY: METHOD=AES-128, IV=0x123456789ABCDEF0123456789ABCDEF0, URI=https://example.com/key.bin",
        1,
    )
    assert result == False


def test_valid_iv_in_EXT_X_KEY():
    result = valid_iv_in_EXT_X_KEY(
        "#EXT-X-KEY: METHOD=AES-128, URI=https://example.com/key.bin", 1
    )
    assert result == True
    result = valid_iv_in_EXT_X_KEY(
        "#EXT-X-KEY: METHOD=AES-128, IV=0x123456789ABCDEF0123456789ABCDEF0, URI=https://example.com/key.bin",
        2,
    )
    assert result == True
    result = valid_iv_in_EXT_X_KEY(
        "#EXT-X-KEY: METHOD=AES-128, IV=0x123456789ABCDEF0123456789ABCDEF0, URI=https://example.com/key.bin",
        3,
    )
    assert result == True


def test_invalid_floating_point_EXTINF():
    result = valid_floating_point_EXTINF("#EXTINF: 10.5,", 2)
    assert result == False
    result = valid_floating_point_EXTINF("#EXTINF: A,", 3)
    assert result == False


def test_valid_floating_point_EXTINF():
    result = valid_floating_point_EXTINF("#EXTINF: 10,", 2)
    assert result == True
    result = valid_floating_point_EXTINF("#EXTINF: 10.5,", 3)
    assert result == True
    result = valid_floating_point_EXTINF("#EXTINF: 10.5,", 4)
    assert result == True


def test_invalid_EXT_X_BYTERANGE_or_EXT_X_I_FRAMES_ONLY():
    result = valid_EXT_X_BYTERANGE_or_EXT_X_I_FRAMES_ONLY(
        "#EXT-X-BYTERANGE: 200000@1000", 3
    )
    assert result == False
    result = valid_EXT_X_BYTERANGE_or_EXT_X_I_FRAMES_ONLY("#EXT-X-I-FRAMES-ONLY", 3)
    assert result == False


def test_valid_EXT_X_BYTERANGE_or_EXT_X_I_FRAMES_ONLY():
    result = valid_EXT_X_BYTERANGE_or_EXT_X_I_FRAMES_ONLY(
        "#EXT-X-BYTERANGE: 200000@1000", 4
    )
    assert result == True
    result = valid_EXT_X_BYTERANGE_or_EXT_X_I_FRAMES_ONLY("#EXT-X-I-FRAMES-ONLY", 4)
    assert result == True
    result = valid_EXT_X_BYTERANGE_or_EXT_X_I_FRAMES_ONLY(
        "#EXT-X-BYTERANGE: 200000@1000", 5
    )
    assert result == True
    result = valid_EXT_X_BYTERANGE_or_EXT_X_I_FRAMES_ONLY("#EXT-X-I-FRAMES-ONLY", 5)
    assert result == True
