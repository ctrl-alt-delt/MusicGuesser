import requests
from bs4 import BeautifulSoup
from lxml import etree
import pandas as pd
import sqlite3
from sqlite3 import Error
import os
import time

startyear = 1965
endyear = 2022
yeariter = startyear

def create_connection(path):
    connection = None
    try:
        connection = sqlite3.connect(path)
    except Error as e:
        print(e)

    return connection

def create_song(conn, song):
    sql = "INSERT or IGNORE INTO Billboard(title,artist,album,year,ranking) VALUES(?,?,?,?,?)"
    cur = conn.cursor()
    cur.execute(sql, song)
    conn.commit()
    return cur.lastrowid

connection = create_connection("music.db")

while (yeariter <= endyear):
    wikiurl="https://en.wikipedia.org/wiki/Billboard_Year-End_Hot_100_singles_of_" + str(yeariter)

    tables = pd.read_html(wikiurl)

    if ((yeariter == 2012) or (yeariter == 2013)):
        table = tables[1]
    else:
        table = tables[0]

    print(yeariter)

    table['Title'] = table['Title'].str.replace("\"", '')
    table['Artist(s)'] = table['Artist(s)'].str.replace("\"", '')
    table['Year'] = str(yeariter).replace('\n', '')

    for index, row in table.iterrows():
        if '№' in table:
            ranking = row['№']
        else:
            ranking = row['No.']
        title = row['Title']
        artist = row['Artist(s)']
        album = ""
        year = row['Year']
        enabled = 1

        print(title)
        print(artist)
        print(album)
        print(year)
        print(ranking)
        print('\n')

        song = (title, artist, album, year, ranking)
        rowid = create_song(connection, song)

    yeariter += 1
