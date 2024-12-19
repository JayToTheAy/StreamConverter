"""Setup the database for the application."""
import sqlite3

if __name__ == "__main__":
    con = sqlite3.connect("db/songs.db")
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS spotify (uid TEXT PRIMARY KEY, isrc TEXT, title TEXT, first_artist TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS ytmusic (uid TEXT PRIMARY KEY, isrc TEXT, title TEXT, first_artist TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS applemusic (songid TEXT, albumid TEXT, isrc TEXT, title TEXT, artist TEXT, PRIMARY KEY (songid, albumid)) ")
