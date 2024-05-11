# How to work with AES encrypted HLS streaming?

The segments may or may not be encrypted. The `keys` attribute list will
be a list  with all the different keys as described with `#EXT-X-KEY`:

Each key has the next properties:

-  `method`: ex.: "AES-128"
-  `uri`: the key uri, ex.: "http://videoserver.com/key.bin"
-  `iv`: the initialization vector, if available. Otherwise `None`.

If no `#EXT-X-KEY` is found, the `keys` list will have a unique element `None`. Multiple keys are supported.

If unencrypted and encrypted segments are mixed in the M3U8 file, then the list will contain a `None` element, with one
or more keys afterwards.

To traverse the list of keys available:

```python

    import m3u8

    m3u8_obj = m3u8.loads('#EXTM3U8 ... etc ...')
    len(m3u8_obj.keys)  # => returns the number of keys available in the list (normally 1)
    for key in m3u8_obj.keys:
       if key:  # First one could be None
          key.uri
          key.method
          key.iv
```

## How to get encrypted segments using a single key?

There are cases where listing segments for a given key is important. It's possible to
retrieve the list of segments encrypted with one key via `by_key` method in the
`segments` list.

Example of getting the segments with no encryption:

```python

    import m3u8

    m3u8_obj = m3u8.loads('#EXTM3U8 ... etc ...')
    segmk1 = m3u8_obj.segments.by_key(None)

    # Get the list of segments encrypted using last key
    segm = m3u8_obj.segments.by_key( m3u8_obj.keys[-1] )
```

With this method, is now possible also to change the key from some of the segments programmatically:


```python

    import m3u8

    m3u8_obj = m3u8.loads('#EXTM3U8 ... etc ...')

    # Create a new Key and replace it
    new_key = m3u8.Key("AES-128", "/encrypted/newkey.bin", None, iv="0xf123ad23f22e441098aa87ee")
    for segment in m3u8_obj.segments.by_key( m3u8_obj.keys[-1] ):
        segment.key = new_key
    # Remember to sync the key from the list as well
    m3u8_obj.keys[-1] = new_key
```


# How to work with variant/master HLS playlist/manifest?

A playlist can have a list to other playlist files, this is used to
represent multiple bitrates videos, and it's called `variant streams`_.
See an `example here`_.

```python

    variant_m3u8 = m3u8.loads('#EXTM3U8 ... contains a variant stream ...')
    variant_m3u8.is_variant    # in this case will be True

    for playlist in variant_m3u8.playlists:
        playlist.uri
        playlist.stream_info.bandwidth
```

the playlist object used in the for loop above has a few attributes:

-  `uri`: the url to the stream
-  `stream_info`: a `StreamInfo` object (actually a namedtuple) with
   all the attributes available to `#EXT-X-STREAM-INF`_
-  `media`: a list of related `Media` objects with all the attributes
   available to `#EXT-X-MEDIA`_
-  `playlist_type`: the type of the playlist, which can be one of `VOD`_
   (video on demand) or `EVENT`_

**NOTE: the following attributes are not implemented yet**, follow
`issue 4`_ for updates

-  `alternative_audios`: its an empty list, unless it's a playlist
   with `Alternative audio`_, in this case it's a list with `Media`
   objects with all the attributes available to `#EXT-X-MEDIA`_
-  `alternative_videos`: same as `alternative_audios`

A variant playlist can also have links to `I-frame playlists`_, which are used
to specify where the I-frames are in a video. See `Apple's documentation`_ on
this for more information. These I-frame playlists can be accessed in a similar
way to regular playlists.

```python

    variant_m3u8 = m3u8.loads('#EXTM3U ... contains a variant stream ...')

    for iframe_playlist in variant_m3u8.iframe_playlists:
        iframe_playlist.uri
        iframe_playlist.iframe_stream_info.bandwidth
```

The iframe_playlist object used in the for loop above has a few attributes:

-  `uri`: the url to the I-frame playlist
-  `base_uri`: the base uri of the variant playlist (if given)
-  `iframe_stream_info`: a `StreamInfo` object (same as a regular playlist)

# How to parse or dump custom (unsupported/unimplemented) HLS tags?

Quoting the documentation::

    Lines that start with the character '#' are either comments or tags.
    Tags begin with #EXT.  They are case-sensitive.  All other lines that
    begin with '#' are comments and SHOULD be ignored.

This library ignores all the non-standard tags by default. If you want them to be collected while loading the file content,
you need to pass a function to the `load/loads` functions, following the example below:

```python

    import m3u8

    def get_movie(line, lineno, data, state):
        if line.startswith('#MOVIE-NAME:'):
            custom_tag = line.split(':')
            data['movie'] = custom_tag[1].strip()

    m3u8_obj = m3u8.load('http://videoserver.com/playlist.m3u8', custom_tags_parser=get_movie)
    print(m3u8_obj.data['movie'])  #  million dollar baby
```

Also you are able to override parsing of existing standard tags.
To achieve this your custom_tags_parser function have to return boolean True - it will mean that you fully implement parsing of current line therefore 'main parser' can go to next line.

```python

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
```

Helper functions get_segment_custom_value() and save_segment_custom_value() are intended for getting/storing your parsed values per segment into Segment class.
After that all custom values will be accessible via property custom_parser_values of Segment instance.

In case you need to dump custom tags, you can use the following code snippet as inspiration:

```python

    def dumps_iptv(iptv : M3U8):
        output = ["#EXTM3U"]
        last_group = ""
        for seg in iptv.segments:
            segdumps = []
            seg_props = seg.custom_parser_values["extinf_props"]
            if seg_props["group-title"] != last_group and last_group != "":
                segdumps.append(2*"\n")
            last_group = seg_props["group-title"]
            if seg.uri:
                if seg.duration is not None:
                    segdumps.append("#EXTINF:%s" % number_to_string(seg.duration))
                    if seg_props["tvg-logo"]:
                        segdumps.append(" tvg-logo=\"%s\"" % seg_props["tvg-logo"])
                    if seg_props["group-title"]:
                        segdumps.append(" group-title=\"%s\"" % seg_props["group-title"])
                    if seg.title:
                        segdumps.append("," + seg.title)
                    segdumps.append("\n")
                segdumps.append(seg.uri)
            output.append("".join(segdumps))
        return "\n".join(output)
```

See `issue 347`_ for more information.

# How to use a custom python HTTP client?

If you don't want to use urllib to download playlists, having more control on how objects are fetched over the internet,
you can use your own client. `requests` is a well known Python HTTP library and it can be used with `m3u8`:

```python

    import m3u8
    import requests

    class RequestsClient():
        def download(self, uri, timeout=None, headers={}, verify_ssl=True):
            o = requests.get(uri, timeout=timeout, headers=headers)
            return o.text, o.url

    playlist = m3u8.load('http://videoserver.com/playlist.m3u8', http_client=RequestsClient())
    print(playlist.dumps())
```

The advantage of using a custom HTTP client is to refine SSL verification, proxies, performance, flexibility, etc.

# How to work behind an HTTP proxy?

In case you need to use a proxy but can't use a system wide proxy (HTTP/HTTPS proxy environment variables), you can pass your
HTTP/HTTPS proxies as a dict to the load function.

```python

    import m3u8

    proxies = {
        'http': 'http://10.10.1.10:3128',
        'https': 'http://10.10.1.10:1080',
    }

    http_client = m3u8.httpclient.DefaultHTTPClient(proxies)
    playlist = m3u8.load('http://videoserver.com/playlist.m3u8', http_client=http_client)  # this could also be an absolute filename
    print(playlist.dumps())
```
It works with the default client only. Custom HTTP clients must implement this feature.
