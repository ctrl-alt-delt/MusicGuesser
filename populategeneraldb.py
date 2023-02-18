# Import libraries
import os
import sys
import json
import spotipy
import random
import pyttsx3
import sqlite3
from sqlite3 import Error
import time
import webbrowser
import spotipy.util as util
from json.decoder import JSONDecodeError

def create_connection(path):
    connection = None
    try:
        connection = sqlite3.connect(path)
    except Error as e:
        print(e)

    return connection

def create_song(conn, song):
    sql = "INSERT or IGNORE INTO General(title,artist,album,year,popularity,id) VALUES(?,?,?,?,?,?)"
    cur = conn.cursor()
    cur.execute(sql, song)
    conn.commit()
    return cur.lastrowid

def get_playlist_id(spotifyObject, year):
    # Search for the Playlist
    results = spotifyObject.search(q='Top Hits of ' + str(year), limit=1, type='playlist')

    return results['playlists']['items'][0]['id']

def login_to_spotify():
    username = "MusicGame"
    scope = 'user-read-private user-read-playback-state user-modify-playback-state'

    try:
        token = util.prompt_for_user_token(username, scope)
    except (AttributeError, JSONDecodeError):
        os.remove(f".cache-{username}")
        token = util.prompt_for_user_token(username, scope)

    # Create Spotify object
    spotifyObject = spotipy.Spotify(auth=token)

    return spotifyObject

########
# MAIN #
########
connection = create_connection("music.db")
spotifyObject = login_to_spotify()

min_year = 1960
max_year = 2023

for playlist_year in range(min_year, max_year):
    print(str(playlist_year) + "/" + str(max_year-1))

    id = get_playlist_id(spotifyObject, playlist_year)
    results = spotifyObject.user_playlist_tracks('spotify', id)
    for song in results['items']:
        song = ( song['track']['name'],
                 song['track']['album']['artists'][0]['name'],
                 song['track']['album']['name'],
                 song['track']['album']['release_date'].split("-")[0],
                 song['track']['popularity'],
                 song['track']['uri'])
        rowid = create_song(connection, song)
