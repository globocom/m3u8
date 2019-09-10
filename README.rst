.. image:: https://travis-ci.org/globocom/m3u8.svg
    :target: https://travis-ci.org/globocom/m3u8

.. image:: https://coveralls.io/repos/globocom/m3u8/badge.png?branch=master
    :target: https://coveralls.io/r/globocom/m3u8?branch=master

.. image:: https://badge.fury.io/py/m3u8.svg
    :target: https://badge.fury.io/py/m3u8


m3u8
====

Python `m3u8`_ parser.

Documentation
=============

The basic usage is to create a playlist object from uri, file path or
directly from a string:

::

    import m3u8

    m3u8_obj = m3u8.load('http://videoserver.com/playlist.m3u8')  # this could also be an absolute filename
    print m3u8_obj.segments
    print m3u8_obj.target_duration

    # if you already have the content as string, use

    m3u8_obj = m3u8.loads('#EXTM3U8 ... etc ... ')

Supported tags
==============

* #EXT-X-TARGETDURATION
* #EXT-X-MEDIA-SEQUENCE
* #EXT-X-DISCONTINUITY-SEQUENCE
* #EXT-X-PROGRAM-DATE-TIME
* #EXT-X-MEDIA
* #EXT-X-PLAYLIST-TYPE
* #EXT-X-KEY
* #EXT-X-STREAM-INF
* #EXT-X-VERSION
* #EXT-X-ALLOW-CACHE
* #EXT-X-ENDLIST
* #EXTINF
* #EXT-X-I-FRAMES-ONLY
* #EXT-X-BYTERANGE
* #EXT-X-I-FRAME-STREAM-INF
* #EXT-X-DISCONTINUITY
* #EXT-X-CUE-OUT
* #EXT-X-CUE-OUT-CONT
* #EXT-X-INDEPENDENT-SEGMENTS
* #EXT-OATCLS-SCTE35
* #EXT-X-CUE-OUT
* #EXT-X-CUE-IN
* #EXT-X-CUE-SPAN
* #EXT-X-MAP
* #EXT-X-START
* #EXT-X-SERVER-CONTROL
* #EXT-X-PART-INF
* #EXT-X-PART
* #EXT-X-RENDITION-REPORT
* #EXT-X-SKIP
* #EXT-X-SESSION-DATA

Encryption keys
---------------

The segments may be or not encrypted. The ``keys`` attribute list will
be an list  with all the different keys as described with `#EXT-X-KEY`_:

Each key has the next properties:

-  ``method``: ex.: "AES-128"
-  ``uri``: the key uri, ex.: "http://videoserver.com/key.bin"
-  ``iv``: the initialization vector, if available. Otherwise ``None``.

If no ``#EXT-X-KEY`` is found, the ``keys`` list will have a unique element ``None``. Multiple keys are supported.

If unencrypted and encrypted segments are mixed in the M3U8 file, then the list will contain a ``None`` element, with one
or more keys afterwards.

To traverse the list of keys available:

::

    import m3u8

    m3u8_obj = m3u8.loads('#EXTM3U8 ... etc ...')
    len(m3u8_obj.keys) => returns the number of keys available in the list (normally 1)
    for key in m3u8_obj.keys:
       if key:  # First one could be None
          key.uri
          key.method
          key.iv


Getting segments encrypted with one key
---------------------------------------

There are cases where listing segments for a given key is important. It's possible to
retrieve the list of segments encrypted with one key via ``by_key`` method in the
``segments`` list.

Example of getting the segments with no encryption:

::

    import m3u8

    m3u8_obj = m3u8.loads('#EXTM3U8 ... etc ...')
    segmk1 = m3u8_obj.segments.by_key(None)

    # Get the list of segments encrypted using last key
    segm = m3u8_obj.segments.by_key( m3u8_obj.keys[-1] )


With this method, is now possible also to change the key from some of the segments programatically:


::

    import m3u8

    m3u8_obj = m3u8.loads('#EXTM3U8 ... etc ...')

    # Create a new Key and replace it
    new_key = m3u8.Key("AES-128", "/encrypted/newkey.bin", None, iv="0xf123ad23f22e441098aa87ee")
    for segment in m3u8_obj.segments.by_key( m3u8_obj.keys[-1] ):
        segm.key = new_key
    # Remember to sync the key from the list as well
    m3u8_obj.keys[-1] = new_key



Variant playlists (variable bitrates)
-------------------------------------

A playlist can have a list to other playlist files, this is used to
represent multiple bitrates videos, and it's called `variant streams`_.
See an `example here`_.

::

    variant_m3u8 = m3u8.loads('#EXTM3U8 ... contains a variant stream ...')
    variant_m3u8.is_variant    # in this case will be True

    for playlist in variant_m3u8.playlists:
        playlist.uri
        playlist.stream_info.bandwidth

the playlist object used in the for loop above has a few attributes:

-  ``uri``: the url to the stream
-  ``stream_info``: a ``StreamInfo`` object (actually a namedtuple) with
   all the attributes available to `#EXT-X-STREAM-INF`_
-  ``media``: a list of related ``Media`` objects with all the attributes
   available to `#EXT-X-MEDIA`_
-  ``playlist_type``: the type of the playlist, which can be one of `VOD`_
   (video on demand) or `EVENT`_

**NOTE: the following attributes are not implemented yet**, follow
`issue 4`_ for updates

-  ``alternative_audios``: its an empty list, unless it's a playlist
   with `Alternative audio`_, in this case it's a list with ``Media``
   objects with all the attributes available to `#EXT-X-MEDIA`_
-  ``alternative_videos``: same as ``alternative_audios``

A variant playlist can also have links to `I-frame playlists`_, which are used
to specify where the I-frames are in a video. See `Apple's documentation`_ on
this for more information. These I-frame playlists can be accessed in a similar
way to regular playlists.

::

    variant_m3u8 = m3u8.loads('#EXTM3U ... contains a variant stream ...')

    for iframe_playlist in variant_m3u8.iframe_playlists:
        iframe_playlist.uri
        iframe_playlist.iframe_stream_info.bandwidth

The iframe_playlist object used in the for loop above has a few attributes:

-  ``uri``: the url to the I-frame playlist
-  ``base_uri``: the base uri of the variant playlist (if given)
-  ``iframe_stream_info``: a ``StreamInfo`` object (same as a regular playlist)

Custom tags
-----------

Quoting the documentation::

    Lines that start with the character '#' are either comments or tags.
    Tags begin with #EXT.  They are case-sensitive.  All other lines that
    begin with '#' are comments and SHOULD be ignored.

This library ignores all the non standard tags by default. If you want them to be collected while loading the file content,
you need to pass a function to the `load/loads` functions, following the example below:

::

    import m3u8

    def get_movie(line, data, lineno):
        if line.startswith('#MOVIE-NAME:'):
            custom_tag = line.split(':')
            data['movie'] = custom_tag[1].strip()

    m3u8_obj = m3u8.load('http://videoserver.com/playlist.m3u8', custom_tags_parser=get_movie)
    print(m3u8_obj.data['movie'])  #  million dollar baby


Running Tests
=============

::

    $ ./runtests

Contributing
============

All contribution is welcome, but we will merge a pull request if, and only if, it

-  has tests
-  follows the code conventions

If you plan to implement a new feature or something that will take more
than a few minutes, please open an issue to make sure we don't work on
the same thing.

.. _m3u8: https://tools.ietf.org/html/rfc8216
.. _#EXT-X-KEY: https://tools.ietf.org/html/rfc8216#section-4.3.2.4
.. _issue 1: https://github.com/globocom/m3u8/issues/1
.. _variant streams: https://tools.ietf.org/html/rfc8216#section-6.2.4
.. _example here: http://tools.ietf.org/html/draft-pantos-http-live-streaming-08#section-8.5
.. _#EXT-X-STREAM-INF: https://tools.ietf.org/html/rfc8216#section-4.3.4.2
.. _issue 4: https://github.com/globocom/m3u8/issues/4
.. _I-frame playlists: https://tools.ietf.org/html/rfc8216#section-4.3.4.3
.. _Apple's documentation: https://developer.apple.com/library/ios/technotes/tn2288/_index.html#//apple_ref/doc/uid/DTS40012238-CH1-I_FRAME_PLAYLIST
.. _Alternative audio: http://tools.ietf.org/html/draft-pantos-http-live-streaming-08#section-8.7
.. _#EXT-X-MEDIA: https://tools.ietf.org/html/rfc8216#section-4.3.4.1
.. _VOD: https://developer.apple.com/library/mac/technotes/tn2288/_index.html#//apple_ref/doc/uid/DTS40012238-CH1-TNTAG2
.. _EVENT: https://developer.apple.com/library/mac/technotes/tn2288/_index.html#//apple_ref/doc/uid/DTS40012238-CH1-EVENT_PLAYLIST
