m3u8
====

Python [m3u8](http://tools.ietf.org/html/draft-pantos-http-live-streaming-08) parser.

Usage
-----

    import m3u8
  
    m3u8_obj = m3u8.load('/tmp/playlist.m3u8')
    print m3u8_obj.chunks
    print m3u8_obj.target_duration
  
    # if you already have the content as string, use
  
    m3u8_obj = m3u8.loads('/tmp/playlist.m3u8')

Runnign Tests
-------------

    $ ./runtests

Contributing
------------

All contribution is welcome! If, and only if, it

- has tests
- follows the code conventions

If you plan to implement a new feature or something that will take more than
a few minutes before a pull request, plase open an issue to make sure we don't
work on the same thing.
