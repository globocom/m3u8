'''
Test server to deliver stubed M3U8s
'''
from os.path import dirname, abspath, join

from bottle import route, run, response
import bottle

playlists = abspath(join(dirname(__file__), 'playlists'))

@route('/simple.m3u8')
def simple():
    response.set_header('Content-Type', 'application/vnd.apple.mpegurl')
    return m3u8_file('simple-playlist.m3u8')

def m3u8_file(filename):
    with open(join(playlists, filename)) as fileobj:
        return fileobj.read().strip()

bottle.debug = True
run(host='localhost', port=8112)
