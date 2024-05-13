from m3u8.version_matching_rules import (
    ValidEXTXBYTERANGEOrEXTXIFRAMESONLY,
    ValidFloatingPointEXTINF,
    ValidIVInEXTXKEY,
)


def test_invalid_iv_in_EXT_X_KEY():
    validator = ValidIVInEXTXKEY(
        version=1,
        line_number=1,
        line="#EXT-X-KEY: METHOD=AES-128, IV=0x123456789ABCDEF0123456789ABCDEF0, URI=https://example.com/key.bin",
    )

    assert not validator.validate()


def test_valid_iv_in_EXT_X_KEY():
    examples = [
        {
            "line": "#EXT-X-KEY: METHOD=AES-128, URI=https://example.com/key.bin",
            "version": 1,
            "expected": True,
        },
        {
            "line": "#EXT-X-KEY: METHOD=AES-128, IV=0x123456789ABCDEF0123456789ABCDEF0, URI=https://example.com/key.bin",
            "version": 2,
            "expected": True,
        },
        {
            "line": "#EXT-X-KEY: METHOD=AES-128, IV=0x123456789ABCDEF0123456789ABCDEF0, URI=https://example.com/key.bin",
            "version": 3,
            "expected": True,
        },
        # Invalid case
        {
            "line": "#EXT-X-KEY: METHOD=AES-128, IV=0x123456789ABCDEF0123456789ABCDEF0, URI=https://example.com/key.bin",
            "version": 1,
            "expected": False,
        },
    ]

    for example in examples:
        validator = ValidIVInEXTXKEY(
            version=example["version"],
            line_number=1,
            line=example["line"],
        )
        assert validator.validate() == example["expected"]


def test_invalid_floating_point_EXTINF():
    examples = [
        {
            "line": "#EXTINF: 10.5,",
            "version": 2,
        },
        {
            "line": "#EXTINF: A,",
            "version": 3,
        },
    ]

    for example in examples:
        validator = ValidFloatingPointEXTINF(
            version=example["version"],
            line_number=1,
            line=example["line"],
        )
        assert not validator.validate()


def test_valid_floating_point_EXTINF():
    examples = [
        {
            "line": "#EXTINF: 10,",
            "version": 2,
        },
        {
            "line": "#EXTINF: 10.5,",
            "version": 3,
        },
        {
            "line": "#EXTINF: 10.5,",
            "version": 4,
        },
    ]

    for example in examples:
        validator = ValidFloatingPointEXTINF(
            version=example["version"],
            line_number=1,
            line=example["line"],
        )
        assert validator.validate()


def test_invalid_EXT_X_BYTERANGE_or_EXT_X_I_FRAMES_ONLY():
    examples = [
        {
            "line": "#EXT-X-BYTERANGE: 200000@1000",
            "version": 3,
        },
        {
            "line": "#EXT-X-I-FRAMES-ONLY",
            "version": 3,
        },
    ]

    for example in examples:
        validator = ValidEXTXBYTERANGEOrEXTXIFRAMESONLY(
            version=example["version"],
            line_number=1,
            line=example["line"],
        )
        assert not validator.validate()


def test_valid_EXT_X_BYTERANGE_or_EXT_X_I_FRAMES_ONLY():
    examples = [
        {
            "line": "#EXT-X-BYTERANGE: 200000@1000",
            "version": 4,
        },
        {
            "line": "#EXT-X-I-FRAMES-ONLY",
            "version": 4,
        },
        {
            "line": "#EXT-X-BYTERANGE: 200000@1000",
            "version": 5,
        },
        {
            "line": "#EXT-X-I-FRAMES-ONLY",
            "version": 5,
        },
    ]

    for example in examples:
        validator = ValidEXTXBYTERANGEOrEXTXIFRAMESONLY(
            version=example["version"],
            line_number=1,
            line=example["line"],
        )
        assert validator.validate()
