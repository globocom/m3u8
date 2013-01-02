from os.path import dirname, abspath, join

TEST_HOST = 'http://localhost:8112'

SIMPLE_PLAYLIST = '''
#EXTM3U
#EXT-X-TARGETDURATION:5220
#EXTINF:5220,
http://media.example.com/entire.ts
#EXT-X-ENDLIST
'''

SIMPLE_PLAYLIST_FILENAME = abspath(join(dirname(__file__), 'playlists/simple-playlist.m3u8'))

SIMPLE_PLAYLIST_URI = TEST_HOST + '/simple.m3u8'

PLAYLIST_WITH_NON_INTEGER_DURATION = '''
#EXTM3U
#EXT-X-TARGETDURATION:5220.5
#EXTINF:5220.5,
http://media.example.com/entire.ts
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

VARIANT_PLAYLIST = '''
#EXTM3U
#EXT-X-STREAM-INF:PROGRAM-ID=1, BANDWIDTH=1280000
http://example.com/low.m3u8
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=2560000
http://example.com/mid.m3u8
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=7680000
http://example.com/hi.m3u8
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=65000,CODECS="mp4a.40.5,avc1.42801e"
http://example.com/audio-only.m3u8
'''

PLAYLIST_WITH_ENCRIPTED_SEGMENTS_AND_IV = '''
#EXTM3U
#EXT-X-MEDIA-SEQUENCE:82400
#EXT-X-ALLOW-CACHE:NO
#EXT-X-VERSION:2
#EXT-X-KEY:METHOD=AES-128,URI="/hls-key/key.bin", IV=0X10ef8f758ca555115584bb5b3c687f52
#EXT-X-TARGETDURATION:8
#EXTINF:8,
../../../../hls/streamNum82400.ts
#EXTINF:8,
../../../../hls/streamNum82401.ts
#EXTINF:8,
../../../../hls/streamNum82402.ts
#EXTINF:8,
../../../../hls/streamNum82403.ts
#EXTINF:8,
../../../../hls/streamNum82404.ts
#EXTINF:8,
../../../../hls/streamNum82405.ts
'''

SIMPLE_PLAYLIST_WITH_TITLE = '''
#EXTM3U
#EXT-X-TARGETDURATION:5220
#EXTINF:5220,"A sample title"
http://media.example.com/entire.ts
#EXT-X-ENDLIST
'''

SIMPLE_PLAYLIST_WITH_RESOLUTION = '''
#EXTM3U
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=445000,RESOLUTION=512x288,CODECS="avc1.77.30, mp4a.40.5"
index_0_av.m3u8?e=b471643725c47acd
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=45000,CODECS="mp4a.40.5"
index_0_a.m3u8?e=b471643725c47acd
'''

RELATIVE_PLAYLIST_FILENAME = abspath(join(dirname(__file__), 'playlists/relative-playlist.m3u8'))

RELATIVE_PLAYLIST_URI = TEST_HOST + '/path/to/relative-playlist.m3u8'

del abspath, dirname, join
