import m3u8

SIMPLE_PLAYLIST = '''
#EXTM3U
#EXT-X-TARGETDURATION:5220
#EXTINF:5220,
http://media.example.com/entire.ts
#EXT-X-ENDLIST
'''

SLIDING_WINDOW_PLAYLIST = '''
#EXTM3U
#EXT-X-TARGETDURATION:8
#EXT-X-MEDIA-SEQUENCE:2680

#EXTINF:8,
https://priv.example.com/fileSequence2680.ts
#EXTINF:8,
https://priv.example.com/fileSequence2681.ts
#EXTINF:8,
https://priv.example.com/fileSequence2682.ts
'''

PLAYLIST_WITH_ENCRIPTED_SEGMENTS = '''
#EXTM3U
#EXT-X-MEDIA-SEQUENCE:7794
#EXT-X-TARGETDURATION:15

#EXT-X-KEY:METHOD=AES-128,URI="https://priv.example.com/key.php?r=52"

#EXTINF:15,
http://media.example.com/fileSequence52-1.ts
#EXTINF:15,
http://media.example.com/fileSequence52-2.ts
#EXTINF:15,
http://media.example.com/fileSequence52-3.ts
'''

PLAYLIST_WITH_ENCRIPTED_SEGMENTS_AND_IV = '''
#EXTM3U
#EXT-X-MEDIA-SEQUENCE:82400
#EXT-X-ALLOW-CACHE:NO
#EXT-X-VERSION:2
#EXT-X-KEY:METHOD=AES-128,URI="/hls-key/tvglobokey.bin",IV=0X10ef8f758ca555115584bb5b3c687f52
#EXT-X-TARGETDURATION:8
#EXTINF:8,
../../../../hls-live/streams/live_hls/events/tvglobo/tvglobo/globoNum82400.ts
#EXTINF:8,
../../../../hls-live/streams/live_hls/events/tvglobo/tvglobo/globoNum82401.ts
#EXTINF:8,
../../../../hls-live/streams/live_hls/events/tvglobo/tvglobo/globoNum82402.ts
#EXTINF:8,
../../../../hls-live/streams/live_hls/events/tvglobo/tvglobo/globoNum82403.ts
#EXTINF:8,
../../../../hls-live/streams/live_hls/events/tvglobo/tvglobo/globoNum82404.ts
#EXTINF:8,
../../../../hls-live/streams/live_hls/events/tvglobo/tvglobo/globoNum82405.ts
'''

def test_should_parse_simple_playlist_from_string():
    data = m3u8.parse(SIMPLE_PLAYLIST)
    assert 5220 == data['targetduration']
    assert ['http://media.example.com/entire.ts'] == [c['uri'] for c in data['chunks']]
    assert [5220] == [c['duration'] for c in data['chunks']]

def test_should_parse_sliding_window_playlist_from_string():
    data = m3u8.parse(SLIDING_WINDOW_PLAYLIST)
    assert 8 == data['targetduration']
    assert 2680 == data['media_sequence']
    assert ['https://priv.example.com/fileSequence2680.ts',
            'https://priv.example.com/fileSequence2681.ts',
            'https://priv.example.com/fileSequence2682.ts'] == [c['uri'] for c in data['chunks']]
    assert [8, 8, 8] == [c['duration'] for c in data['chunks']]

def test_should_load_playlist_with_encripted_segments_from_string():
    data = m3u8.parse(PLAYLIST_WITH_ENCRIPTED_SEGMENTS)
    assert 7794 == data['media_sequence']
    assert 15 == data['targetduration']
    assert 'AES-128' == data['key']['method']
    assert 'https://priv.example.com/key.php?r=52' == data['key']['uri']
    assert ['http://media.example.com/fileSequence52-1.ts',
            'http://media.example.com/fileSequence52-2.ts',
            'http://media.example.com/fileSequence52-3.ts'] == [c['uri'] for c in data['chunks']]
    assert [15, 15, 15] == [c['duration'] for c in data['chunks']]

def test_should_load_playlist_with_iv_from_string():
    data = m3u8.parse(PLAYLIST_WITH_ENCRIPTED_SEGMENTS_AND_IV)
    assert "/hls-key/tvglobokey.bin" == data['key']['uri']
    assert "AES-128" == data['key']['method']
    assert "0X10ef8f758ca555115584bb5b3c687f52" == data['key']['iv']
