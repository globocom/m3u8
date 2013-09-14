import m3u8

def test_create_a_variant_m3u8_with_two_playlists():
    variant_m3u8 = m3u8.M3U8()

    subtitles = m3u8.Media('english_sub.m3u8', 'SUBTITLES', 'subs', 'en',
                           'English', 'YES', 'YES', 'NO', None)
    variant_m3u8.add_media(subtitles)

    low_playlist = m3u8.Playlist('http://example.com/low.m3u8', stream_info={'bandwidth': '1280000', 'program_id': '1', 'subtitles': 'subs'}, media=[subtitles], base_uri=None)
    high_playlist = m3u8.Playlist('http://example.com/high.m3u8', stream_info={'bandwidth': '3000000', 'program_id': '1', 'subtitles': 'subs'}, media=[subtitles], base_uri=None)

    variant_m3u8.add_playlist(low_playlist)
    variant_m3u8.add_playlist(high_playlist)

    expected_content = """\
#EXTM3U
#EXT-X-MEDIA:URI="english_sub.m3u8",TYPE=SUBTITLES,GROUP-ID="subs",LANGUAGE="en",NAME="English",DEFAULT=YES,AUTOSELECT=YES,FORCED=NO
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=1280000,SUBTITLES=subs
http://example.com/low.m3u8
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=3000000,SUBTITLES=subs
http://example.com/high.m3u8
"""
    assert expected_content == variant_m3u8.dumps()
