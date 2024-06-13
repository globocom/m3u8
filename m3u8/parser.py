# Copyright 2014 Globo.com Player authors. All rights reserved.
# Use of this source code is governed by a MIT License
# license that can be found in the LICENSE file.

import itertools
import re
from datetime import datetime, timedelta

try:
    from backports.datetime_fromisoformat import MonkeyPatch

    MonkeyPatch.patch_fromisoformat()
except ImportError:
    pass


from m3u8 import protocol, version_matching

"""
http://tools.ietf.org/html/draft-pantos-http-live-streaming-08#section-3.2
http://stackoverflow.com/questions/2785755/how-to-split-but-ignore-separators-in-quoted-strings-in-python
"""
ATTRIBUTELISTPATTERN = re.compile(r"""((?:[^,"']|"[^"]*"|'[^']*')+)""")


def cast_date_time(value):
    return datetime.fromisoformat(value)


def format_date_time(value, **kwargs):
    return value.isoformat(**kwargs)


class ParseError(Exception):
    def __init__(self, lineno, line):
        self.lineno = lineno
        self.line = line

    def __str__(self):
        return "Syntax error in manifest on line %d: %s" % (self.lineno, self.line)


def parse(content, strict=False, custom_tags_parser=None):
    """
    Given a M3U8 playlist content returns a dictionary with all data found
    """
    data = {
        "media_sequence": 0,
        "is_variant": False,
        "is_endlist": False,
        "is_i_frames_only": False,
        "is_independent_segments": False,
        "is_images_only": False,
        "playlist_type": None,
        "playlists": [],
        "segments": [],
        "iframe_playlists": [],
        "image_playlists": [],
        "tiles": [],
        "media": [],
        "keys": [],
        "rendition_reports": [],
        "skip": {},
        "part_inf": {},
        "session_data": [],
        "session_keys": [],
        "segment_map": [],
    }

    state = {
        "expect_segment": False,
        "expect_playlist": False,
        "current_key": None,
        "current_segment_map": None,
    }

    lines = string_to_lines(content)
    if strict:
        found_errors = version_matching.validate(lines)

        if len(found_errors) > 0:
            raise Exception(found_errors)

    lineno = 0
    for line in lines:
        lineno += 1
        line = line.strip()

        # Call custom parser if needed
        if line.startswith("#") and callable(custom_tags_parser):
            go_to_next_line = custom_tags_parser(line, lineno, data, state)

            # Do not try to parse other standard tags on this line if custom_tags_parser function returns 'True'
            if go_to_next_line:
                continue

        if line.startswith(protocol.ext_x_byterange):
            _parse_byterange(line, state)
            state["expect_segment"] = True
            continue

        if line.startswith(protocol.ext_x_bitrate):
            _parse_bitrate(line, state)

        elif line.startswith(protocol.ext_x_targetduration):
            _parse_simple_parameter(line, data, float)

        elif line.startswith(protocol.ext_x_media_sequence):
            _parse_simple_parameter(line, data, int)

        elif line.startswith(protocol.ext_x_discontinuity_sequence):
            _parse_simple_parameter(line, data, int)

        elif line.startswith(protocol.ext_x_program_date_time):
            _, program_date_time = _parse_simple_parameter_raw_value(
                line, cast_date_time
            )
            if not data.get("program_date_time"):
                data["program_date_time"] = program_date_time
            state["current_program_date_time"] = program_date_time
            state["program_date_time"] = program_date_time

        elif line.startswith(protocol.ext_x_discontinuity):
            state["discontinuity"] = True

        elif line.startswith(protocol.ext_x_cue_out_cont):
            _parse_cueout_cont(line, state)
            state["cue_out"] = True

        elif line.startswith(protocol.ext_x_cue_out):
            _parse_cueout(line, state)
            state["cue_out_start"] = True
            state["cue_out"] = True
            if "DURATION" in line.upper():
                state["cue_out_explicitly_duration"] = True

        elif line.startswith(f"{protocol.ext_oatcls_scte35}:"):
            _parse_oatcls_scte35(line, state)

        elif line.startswith(f"{protocol.ext_x_asset}:"):
            _parse_asset(line, state)

        elif line.startswith(protocol.ext_x_cue_in):
            state["cue_in"] = True

        elif line.startswith(protocol.ext_x_cue_span):
            state["cue_out"] = True

        elif line.startswith(protocol.ext_x_version):
            _parse_simple_parameter(line, data, int)

        elif line.startswith(protocol.ext_x_allow_cache):
            _parse_simple_parameter(line, data)

        elif line.startswith(protocol.ext_x_key):
            key = _parse_key(line)
            state["current_key"] = key
            if key not in data["keys"]:
                data["keys"].append(key)

        elif line.startswith(protocol.extinf):
            _parse_extinf(line, data, state, lineno, strict)
            state["expect_segment"] = True

        elif line.startswith(protocol.ext_x_stream_inf):
            state["expect_playlist"] = True
            _parse_stream_inf(line, data, state)

        elif line.startswith(protocol.ext_x_i_frame_stream_inf):
            _parse_i_frame_stream_inf(line, data)

        elif line.startswith(protocol.ext_x_media):
            _parse_media(line, data, state)

        elif line.startswith(protocol.ext_x_playlist_type):
            _parse_simple_parameter(line, data)

        elif line.startswith(protocol.ext_i_frames_only):
            data["is_i_frames_only"] = True

        elif line.startswith(protocol.ext_is_independent_segments):
            data["is_independent_segments"] = True

        elif line.startswith(protocol.ext_x_endlist):
            data["is_endlist"] = True

        elif line.startswith(protocol.ext_x_map):
            quoted_parser = remove_quotes_parser("uri", "byterange")
            segment_map_info = _parse_attribute_list(
                protocol.ext_x_map, line, quoted_parser
            )
            state["current_segment_map"] = segment_map_info
            data["segment_map"].append(segment_map_info)

        elif line.startswith(protocol.ext_x_start):
            attribute_parser = {"time_offset": lambda x: float(x)}
            start_info = _parse_attribute_list(
                protocol.ext_x_start, line, attribute_parser
            )
            data["start"] = start_info

        elif line.startswith(protocol.ext_x_server_control):
            _parse_server_control(line, data, state)

        elif line.startswith(protocol.ext_x_part_inf):
            _parse_part_inf(line, data, state)

        elif line.startswith(protocol.ext_x_rendition_report):
            _parse_rendition_report(line, data, state)

        elif line.startswith(protocol.ext_x_part):
            _parse_part(line, data, state)

        elif line.startswith(protocol.ext_x_skip):
            _parse_skip(line, data, state)

        elif line.startswith(protocol.ext_x_session_data):
            _parse_session_data(line, data, state)

        elif line.startswith(protocol.ext_x_session_key):
            _parse_session_key(line, data, state)

        elif line.startswith(protocol.ext_x_preload_hint):
            _parse_preload_hint(line, data, state)

        elif line.startswith(protocol.ext_x_daterange):
            _parse_daterange(line, data, state)

        elif line.startswith(protocol.ext_x_gap):
            state["gap"] = True

        elif line.startswith(protocol.ext_x_content_steering):
            _parse_content_steering(line, data, state)

        elif line.startswith(protocol.ext_x_image_stream_inf):
            _parse_image_stream_inf(line, data)

        elif line.startswith(protocol.ext_x_images_only):
            data["is_images_only"] = True

        elif line.startswith(protocol.ext_x_tiles):
            _parse_tiles(line, data, state)

        elif line.startswith(protocol.ext_m3u):
            # We don't parse #EXTM3U, it just should to be present
            pass

        elif line.strip() == "":
            # blank lines are legal
            pass

        elif (not line.startswith("#")) and (state["expect_segment"]):
            _parse_ts_chunk(line, data, state)
            state["expect_segment"] = False

        elif (not line.startswith("#")) and (state["expect_playlist"]):
            _parse_variant_playlist(line, data, state)
            state["expect_playlist"] = False

        elif strict:
            raise ParseError(lineno, line)

    # there could be remaining partial segments
    if "segment" in state:
        data["segments"].append(state.pop("segment"))

    return data


def _parse_key(line):
    params = ATTRIBUTELISTPATTERN.split(line.replace(protocol.ext_x_key + ":", ""))[
        1::2
    ]
    key = {}
    for param in params:
        name, value = param.split("=", 1)
        key[normalize_attribute(name)] = remove_quotes(value)
    return key


def _parse_extinf(line, data, state, lineno, strict):
    chunks = line.replace(protocol.extinf + ":", "").split(",", 1)
    if len(chunks) == 2:
        duration, title = chunks
    elif len(chunks) == 1:
        if strict:
            raise ParseError(lineno, line)
        else:
            duration = chunks[0]
            title = ""
    if "segment" not in state:
        state["segment"] = {}
    state["segment"]["duration"] = float(duration)
    state["segment"]["title"] = title


def _parse_ts_chunk(line, data, state):
    segment = state.pop("segment")
    if state.get("program_date_time"):
        segment["program_date_time"] = state.pop("program_date_time")
    if state.get("current_program_date_time"):
        segment["current_program_date_time"] = state["current_program_date_time"]
        state["current_program_date_time"] += timedelta(seconds=segment["duration"])
    segment["uri"] = line
    segment["cue_in"] = state.pop("cue_in", False)
    segment["cue_out"] = state.pop("cue_out", False)
    segment["cue_out_start"] = state.pop("cue_out_start", False)
    segment["cue_out_explicitly_duration"] = state.pop(
        "cue_out_explicitly_duration", False
    )

    scte_op = state.get if segment["cue_out"] else state.pop
    segment["scte35"] = scte_op("current_cue_out_scte35", None)
    segment["oatcls_scte35"] = scte_op("current_cue_out_oatcls_scte35", None)
    segment["scte35_duration"] = scte_op("current_cue_out_duration", None)
    segment["scte35_elapsedtime"] = scte_op("current_cue_out_elapsedtime", None)
    segment["asset_metadata"] = scte_op("asset_metadata", None)

    segment["discontinuity"] = state.pop("discontinuity", False)
    if state.get("current_key"):
        segment["key"] = state["current_key"]
    else:
        # For unencrypted segments, the initial key would be None
        if None not in data["keys"]:
            data["keys"].append(None)
    if state.get("current_segment_map"):
        segment["init_section"] = state["current_segment_map"]
    segment["dateranges"] = state.pop("dateranges", None)
    segment["gap_tag"] = state.pop("gap", None)
    data["segments"].append(segment)


def _parse_attribute_list(prefix, line, attribute_parser, default_parser=None):
    params = ATTRIBUTELISTPATTERN.split(line.replace(prefix + ":", ""))[1::2]

    attributes = {}
    for param in params:
        name, value = param.split("=", 1)
        name = normalize_attribute(name)

        if name in attribute_parser:
            value = attribute_parser[name](value)
        elif default_parser is not None:
            value = default_parser(value)

        attributes[name] = value

    return attributes


def _parse_stream_inf(line, data, state):
    data["is_variant"] = True
    data["media_sequence"] = None
    attribute_parser = remove_quotes_parser(
        "codecs",
        "audio",
        "video",
        "video_range",
        "subtitles",
        "pathway_id",
        "stable_variant_id",
    )
    attribute_parser["program_id"] = int
    attribute_parser["bandwidth"] = lambda x: int(float(x))
    attribute_parser["average_bandwidth"] = int
    attribute_parser["frame_rate"] = float
    attribute_parser["video_range"] = str
    attribute_parser["hdcp_level"] = str
    state["stream_info"] = _parse_attribute_list(
        protocol.ext_x_stream_inf, line, attribute_parser
    )


def _parse_i_frame_stream_inf(line, data):
    attribute_parser = remove_quotes_parser(
        "codecs", "uri", "pathway_id", "stable_variant_id"
    )
    attribute_parser["program_id"] = int
    attribute_parser["bandwidth"] = int
    attribute_parser["average_bandwidth"] = int
    attribute_parser["video_range"] = str
    attribute_parser["hdcp_level"] = str
    iframe_stream_info = _parse_attribute_list(
        protocol.ext_x_i_frame_stream_inf, line, attribute_parser
    )
    iframe_playlist = {
        "uri": iframe_stream_info.pop("uri"),
        "iframe_stream_info": iframe_stream_info,
    }

    data["iframe_playlists"].append(iframe_playlist)


def _parse_image_stream_inf(line, data):
    attribute_parser = remove_quotes_parser(
        "codecs", "uri", "pathway_id", "stable_variant_id"
    )
    attribute_parser["program_id"] = int
    attribute_parser["bandwidth"] = int
    attribute_parser["average_bandwidth"] = int
    attribute_parser["resolution"] = str
    image_stream_info = _parse_attribute_list(
        protocol.ext_x_image_stream_inf, line, attribute_parser
    )
    image_playlist = {
        "uri": image_stream_info.pop("uri"),
        "image_stream_info": image_stream_info,
    }

    data["image_playlists"].append(image_playlist)


def _parse_tiles(line, data, state):
    attribute_parser = remove_quotes_parser("uri")
    attribute_parser["resolution"] = str
    attribute_parser["layout"] = str
    attribute_parser["duration"] = float
    tiles_info = _parse_attribute_list(protocol.ext_x_tiles, line, attribute_parser)
    data["tiles"].append(tiles_info)


def _parse_media(line, data, state):
    quoted = remove_quotes_parser(
        "uri",
        "group_id",
        "language",
        "assoc_language",
        "name",
        "instream_id",
        "characteristics",
        "channels",
        "stable_rendition_id",
        "thumbnails",
        "image",
    )
    media = _parse_attribute_list(protocol.ext_x_media, line, quoted)
    data["media"].append(media)


def _parse_variant_playlist(line, data, state):
    playlist = {"uri": line, "stream_info": state.pop("stream_info")}

    data["playlists"].append(playlist)


def _parse_bitrate(line, state):
    if "segment" not in state:
        state["segment"] = {}
    state["segment"]["bitrate"] = line.replace(protocol.ext_x_bitrate + ":", "")


def _parse_byterange(line, state):
    if "segment" not in state:
        state["segment"] = {}
    state["segment"]["byterange"] = line.replace(protocol.ext_x_byterange + ":", "")


def _parse_simple_parameter_raw_value(line, cast_to=str, normalize=False):
    param, value = line.split(":", 1)
    param = normalize_attribute(param.replace("#EXT-X-", ""))
    if normalize:
        value = value.strip().lower()
    return param, cast_to(value)


def _parse_and_set_simple_parameter_raw_value(line, data, cast_to=str, normalize=False):
    param, value = _parse_simple_parameter_raw_value(line, cast_to, normalize)
    data[param] = value
    return data[param]


def _parse_simple_parameter(line, data, cast_to=str):
    return _parse_and_set_simple_parameter_raw_value(line, data, cast_to, True)


def _parse_cueout_cont(line, state):
    elements = line.split(":", 1)
    if len(elements) != 2:
        return

    # EXT-X-CUE-OUT-CONT:2.436/120 style
    res = re.match(
        r"^[-+]?([0-9]+(\.[0-9]+)?|\.[0-9]+)/[-+]?([0-9]+(\.[0-9]+)?|\.[0-9]+)$",
        elements[1],
    )
    if res:
        state["current_cue_out_elapsedtime"] = res.group(1)
        state["current_cue_out_duration"] = res.group(3)
        return

    # EXT-X-CUE-OUT-CONT:ElapsedTime=10,Duration=60,SCTE35=... style
    cue_info = _parse_attribute_list(
        protocol.ext_x_cue_out_cont,
        line,
        remove_quotes_parser("duration", "elapsedtime", "scte35"),
    )

    duration = cue_info.get("duration")
    if duration:
        state["current_cue_out_duration"] = duration

    scte35 = cue_info.get("scte35")
    if duration:
        state["current_cue_out_scte35"] = scte35

    elapsedtime = cue_info.get("elapsedtime")
    if elapsedtime:
        state["current_cue_out_elapsedtime"] = elapsedtime


def _cueout_no_duration(line):
    # this needs to be called first since line.split in all other
    # parsers will throw a ValueError if passed just this tag
    if line == protocol.ext_x_cue_out:
        return (None, None)


def _cueout_envivio(line, state):
    param, value = line.split(":", 1)
    res = re.match('.*DURATION=(.*),.*,CUE="(.*)"', value)
    if res:
        return (res.group(2), res.group(1))
    else:
        return None


def _cueout_duration(line):
    # This was added separately rather than modifying "simple"
    param, value = line.split(":", 1)
    res = re.match(r"DURATION=(.*)", value)
    if res:
        return (None, res.group(1))


def _cueout_simple(line):
    param, value = line.split(":", 1)
    res = re.match(r"^(\d+(?:\.\d)?\d*)$", value)
    if res:
        return (None, res.group(1))


def _parse_cueout(line, state):
    _cueout_state = (
        _cueout_no_duration(line)
        or _cueout_envivio(line, state)
        or _cueout_duration(line)
        or _cueout_simple(line)
    )
    if _cueout_state:
        cue_out_scte35, cue_out_duration = _cueout_state
        current_cue_out_scte35 = state.get("current_cue_out_scte35")
        state["current_cue_out_scte35"] = cue_out_scte35 or current_cue_out_scte35
        state["current_cue_out_duration"] = cue_out_duration


def _parse_server_control(line, data, state):
    attribute_parser = {
        "can_block_reload": str,
        "hold_back": lambda x: float(x),
        "part_hold_back": lambda x: float(x),
        "can_skip_until": lambda x: float(x),
        "can_skip_dateranges": str,
    }

    data["server_control"] = _parse_attribute_list(
        protocol.ext_x_server_control, line, attribute_parser
    )


def _parse_part_inf(line, data, state):
    attribute_parser = {"part_target": lambda x: float(x)}

    data["part_inf"] = _parse_attribute_list(
        protocol.ext_x_part_inf, line, attribute_parser
    )


def _parse_rendition_report(line, data, state):
    attribute_parser = remove_quotes_parser("uri")
    attribute_parser["last_msn"] = int
    attribute_parser["last_part"] = int

    rendition_report = _parse_attribute_list(
        protocol.ext_x_rendition_report, line, attribute_parser
    )

    data["rendition_reports"].append(rendition_report)


def _parse_part(line, data, state):
    attribute_parser = remove_quotes_parser("uri")
    attribute_parser["duration"] = lambda x: float(x)
    attribute_parser["independent"] = str
    attribute_parser["gap"] = str
    attribute_parser["byterange"] = str

    part = _parse_attribute_list(protocol.ext_x_part, line, attribute_parser)

    # this should always be true according to spec
    if state.get("current_program_date_time"):
        part["program_date_time"] = state["current_program_date_time"]
        state["current_program_date_time"] += timedelta(seconds=part["duration"])

    part["dateranges"] = state.pop("dateranges", None)
    part["gap_tag"] = state.pop("gap", None)

    if "segment" not in state:
        state["segment"] = {}
    segment = state["segment"]
    if "parts" not in segment:
        segment["parts"] = []

    segment["parts"].append(part)


def _parse_skip(line, data, state):
    attribute_parser = remove_quotes_parser("recently_removed_dateranges")
    attribute_parser["skipped_segments"] = int

    data["skip"] = _parse_attribute_list(protocol.ext_x_skip, line, attribute_parser)


def _parse_session_data(line, data, state):
    quoted = remove_quotes_parser("data_id", "value", "uri", "language")
    session_data = _parse_attribute_list(protocol.ext_x_session_data, line, quoted)
    data["session_data"].append(session_data)


def _parse_session_key(line, data, state):
    params = ATTRIBUTELISTPATTERN.split(
        line.replace(protocol.ext_x_session_key + ":", "")
    )[1::2]
    key = {}
    for param in params:
        name, value = param.split("=", 1)
        key[normalize_attribute(name)] = remove_quotes(value)
    data["session_keys"].append(key)


def _parse_preload_hint(line, data, state):
    attribute_parser = remove_quotes_parser("uri")
    attribute_parser["type"] = str
    attribute_parser["byterange_start"] = int
    attribute_parser["byterange_length"] = int

    data["preload_hint"] = _parse_attribute_list(
        protocol.ext_x_preload_hint, line, attribute_parser
    )


def _parse_daterange(line, date, state):
    attribute_parser = remove_quotes_parser("id", "class", "start_date", "end_date")
    attribute_parser["duration"] = float
    attribute_parser["planned_duration"] = float
    attribute_parser["end_on_next"] = str
    attribute_parser["scte35_cmd"] = str
    attribute_parser["scte35_out"] = str
    attribute_parser["scte35_in"] = str

    parsed = _parse_attribute_list(protocol.ext_x_daterange, line, attribute_parser)

    if "dateranges" not in state:
        state["dateranges"] = []

    state["dateranges"].append(parsed)


def _parse_content_steering(line, data, state):
    attribute_parser = remove_quotes_parser("server_uri", "pathway_id")

    data["content_steering"] = _parse_attribute_list(
        protocol.ext_x_content_steering, line, attribute_parser
    )


def _parse_oatcls_scte35(line, state):
    scte35_cue = line.split(":", 1)[1]
    state["current_cue_out_oatcls_scte35"] = scte35_cue
    state["current_cue_out_scte35"] = scte35_cue


def _parse_asset(line, state):
    # EXT-X-ASSET attribute values may or may not be quoted, and need to be URL-encoded.
    # They are preserved as-is here to prevent loss of information.
    state["asset_metadata"] = _parse_attribute_list(
        protocol.ext_x_asset, line, {}, default_parser=str
    )


def string_to_lines(string):
    return string.strip().splitlines()


def remove_quotes_parser(*attrs):
    return dict(zip(attrs, itertools.repeat(remove_quotes)))


def remove_quotes(string):
    """
    Remove quotes from string.

    Ex.:
      "foo" -> foo
      'foo' -> foo
      'foo  -> 'foo

    """
    quotes = ('"', "'")
    if string.startswith(quotes) and string.endswith(quotes):
        return string[1:-1]
    return string


def normalize_attribute(attribute):
    return attribute.replace("-", "_").lower().strip()


def get_segment_custom_value(state, key, default=None):
    """
    Helper function for getting custom values for Segment
    Are useful with custom_tags_parser
    """
    if "segment" not in state:
        return default
    if "custom_parser_values" not in state["segment"]:
        return default
    return state["segment"]["custom_parser_values"].get(key, default)


def save_segment_custom_value(state, key, value):
    """
    Helper function for saving custom values for Segment
    Are useful with custom_tags_parser
    """
    if "segment" not in state:
        state["segment"] = {}

    if "custom_parser_values" not in state["segment"]:
        state["segment"]["custom_parser_values"] = {}

    state["segment"]["custom_parser_values"][key] = value
