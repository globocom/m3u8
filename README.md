m3u8
====

Python [m3u8](http://tools.ietf.org/html/draft-pantos-http-live-streaming-08) parser.

# Documentation

The basic usage is to create a playlist object from a file or directly from a string:

    import m3u8
  
    m3u8_obj = m3u8.load('/tmp/playlist.m3u8')
    print m3u8_obj.chunks
    print m3u8_obj.target_duration
  
    # if you already have the content as string, use
  
    m3u8_obj = m3u8.loads('#EXTM3U8 ... etc ... ')

## [not implemented yet] Variant playlists (variable bitrates)

**See [issue 4](https://github.com/globocom/m3u8/issues/4)**

A playlist can have a list to other playlist files, this is used to represent multiple bitrates videos, and it's
called [variant streams](http://tools.ietf.org/html/draft-pantos-http-live-streaming-08#section-6.2.4). 
See an [example here](http://tools.ietf.org/html/draft-pantos-http-live-streaming-08#section-8.5).

    variant_m3u8 = m3u8.loads('#EXTM3U8 ... contains a variant stream ...')
    variant_m3u8.is_variant    # in this case will be True
    
    for playlist in variant_m3u8.playlists:
        playlist.resource
        playlist.stream_info.bandwidth

the playlist object used in the for loop above has a few attributes:

- `resource`: the url to the stream
- `stream_info`: a `StreamInfo` object (actually a namedtuple) with all the attributes available to [#EXT-X-STREAM-INF](http://tools.ietf.org/html/draft-pantos-http-live-streaming-08#section-3.4.10)
- `iframe_stream_info`: usually `None`, unless it's a playlist with [I-Frames](http://tools.ietf.org/html/draft-pantos-http-live-streaming-08#section-3.4.13),
   in this case it's also a namedtuple `IFrameStreamInfo` with all the attribute available to [#EXT-X-I-FRAME-STREAM-INF](http://tools.ietf.org/html/draft-pantos-http-live-streaming-08#section-3.4.13)
- `alternative_audios`: it's an empty list, unless it's a playlist with [Alternative audio](http://tools.ietf.org/html/draft-pantos-http-live-streaming-08#section-8.7),
   in this case it's a list with `Media` objects with all the attributes available to [#X-EXT-MEDIA](http://tools.ietf.org/html/draft-pantos-http-live-streaming-08#section-3.4.9)
- `alternative_videos`: same as `alternative_audios`


# Running Tests

    $ ./runtests

# Contributing

All contribution is welcome! If, and only if, it

- has tests
- follows the code conventions

If you plan to implement a new feature or something that will take more than
a few minutes, plase open an issue to make sure we don't work on the same thing.
