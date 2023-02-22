# Import libraries
import os
import sys
import json
import spotipy
import sqlite3
from sqlite3 import Error
import random
import pyttsx3
import time
import webbrowser
import spotipy.util as util
from json.decoder import JSONDecodeError

####################
# DATABASE INDEXES #
####################
db_title_idx      = 0
db_artist_idx     = 1
db_album_idx      = 2
db_year_idx       = 3
db_popularity_idx = 4
db_id_idx         = 5

###########
# Globals #
###########
played_songs_file_name = "played_songs.txt"
MAX_PLAYED_SONGS       = 50
played_songs           = []
deviceID               = 0
popularity_cutoff      = 60
num_rounds             = 15
start_playing_offset   = 5
song_play_length       = 10
min_year               = 1960
max_year               = 2023
engine                 = pyttsx3.init()
engine.setProperty('rate', 170)

#########################################
# function: create_connection()         #
#                                       #
# Creates a connection to the database. #
#########################################
def create_connection(path):
    connection = None
    try:
        connection = sqlite3.connect(path)
    except Error as e:
        print(e)

    return connection

conn = create_connection("music.db")

#########################################
# function: get_random_song_from_year() #
#                                       #
# Queries the database for a song in    #
# the given year and above the given    #
# popularity value.                     #
#########################################
def get_random_song_from_year(year):
    cur = conn.cursor()
    cur.execute("SELECT *  FROM General WHERE Year=? AND Popularity >= ? ORDER BY RANDOM() LIMIT 1", (year,popularity_cutoff,))
    rows = cur.fetchall()
    return rows[0]

#########################################
# function: login_to_spoity()           #
#                                       #
# Gets a Spotify API token.             #
#########################################
def login_to_spotify():
    username = "MusicGame"
    scope = 'user-read-private user-read-playback-state user-modify-playback-state'

    try:
        token = util.prompt_for_user_token(username, scope)
    except (AttributeError, JSONDecodeError):
        os.remove(f".cache-{username}")
        token = util.prompt_for_user_token(username, scope)

    spotify_object = spotipy.Spotify(auth=token)

    return spotify_object

#########################################
# function: get_device_id()             #
#                                       #
# Gets the Spotify device ID.           #
#########################################
def get_device_id(spotify_object):
    devices = spotify_object.devices()
    deviceID = devices['devices'][0]['id']

    return deviceID

#########################################
# function: display_song_info()         #
#                                       #
# Displays the song info for the given  #
# song.                                 #
#########################################
def display_song_info(song_to_play, show_year):
    print("Title: " + song_to_play[db_title_idx])
    print("Artist: " + song_to_play[db_artist_idx])
    print("Album: " + song_to_play[db_album_idx])
    if (show_year):
        print("Year: " + str(song_to_play[db_year_idx]))
    engine.say("That song was " + song_to_play[db_title_idx] + " by " + song_to_play[db_artist_idx])
    engine.runAndWait();

    print()

#########################################
# function: write_played_songs_file()   #
#                                       #
# Writes the list of played songs to    #
# the file.                             #
#########################################
def write_played_songs_file():
    f = open (played_songs_file_name, "a")
    for id in played_songs:
        f.write(id)
        f.write("\n")
    f.close()

#########################################
# function: read_played_songs_file()    #
#                                       #
# Reads in the list of played songs.    #
#########################################
def read_played_songs_file():
    if os.path.isfile(played_songs_file_name):
        with open(played_songs_file_name) as fp:
            line = fp.readline().strip()
            while line:
                played_songs.append(line)
                line = fp.readline().strip()
    else:
        with open(played_songs_file_name, "w+"):
            pass

#########################################
# function: main_menu()                 #
#                                       #
# Displays the main menu of the game.   #
#########################################
def main_menu(spotify_object):
    game_selection = ""

    while (game_selection !=  "9"):
        print("-------------------")
        print("(1) Guess Year From Songs")
        print("(2) Guess Songs in Range")
        print("(9) Quit")
        print("-------------------")

        game_selection = input("> ")

        if (game_selection == "1"):
            guess_year_from_songs(spotify_object)
        if (game_selection == "2"):
            guess_songs_in_range(spotify_object)
        elif (game_selection == "9"):
            write_played_songs_file()
            print("See ya.")
        else:
            print("Not supported.")

#########################################
# function: announce_song_number()      #
#                                       #
# Announces the song/round number.      #
#########################################
def announce_song_number(count, total):
    if ((count+1) == total):
        print(str("Last Song"))
        engine.say("Last Song")
    else:
        print(str("Song #" + str(count+1)))
        engine.say("Song Number " + str(count+1))

    engine.runAndWait()

#########################################
# function: announce_year_answer()      #
#                                       #
# Announces the year.                   #
#########################################
def announce_year_answer(year):
    print("The year was...")
    engine.say("The year was")
    engine.runAndWait()
    time.sleep(.5)
    print(str(year))
    engine.say(str(year))
    engine.runAndWait()

#########################################
# function: announce_year_answer()      #
#                                       #
# Plays the given song using Spotify.   #
# Begins at the given start point and   #
# plays for the given length.           #
#########################################
def play_song(song_id, song_start_point, song_play_length):
    playlist = []
    playlist.append(song_id[db_id_idx])
    spotify_object.start_playback(device_id, None, playlist, None, song_start_point)
    time.sleep(start_playing_offset + song_play_length)
    spotify_object.pause_playback(deviceID)
    time.sleep(1)

#########################################
# function: guess_year_from_songs()     #
#                                       #
# Game mode where you guess the year    #
# from X numbers of songs played from   #
# that year.                            #
#########################################
def guess_year_from_songs(spotify_object):
    round_count = 0
    played_artists = []
    played_albums = []

    input_min_year = int(input("Min Year? "))
    while (input_min_year < min_year):
        print("Out of range.")
        input_min_year = int(input("Min Year? "))

    input_max_year = int(input("Max Year? "))
    while (input_max_year > max_year):
        print("Out of range.")
        input_max_year = int(input("Max Year? "))

    print()

    rand_year = random.randint(input_min_year, input_max_year)

    while round_count < num_rounds:
        announce_song_number(round_count, num_rounds)

        song_start_point     = random.randrange(30000, 90000)
        song_to_play = get_random_song_from_year(rand_year)

        while (song_to_play[db_id_idx] in played_songs or
               song_to_play[db_artist_idx] in played_artists or
               song_to_play[db_album_idx] in played_albums):
            song_to_play = get_random_song_from_year(rand_year)

        play_song(song_to_play, song_start_point, song_play_length)

        display_song_info(song_to_play, False)

        round_count += 1

        if (len(played_songs) == MAX_PLAYED_SONGS):
            played_songs.pop(0)

        played_songs.append(song_to_play[db_id_idx])
        played_artists.append(song_to_play[db_artist_idx])
        played_albums.append(song_to_play[db_album_idx])

    announce_year_answer(rand_year)

#########################################
# function: guess_songs_in_range()      #
#                                       #
# Game mode where you guess X number    #
# of songs in the given year range.     #
#########################################
def guess_songs_in_range(spotify_object):
    round_count = 0

    input_min_year = int(input("Min Year? "))
    while (input_min_year < min_year):
        print("Out of range.")
        input_min_year = int(input("Min Year? "))

    input_max_year = int(input("Max Year? "))
    while (input_max_year > max_year):
        print("Out of range.")
        input_max_year = int(input("Max Year? "))

    print()

    while round_count < num_rounds:

        rand_year = random.randint(input_min_year, input_max_year)

        announce_song_number(round_count, num_rounds)

        song_start_point     = random.randrange(30000, 90000)
        song_to_play = get_random_song_from_year(rand_year)

        while (song_to_play[db_id_idx] in played_songs):
            song_to_play = get_random_song_from_year(rand_year)

        play_song(song_to_play, song_start_point, song_play_length)

        display_song_info(song_to_play, True)

        round_count += 1

        if (len(played_songs) == MAX_PLAYED_SONGS):
            played_songs.pop(0)

        played_songs.append(song_to_play[db_id_idx])

########
# MAIN #
########
read_played_songs_file()
spotify_object = login_to_spotify()
device_id = get_device_id(spotify_object)
main_menu(spotify_object)
