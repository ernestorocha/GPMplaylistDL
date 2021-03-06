#!/usr/bin/python3
# -*- coding: utf-8 -*- 
'''
This is a little script to download every song from every playlist
if your Google Play Music account. Songs are organized as follows:
    <playlist>/<artist>/<album>/<song>.mp3

I Highly recomend putting this file in your %USER%\Music folder
before running.

Please note that this will ONLY work if you have a subscription.

Requirements:
- gmusicapi
- requests

For further documentation on what I'm using here, check out:
http://unofficial-google-music-api.readthedocs.io/en/latest/reference/mobileclient.html
'''

from gmusicapi import Mobileclient
import requests
import os, unicodedata

# Account settings
username = ""
password = "" # App-specific passwords work here too

# Output Settings
showSongs = True # set to true to show each song path before it's downloaded
quiet = False # set to true to completely silence

# Playlist settings
## Export as...
m3u = True
winamp = False

rootPath = "" # Playlists can require abs. paths. Default is current dir
if rootPath == "":
    rootPath = os.path.realpath('.')


# Here thar be dragons

# Start with some declarations
def dlSong(id, name):
    url = mc.get_stream_url(id, device_id=device_id)
    r = requests.get(url, stream=True)
    with open(name, "wb") as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)

def clean(string):
    # Replace chars with alternatives - "<>:\"/|?*" - thanks to https://stackoverflow.com/a/51548942/2999220
    string = string.replace('<', '‹')
    string = string.replace('>', '›')
    string = string.replace(':', '：')
    string = string.replace('"', '”')
    string = string.replace('\\', '＼')
    string = string.replace('/', '∕')
    string = string.replace('|', '⏐')
    string = string.replace('?', '︖')
    string = string.replace('*', '⁎')
    return string

class Playlist(object):
    def __init__(self, name):
        name = clean(name)
        self.name = name
        self.path = name
        self.songs = []
    def __repr__(self):
        return "{}: {} songs".format(self.name, len(self.songs))
    def addSong(self, song):
        self.songs.append(song)
    def makePath(self, song):
        song.path = os.path.join(rootPath, clean(song.artist), clean(song.album))
        try:
            os.makedirs(song.path)
        except:
            pass
    def songPath(self, song):
        self.makePath(song)
        return os.path.join(song.path, clean(song.title) + ".mp3")

class Song(object):
    def __init__(self, tid, title, artist, album, length):
        self.tid = clean(tid)
        self.title = clean(title)
        self.artist = clean(artist)
        self.album = clean(album)
        self.length = length
    def __repr__(self):
        return "{} - {}".format(self.artist, self.title)

# Login
mc = Mobileclient()
mc.__init__(debug_logging=False, validate=True, verify_ssl=True)
mc.login(username, password, mc.FROM_MAC_ADDRESS)

# Pick a device_id for downloading later
device_id = None
for device in mc.get_registered_devices():
    if device['type'] == 'ANDROID':
        device_id = device['id'][2:] #.encode('ascii','ignore')
        break
    elif device['type'] == 'IOS':
        device_id = device['id']
        break

if not device_id:
    print("No Android or iOS device linked to account!")
    exit()

mc = Mobileclient()
mc.login(username, password, device_id)

# Grab all playlists, and sort them into a structure
playlists = mc.get_all_user_playlist_contents()
if not quiet:
    print(len(playlists), "playlist(s) found.")
master = []
for ply in playlists:
    name = ply['name']
    curPlaylist = Playlist(name)
    tracks = ply['tracks']
    for song in tracks:
        if song['source'] == u"2": # If song is not custom upload
            tid = song['trackId']
            title = song['track']['title']
            artist = song['track']['artist']
            album = song['track']['album']
            length = int(song['track']['durationMillis']) / 1000
            newSong = Song(tid, title, artist, album, length)
            curPlaylist.addSong(newSong)
    master.append(curPlaylist)


# Step through the playlists and download songs
for playlist in master:
    if not quiet:
        print("Grabbing", playlist)
    for song in playlist.songs:
        path = playlist.songPath(song)
        if not os.path.isfile(path): # Skip existing songs
            if showSongs and not quiet:
                print("DL:", path)
            dlSong(song.tid, path)

# Deal with playlists
if m3u:
    for playlist in master:
        fname = playlist.name + ".m3u"
        with open(fname, "w+") as f:
            f.write("#EXTM3U\n")
            for song in playlist.songs:
                meta = "#EXTINF:{},{}".format(song.length, song)
                path = os.path.join(rootPath, playlist.songPath(song))
                f.write(meta + "\n")
                f.write(path + "\n")

if winamp:
    for playlist in master:
        fname = playlist.name + ".pls"
        with open(fname, "w+") as f:
            f.write("[playlist]")
            for i, song in enumerate(playlist.songs):
                path = os.path.join(rootPath, playlist.songPath(song))
                f.write("File{}={}\n".format(i, path))
                f.write("Title{}={}\n".format(i, song.title))
                f.write("Length{}={}\n".format(i, song.length))
            f.write("NumberOfEntries={}".format(len(playlist.songs)))
            f.write("Version=2")

