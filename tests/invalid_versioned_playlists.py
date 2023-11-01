# Should have at least version 2 if you have IV in EXT-X-KEY.
M3U8_RULE_IV = """
#EXTM3U
#EXT-X-VERSION: 1
#EXT-X-KEY: METHOD=AES-128, IV=0x123456789ABCDEF0123456789ABCDEF0, URI="https://example.com/key.bin"
#EXT-X-TARGETDURATION: 10
#EXTINF: 10.0,
https://example.com/segment1.ts
"""

# Should have at least version 3 if you have floating point EXTINF duration values.
M3U8_RULE_FLOATING_POINT = """
#EXTM3U
#EXT-X-VERSION: 2
#EXT-X-TARGETDURATION: 10
#EXTINF: 10.5,
https://example.com/segment1.ts
"""

# Should have at least version 4 if you have EXT-X-BYTERANGE or EXT-X-IFRAME-ONLY.
M3U8_RULE_BYTE_RANGE = """
#EXTM3U
#EXT-X-VERSION: 3
#EXT-X-BYTERANGE: 200000@1000
#EXT-X-TARGETDURATION: 10
#EXTINF: 10.0,
https://example.com/segment1.ts
"""
