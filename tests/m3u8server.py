# coding: utf-8
# Copyright 2014 Globo.com Player authors. All rights reserved.
# Use of this source code is governed by a MIT License
# license that can be found in the LICENSE file.

#Test server to deliver stubed M3U8s

from os.path import dirname, abspath, join

from bottle import route, run, response, redirect
import bottle

playlists = abspath(join(dirname(__file__), 'playlists'))

@route('/path/to/redirect_me')
def simple():
    redirect('/simple.m3u8')

@route('/simple.m3u8')
def simple():
    response.set_header('Content-Type', 'application/vnd.apple.mpegurl')
    return m3u8_file('simple-playlist.m3u8')

@route('/path/to/relative-playlist.m3u8')
def simple():
    response.set_header('Content-Type', 'application/vnd.apple.mpegurl')
    return m3u8_file('relative-playlist.m3u8')

def m3u8_file(filename):
    with open(join(playlists, filename)) as fileobj:
        return fileobj.read().strip()

bottle.debug = True
run(host='localhost', port=8112)
