import m3u8

def test_create_a_variant_m3u8_with_two_playlists():
    low_playlist = m3u8.Playlist('http://example.com/low.m3u8', stream_info={'bandwidth': '1280000', 'program_id': '1'}, base_uri=None)
    high_playlist = m3u8.Playlist('http://example.com/high.m3u8', stream_info={'bandwidth': '3000000', 'program_id': '1'}, base_uri=None)

    variant_m3u8 = m3u8.M3U8()
    variant_m3u8.add_playlist(low_playlist)
    variant_m3u8.add_playlist(high_playlist)

    expected_content = """\
#EXTM3U
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=1280000
http://example.com/low.m3u8
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=3000000
http://example.com/high.m3u8
"""
    assert expected_content == variant_m3u8.dumps()
