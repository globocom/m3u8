from typing import Callable, List

from m3u8 import protocol
from m3u8.version_matching_rules import *


class VersionMatchingError(Exception):
    def __init__(self, lineno, line):
        self.lineno = lineno
        self.line = line

    def __str__(self):
        return f"Version matching error at line {self.lineno}: {self.line}"


def get_version(file_lines: List[str]):
    for line in file_lines:
        if line.startswith(protocol.ext_x_version):
            version = line.split(":")[1]
            return float(version)

    return None


def valid_in_all_rules(line_number: int, line: str, version: float):
    rules: List[Callable[[str, float], bool]] = [
        valid_iv_in_EXT_X_KEY,
        valid_floating_point_EXTINF,
        valid_EXT_X_BYTERANGE_or_EXT_X_I_FRAMES_ONLY,
    ]

    for rule in rules:
        if not rule(line, version):
            raise VersionMatchingError(line_number, line)


def validate(file_lines: List[str]):
    found_version = get_version(file_lines)
    if found_version is None:
        return

    for number, line in enumerate(file_lines):
        valid_in_all_rules(number, line, found_version)
