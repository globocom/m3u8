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

Encryption keys
---------------

The segments may or may not be encrypted. The ``keys`` attribute list will
be a list  with all the different keys as described with `#EXT-X-KEY`_:

Each key has the next properties:

-  ``method``: ex.: "AES-128"
-  ``uri``: the key uri, ex.: "http://videoserver.com/key.bin"
-  ``iv``: the initialization vector, if available. Otherwise ``None``.

If no ``#EXT-X-KEY`` is found, the ``keys`` list will have a unique element ``None``. Multiple keys are supported.

If unencrypted and encrypted segments are mixed in the M3U8 file, then the list will contain a ``None`` element, with one
or more keys afterwards.

To traverse the list of keys available:

.. code-block:: python

    import m3u8

    m3u8_obj = m3u8.loads('#EXTM3U8 ... etc ...')
    len(m3u8_obj.keys)  # => returns the number of keys available in the list (normally 1)
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

.. code-block:: python

    import m3u8

    m3u8_obj = m3u8.loads('#EXTM3U8 ... etc ...')
    segmk1 = m3u8_obj.segments.by_key(None)

    # Get the list of segments encrypted using last key
    segm = m3u8_obj.segments.by_key( m3u8_obj.keys[-1] )


With this method, is now possible also to change the key from some of the segments programmatically:


.. code-block:: python

    import m3u8

    m3u8_obj = m3u8.loads('#EXTM3U8 ... etc ...')

    # Create a new Key and replace it
    new_key = m3u8.Key("AES-128", "/encrypted/newkey.bin", None, iv="0xf123ad23f22e441098aa87ee")
    for segment in m3u8_obj.segments.by_key( m3u8_obj.keys[-1] ):
        segment.key = new_key
    # Remember to sync the key from the list as well
    m3u8_obj.keys[-1] = new_key



Variant playlists (variable bitrates)
-------------------------------------

A playlist can have a list to other playlist files, this is used to
represent multiple bitrates videos, and it's called `variant streams`_.
See an `example here`_.

.. code-block:: python

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

.. code-block:: python

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

This library ignores all the non-standard tags by default. If you want them to be collected while loading the file content,
you need to pass a function to the `load/loads` functions, following the example below:

.. code-block:: python

    import m3u8

    def get_movie(line, lineno, data, state):
        if line.startswith('#MOVIE-NAME:'):
            custom_tag = line.split(':')
            data['movie'] = custom_tag[1].strip()

    m3u8_obj = m3u8.load('http://videoserver.com/playlist.m3u8', custom_tags_parser=get_movie)
    print(m3u8_obj.data['movie'])  #  million dollar baby


Also you are able to override parsing of existing standard tags.
To achieve this your custom_tags_parser function have to return boolean True - it will mean that you fully implement parsing of current line therefore 'main parser' can go to next line.

.. code-block:: python

    import re
    import m3u8
    from m3u8 import protocol
    from m3u8.parser import save_segment_custom_value


    def parse_iptv_attributes(line, lineno, data, state):
        # Customize parsing #EXTINF
        if line.startswith(protocol.extinf):
            title = ''
            chunks = line.replace(protocol.extinf + ':', '').split(',', 1)
            if len(chunks) == 2:
                duration_and_props, title = chunks
            elif len(chunks) == 1:
                duration_and_props = chunks[0]

            additional_props = {}
            chunks = duration_and_props.strip().split(' ', 1)
            if len(chunks) == 2:
                duration, raw_props = chunks
                matched_props = re.finditer(r'([\w\-]+)="([^"]*)"', raw_props)
                for match in matched_props:
                    additional_props[match.group(1)] = match.group(2)
            else:
                duration = duration_and_props

            if 'segment' not in state:
                state['segment'] = {}
            state['segment']['duration'] = float(duration)
            state['segment']['title'] = title

            # Helper function for saving custom values
            save_segment_custom_value(state, 'extinf_props', additional_props)

            # Tell 'main parser' that we expect an URL on next lines
            state['expect_segment'] = True

            # Tell 'main parser' that it can go to next line, we've parsed current fully.
            return True


    if __name__ == '__main__':
        PLAYLIST = """#EXTM3U
        #EXTINF:-1 timeshift="0" catchup-days="7" catchup-type="flussonic" tvg-id="channel1" group-title="Group1",Channel1
        http://str00.iptv.domain/7331/mpegts?token=longtokenhere
        """

        parsed = m3u8.loads(PLAYLIST, custom_tags_parser=parse_iptv_attributes)

        first_segment_props = parsed.segments[0].custom_parser_values['extinf_props']
        print(first_segment_props['tvg-id'])  # 'channel1'
        print(first_segment_props['group-title'])  # 'Group1'
        print(first_segment_props['catchup-type'])  # 'flussonic'

Helper functions get_segment_custom_value() and save_segment_custom_value() are intended for getting/storing your parsed values per segment into Segment class.
After that all custom values will be accessible via property custom_parser_values of Segment instance.

Using different HTTP clients
----------------------------

If you don't want to use urllib to download playlists, having more control on how objects are fetched over the internet,
you can use your own client. `requests` is a well known Python HTTP library and it can be used with `m3u8`:

.. code-block:: python

    import m3u8
    import requests

    class RequestsClient():
        def download(self, uri, timeout=None, headers={}, verify_ssl=True):
            o = requests.get(uri, timeout=timeout, headers=headers)
            return o.text, o.url

    playlist = m3u8.load('http://videoserver.com/playlist.m3u8', http_client=RequestsClient())
    print(playlist.dumps())

The advantage of using a custom HTTP client is to refine SSL verification, proxies, performance, flexibility, etc.

Playlists behind proxies
------------------------

In case you need to use a proxy but can't use a system wide proxy (HTTP/HTTPS proxy environment variables), you can pass your
HTTP/HTTPS proxies as a dict to the load function.

.. code-block:: python

    import m3u8

    proxies = {
        'http': 'http://10.10.1.10:3128',
        'https': 'http://10.10.1.10:1080',
    }

    http_client = m3u8.httpclient.DefaultHTTPClient(proxies)
    playlist = m3u8.load('http://videoserver.com/playlist.m3u8', http_client=http_client)  # this could also be an absolute filename
    print(playlist.dumps())

It works with the default client only. Custom HTTP clients must implement this feature.

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
