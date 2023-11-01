from m3u8 import protocol


# You must use at least protocol version 2 if you have IV in EXT-X-KEY.
def valid_iv_in_EXT_X_KEY(line: str, version: float):
    if not protocol.ext_x_key in line:
        return True

    if "IV" in line:
        return version >= 2

    return True


# You must use at least protocol version 3 if you have floating point EXTINF duration values.
def valid_floating_point_EXTINF(line: str, version: float):
    if not protocol.extinf in line:
        return True

    chunks = line.replace(protocol.extinf + ":", "").split(",", 1)
    duration = chunks[0]

    def is_floating_number(value: str):
        try:
            float_value = float(value)
            return "." in value and float_value != int(float_value)
        except ValueError:
            return False

    if is_floating_number(duration):
        return version >= 3

    return True


# You must use at least protocol version 4 if you have EXT-X-BYTERANGE or EXT-X-IFRAME-ONLY.
def valid_EXT_X_BYTERANGE_or_EXT_X_IFRAME_ONLY(line: str, version: float):
    if not protocol.ext_x_byterange in line and not protocol.ext_i_frames_only in line:
        return True

    return version >= 4
