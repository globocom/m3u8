import m3u8
from playlists import *

def test_should_parse_simple_playlist_from_string():
    data = m3u8.parse(SIMPLE_PLAYLIST)
    assert 5220 == data['targetduration']
    assert ['http://media.example.com/entire.ts'] == [c['uri'] for c in data['segments']]
    assert [5220] == [c['duration'] for c in data['segments']]

def test_should_parse_simple_playlist_from_string_with_different_linebreaks():
    data = m3u8.parse(SIMPLE_PLAYLIST.replace('\n', '\r\n'))
    assert 5220 == data['targetduration']
    assert ['http://media.example.com/entire.ts'] == [c['uri'] for c in data['segments']]
    assert [5220] == [c['duration'] for c in data['segments']]

def test_should_parse_sliding_window_playlist_from_string():
    data = m3u8.parse(SLIDING_WINDOW_PLAYLIST)
    assert 8 == data['targetduration']
    assert 2680 == data['media_sequence']
    assert ['https://priv.example.com/fileSequence2680.ts',
            'https://priv.example.com/fileSequence2681.ts',
            'https://priv.example.com/fileSequence2682.ts'] == [c['uri'] for c in data['segments']]
    assert [8, 8, 8] == [c['duration'] for c in data['segments']]

def test_should_parse_playlist_with_encripted_segments_from_string():
    data = m3u8.parse(PLAYLIST_WITH_ENCRIPTED_SEGMENTS)
    assert 7794 == data['media_sequence']
    assert 15 == data['targetduration']
    assert 'AES-128' == data['key']['method']
    assert 'https://priv.example.com/key.php?r=52' == data['key']['uri']
    assert ['http://media.example.com/fileSequence52-1.ts',
            'http://media.example.com/fileSequence52-2.ts',
            'http://media.example.com/fileSequence52-3.ts'] == [c['uri'] for c in data['segments']]
    assert [15, 15, 15] == [c['duration'] for c in data['segments']]

def test_should_load_playlist_with_iv_from_string():
    data = m3u8.parse(PLAYLIST_WITH_ENCRIPTED_SEGMENTS_AND_IV)
    assert "/hls-key/tvglobokey.bin" == data['key']['uri']
    assert "AES-128" == data['key']['method']
    assert "0X10ef8f758ca555115584bb5b3c687f52" == data['key']['iv']

def test_should_parse_title_from_playlist():
    data = m3u8.parse(SIMPLE_PLAYLIST_WITH_TITLE)
    assert 1 == len(data['segments'])
    assert 5220 == data['segments'][0]['duration']
    assert "A sample title" == data['segments'][0]['title']
    assert "http://media.example.com/entire.ts" == data['segments'][0]['uri']

def test_should_parse_variant_playlist():
    data = m3u8.parse(VARIANT_PLAYLIST)
    playlists = list(data['playlists'])

    assert True == data['is_variant']
    assert 4 == len(playlists)

    assert 'http://example.com/low.m3u8' == playlists[0]['resource']
    assert '1' == playlists[0]['stream_info']['program_id']
    assert '1280000' == playlists[0]['stream_info']['bandwidth']

    assert 'http://example.com/audio-only.m3u8' == playlists[-1]['resource']
    assert '1' == playlists[-1]['stream_info']['program_id']
    assert '65000' == playlists[-1]['stream_info']['bandwidth']
    assert 'mp4a.40.5' == playlists[-1]['stream_info']['codecs']
