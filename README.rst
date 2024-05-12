.. image:: https://github.com/globocom/m3u8/actions/workflows/main.yml/badge.svg

.. image:: https://badge.fury.io/py/m3u8.svg
    :target: https://badge.fury.io/py/m3u8

m3u8
====

Python `m3u8`_ parser.

Documentation
=============

Loading a playlist
------------------

To load a playlist into an object from uri, file path or directly from string, use the `load/loads` functions:

.. code-block:: python

    import m3u8

    playlist = m3u8.load('http://videoserver.com/playlist.m3u8')  # this could also be an absolute filename
    print(playlist.segments)
    print(playlist.target_duration)

    # if you already have the content as string, use

    playlist = m3u8.loads('#EXTM3U8 ... etc ... ')

Dumping a playlist
------------------

To dump a playlist from an object to the console or a file, use the `dump/dumps` functions:

.. code-block:: python

    import m3u8

    playlist = m3u8.load('http://videoserver.com/playlist.m3u8')
    print(playlist.dumps())

    # if you want to write a file from its content

    playlist.dump('playlist.m3u8')


Supported tags
==============

* `#EXT-X-TARGETDURATION`_
* `#EXT-X-MEDIA-SEQUENCE`_
* `#EXT-X-DISCONTINUITY-SEQUENCE`_
* `#EXT-X-PROGRAM-DATE-TIME`_
* `#EXT-X-MEDIA`_
* `#EXT-X-PLAYLIST-TYPE`_
* `#EXT-X-KEY`_
* `#EXT-X-STREAM-INF`_
* `#EXT-X-VERSION`_
* `#EXT-X-ALLOW-CACHE`_
* `#EXT-X-ENDLIST`_
* `#EXTINF`_
* `#EXT-X-I-FRAMES-ONLY`_
* `#EXT-X-BITRATE`_
* `#EXT-X-BYTERANGE`_
* `#EXT-X-I-FRAME-STREAM-INF`_
* `#EXT-X-IMAGES-ONLY`_
* `#EXT-X-IMAGE-STREAM-INF`_
* `#EXT-X-TILES`_
* `#EXT-X-DISCONTINUITY`_
* #EXT-X-CUE-OUT
* #EXT-X-CUE-OUT-CONT
* #EXT-X-CUE-IN
* #EXT-X-CUE-SPAN
* #EXT-OATCLS-SCTE35
* `#EXT-X-INDEPENDENT-SEGMENTS`_
* `#EXT-X-MAP`_
* `#EXT-X-START`_
* `#EXT-X-SERVER-CONTROL`_
* `#EXT-X-PART-INF`_
* `#EXT-X-PART`_
* `#EXT-X-RENDITION-REPORT`_
* `#EXT-X-SKIP`_
* `#EXT-X-SESSION-DATA`_
* `#EXT-X-PRELOAD-HINT`_
* `#EXT-X-SESSION-KEY`_
* `#EXT-X-DATERANGE`_
* `#EXT-X-GAP`_
* `#EXT-X-CONTENT-STEERING`_

Frequently Asked Questions
==========================

* `FAQ`_

Running Tests
=============

.. code-block:: bash

    $ ./runtests

Contributing
============

All contributions are welcome, but we will merge a pull request if, and only if, it

-  has tests
-  follows the code conventions

If you plan to implement a new feature or something that will take more
than a few minutes, please open an issue to make sure we don't work on
the same thing.

.. _m3u8: https://tools.ietf.org/html/rfc8216
.. _issue 347: https://github.com/globocom/m3u8/issues/347
.. _#EXT-X-VERSION: https://tools.ietf.org/html/rfc8216#section-4.3.1.2
.. _#EXTINF: https://tools.ietf.org/html/rfc8216#section-4.3.2.1
.. _#EXT-X-ALLOW-CACHE: https://datatracker.ietf.org/doc/html/draft-pantos-http-live-streaming-07#section-3.3.6
.. _#EXT-X-BITRATE: https://datatracker.ietf.org/doc/html/draft-pantos-hls-rfc8216bis#section-4.4.4.8
.. _#EXT-X-BYTERANGE: https://tools.ietf.org/html/rfc8216#section-4.3.2.2
.. _#EXT-X-DISCONTINUITY: https://tools.ietf.org/html/rfc8216#section-4.3.2.3
.. _#EXT-X-KEY: https://tools.ietf.org/html/rfc8216#section-4.3.2.4
.. _#EXT-X-MAP: https://tools.ietf.org/html/rfc8216#section-4.3.2.5
.. _#EXT-X-PROGRAM-DATE-TIME: https://tools.ietf.org/html/rfc8216#section-4.3.2.6
.. _#EXT-X-DATERANGE: https://tools.ietf.org/html/rfc8216#section-4.3.2.7
.. _#EXT-X-TARGETDURATION: https://tools.ietf.org/html/rfc8216#section-4.3.3.1
.. _#EXT-X-MEDIA-SEQUENCE: https://tools.ietf.org/html/rfc8216#section-4.3.3.2
.. _#EXT-X-DISCONTINUITY-SEQUENCE: https://tools.ietf.org/html/rfc8216#section-4.3.3.3
.. _#EXT-X-ENDLIST: https://tools.ietf.org/html/rfc8216#section-4.3.3.4
.. _#EXT-X-PLAYLIST-TYPE: https://tools.ietf.org/html/rfc8216#section-4.3.3.5
.. _#EXT-X-I-FRAMES-ONLY: https://tools.ietf.org/html/rfc8216#section-4.3.3.6
.. _#EXT-X-MEDIA: https://tools.ietf.org/html/rfc8216#section-4.3.4.1
.. _#EXT-X-STREAM-INF: https://tools.ietf.org/html/rfc8216#section-4.3.4.2
.. _#EXT-X-I-FRAME-STREAM-INF: https://tools.ietf.org/html/rfc8216#section-4.3.4.3
.. _#EXT-X-IMAGES-ONLY: https://github.com/image-media-playlist/spec/blob/master/image_media_playlist_v0_4.pdf
.. _#EXT-X-IMAGE-STREAM-INF: https://github.com/image-media-playlist/spec/blob/master/image_media_playlist_v0_4.pdf
.. _#EXT-X-TILES: https://github.com/image-media-playlist/spec/blob/master/image_media_playlist_v0_4.pdf
.. _#EXT-X-SESSION-DATA: https://tools.ietf.org/html/rfc8216#section-4.3.4.4
.. _#EXT-X-SESSION-KEY: https://tools.ietf.org/html/rfc8216#section-4.3.4.5
.. _#EXT-X-INDEPENDENT-SEGMENTS: https://tools.ietf.org/html/rfc8216#section-4.3.5.1
.. _#EXT-X-START: https://tools.ietf.org/html/rfc8216#section-4.3.5.2
.. _#EXT-X-PRELOAD-HINT: https://datatracker.ietf.org/doc/html/draft-pantos-hls-rfc8216bis-09#section-4.4.5.3
.. _#EXT-X-DATERANGE: https://tools.ietf.org/html/rfc8216#section-4.3.2.7
.. _#EXT-X-GAP: https://tools.ietf.org/html/draft-pantos-hls-rfc8216bis-05#section-4.4.2.7
.. _#EXT-X-CONTENT-STEERING: https://tools.ietf.org/html/draft-pantos-hls-rfc8216bis-10#section-4.4.6.64
.. _#EXT-X-SKIP: https://datatracker.ietf.org/doc/html/draft-pantos-hls-rfc8216bis#section-4.4.5.2
.. _#EXT-X-RENDITION-REPORT: https://datatracker.ietf.org/doc/html/draft-pantos-hls-rfc8216bis#section-4.4.5.4
.. _#EXT-X-PART: https://datatracker.ietf.org/doc/html/draft-pantos-hls-rfc8216bis#section-4.4.4.9
.. _#EXT-X-PART-INF: https://datatracker.ietf.org/doc/html/draft-pantos-hls-rfc8216bis#section-4.4.3.7
.. _#EXT-X-SERVER-CONTROL: https://datatracker.ietf.org/doc/html/draft-pantos-hls-rfc8216bis#section-4.4.3.8
.. _issue 1: https://github.com/globocom/m3u8/issues/1
.. _variant streams: https://tools.ietf.org/html/rfc8216#section-6.2.4
.. _example here: http://tools.ietf.org/html/draft-pantos-http-live-streaming-08#section-8.5
.. _issue 4: https://github.com/globocom/m3u8/issues/4
.. _I-frame playlists: https://tools.ietf.org/html/rfc8216#section-4.3.4.3
.. _Apple's documentation: https://developer.apple.com/library/ios/technotes/tn2288/_index.html#//apple_ref/doc/uid/DTS40012238-CH1-I_FRAME_PLAYLIST
.. _Alternative audio: http://tools.ietf.org/html/draft-pantos-http-live-streaming-08#section-8.7
.. _VOD: https://developer.apple.com/library/mac/technotes/tn2288/_index.html#//apple_ref/doc/uid/DTS40012238-CH1-TNTAG2
.. _EVENT: https://developer.apple.com/library/mac/technotes/tn2288/_index.html#//apple_ref/doc/uid/DTS40012238-CH1-EVENT_PLAYLIST
.. _FAQ: https://github.com/globocom/m3u8/blob/master/FAQ.md
