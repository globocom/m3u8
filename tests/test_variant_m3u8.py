# coding: utf-8
# Copyright 2014 Globo.com Player authors. All rights reserved.
# Use of this source code is governed by a MIT License
# license that can be found in the LICENSE file.

import m3u8, playlists

def test_create_a_variant_m3u8_with_two_playlists():
    variant_m3u8 = m3u8.M3U8()

    subtitles = m3u8.Media('english_sub.m3u8', 'SUBTITLES', 'subs', 'en',
                           'English', 'YES', 'YES', 'NO', None)
    variant_m3u8.add_media(subtitles)

    low_playlist = m3u8.Playlist('http://example.com/low.m3u8', stream_info={'bandwidth': 1280000, 'program_id': 1, 'closed_captions': 'NONE', 'subtitles': 'subs'}, media=[subtitles], base_uri=None)
    high_playlist = m3u8.Playlist('http://example.com/high.m3u8', stream_info={'bandwidth': 3000000, 'program_id': 1, 'subtitles': 'subs'}, media=[subtitles], base_uri=None)

    variant_m3u8.add_playlist(low_playlist)
    variant_m3u8.add_playlist(high_playlist)

    expected_content = """\
#EXTM3U
#EXT-X-MEDIA:URI="english_sub.m3u8",TYPE=SUBTITLES,GROUP-ID="subs",LANGUAGE="en",NAME="English",DEFAULT=YES,AUTOSELECT=YES,FORCED=NO
#EXT-X-STREAM-INF:PROGRAM-ID=1,CLOSED-CAPTIONS=NONE,BANDWIDTH=1280000,SUBTITLES="subs"
http://example.com/low.m3u8
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=3000000,SUBTITLES="subs"
http://example.com/high.m3u8
"""
    assert expected_content == variant_m3u8.dumps()

def test_create_a_variant_m3u8_with_two_playlists_and_two_iframe_playlists():
    variant_m3u8 = m3u8.M3U8()

    subtitles = m3u8.Media('english_sub.m3u8', 'SUBTITLES', 'subs', 'en',
                           'English', 'YES', 'YES', 'NO', None)
    variant_m3u8.add_media(subtitles)

    low_playlist = m3u8.Playlist(
        uri='video-800k.m3u8',
        stream_info={'bandwidth': 800000,
                     'program_id': 1,
                     'resolution': '624x352',
                     'codecs': 'avc1.4d001f, mp4a.40.5',
                     'subtitles': 'subs'},
        media=[subtitles],
        base_uri='http://example.com/'
    )
    high_playlist = m3u8.Playlist(
        uri='video-1200k.m3u8',
        stream_info={'bandwidth': 1200000,
                     'program_id': 1,
                     'codecs': 'avc1.4d001f, mp4a.40.5',
                     'subtitles': 'subs'},
        media=[subtitles],
        base_uri='http://example.com/'
    )
    low_iframe_playlist = m3u8.IFramePlaylist(
        uri='video-800k-iframes.m3u8',
        iframe_stream_info={'bandwidth': 151288,
                            'program_id': 1,
                            'closed_captions': None,
                            'resolution': '624x352',
                            'codecs': 'avc1.4d001f'},
        base_uri='http://example.com/'
    )
    high_iframe_playlist = m3u8.IFramePlaylist(
        uri='video-1200k-iframes.m3u8',
        iframe_stream_info={'bandwidth': 193350,
                            'codecs': 'avc1.4d001f'},
        base_uri='http://example.com/'
    )

    variant_m3u8.add_playlist(low_playlist)
    variant_m3u8.add_playlist(high_playlist)
    variant_m3u8.add_iframe_playlist(low_iframe_playlist)
    variant_m3u8.add_iframe_playlist(high_iframe_playlist)

    expected_content = """\
#EXTM3U
#EXT-X-MEDIA:URI="english_sub.m3u8",TYPE=SUBTITLES,GROUP-ID="subs",\
LANGUAGE="en",NAME="English",DEFAULT=YES,AUTOSELECT=YES,FORCED=NO
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=800000,RESOLUTION=624x352,\
CODECS="avc1.4d001f, mp4a.40.5",SUBTITLES="subs"
video-800k.m3u8
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=1200000,\
CODECS="avc1.4d001f, mp4a.40.5",SUBTITLES="subs"
video-1200k.m3u8
#EXT-X-I-FRAME-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=151288,RESOLUTION=624x352,\
CODECS="avc1.4d001f",URI="video-800k-iframes.m3u8"
#EXT-X-I-FRAME-STREAM-INF:BANDWIDTH=193350,\
CODECS="avc1.4d001f",URI="video-1200k-iframes.m3u8"
"""
    assert expected_content == variant_m3u8.dumps()


def test_variant_playlist_with_average_bandwidth():
    variant_m3u8 = m3u8.M3U8()

    low_playlist = m3u8.Playlist(
        'http://example.com/low.m3u8',
        stream_info={'bandwidth': 1280000,
                     'average_bandwidth': 1257891,
                     'program_id': 1,
                     'subtitles': 'subs'},
        media=[],
        base_uri=None
    )
    high_playlist = m3u8.Playlist(
        'http://example.com/high.m3u8',
        stream_info={'bandwidth': 3000000,
                     'average_bandwidth': 2857123,
                     'program_id': 1,
                     'subtitles': 'subs'},
       media=[],
       base_uri=None
    )

    variant_m3u8.add_playlist(low_playlist)
    variant_m3u8.add_playlist(high_playlist)

    expected_content = """\
#EXTM3U
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=1280000,AVERAGE-BANDWIDTH=1257891
http://example.com/low.m3u8
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=3000000,AVERAGE-BANDWIDTH=2857123
http://example.com/high.m3u8
"""
    assert expected_content == variant_m3u8.dumps()


def test_variant_playlist_with_video_range():
    variant_m3u8 = m3u8.M3U8()

    sdr_playlist = m3u8.Playlist(
        'http://example.com/sdr.m3u8',
        stream_info={'bandwidth': 1280000,
                     'video_range': 'SDR',
                     'program_id': 1},
        media=[],
        base_uri=None
    )
    hdr_playlist = m3u8.Playlist(
        'http://example.com/hdr.m3u8',
        stream_info={'bandwidth': 3000000,
                     'video_range': 'PQ',
                     'program_id': 1},
       media=[],
       base_uri=None
    )

    variant_m3u8.add_playlist(sdr_playlist)
    variant_m3u8.add_playlist(hdr_playlist)

    expected_content = """\
#EXTM3U
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=1280000,VIDEO-RANGE=SDR
http://example.com/sdr.m3u8
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=3000000,VIDEO-RANGE=PQ
http://example.com/hdr.m3u8
"""
    assert expected_content == variant_m3u8.dumps()

def test_variant_playlist_with_multiple_media():
    variant_m3u8 = m3u8.loads(playlists.MULTI_MEDIA_PLAYLIST)
    assert variant_m3u8.dumps() == playlists.MULTI_MEDIA_PLAYLIST
