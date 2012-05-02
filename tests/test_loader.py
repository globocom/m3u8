import m3u8
from playlists import *

def test_loads_should_create_m3u8_object_from_string():
    m3u8_obj = m3u8.loads(SIMPLE_PLAYLIST)
    assert 5220 == m3u8_obj.target_duration
