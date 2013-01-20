import m3u8


def test_create_a_variant_m3u8_with_three_playlists():
    low_playlist = m3u8.Playlist('http://example.com/low.m3u8', stream_info={'bandwidth': '1280000', 'program_id': '1'}, baseuri=None)
    high_playlist = m3u8.Playlist('http://example.com/high.m3u8', stream_info={'bandwidth': '3000000', 'program_id': '1'}, baseuri=None)
    i_frame_playlist = m3u8.IFramePlaylist(iframe_stream_info={'uri': 'http://example.com/iframe.m3u8', 'bandwidth': '128000', 'program_id': '1'}, baseuri=None)

    variant_m3u8 = m3u8.M3U8()
    variant_m3u8.add_playlist(low_playlist)
    variant_m3u8.add_playlist(high_playlist)
    variant_m3u8.add_iframe_playlist(i_frame_playlist)

    expected_content = """\
#EXTM3U
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=1280000
http://example.com/low.m3u8
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=3000000
http://example.com/high.m3u8
#EXT-X-I-FRAME-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=128000,URI="http://example.com/iframe.m3u8"\
"""
    assert expected_content == variant_m3u8.dumps()
