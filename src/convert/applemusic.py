"""Convert between Apple Music URLs and Song objects"""

import sqlite3
import applemusicpy
from . import song

class AppleMusicConverter(applemusicpy.AppleMusic):
    """Converts between songs and Apple Music URLs"""
    con = sqlite3.connect("../db/songs.db") # this is relative to the convert pkg
    cur = con.cursor()

    def __init__(self, secret_key, key_id, team_id):
        super().__init__(secret_key, key_id, team_id)

    def url_to_song(self, url: str) -> song.Song:
        raise NotImplementedError

    def song_to_url(self, a_song: song.Song, best_match: bool = False) -> str:

        # first, check the database for the isrc if we have an isrc
        if a_song.isrc is not None:
            self.cur.execute("SELECT songid, albumid FROM applemusic WHERE isrc=? limit 1",
                             [a_song.isrc])
            track = self.cur.fetchone()
            if track is not None:
                songid, albumid = track[0], track[1]
                url = f"https://music.apple.com/us/album/{albumid}?i={songid}"
                return url

            # if nothing was returned from the DB, search apple music by isrc
            track = self.song_by_isrc(a_song.isrc)
            if track is not None:
                self.__commit_song(track)
                return f"https://music.apple.com/us/album/{track['album_id']}?i={track['song_id']}"

        # if we don't have an isrc or failed to match, search by title and artist
        tracks = self.search(f"{a_song.title} {a_song.first_artist}",
                             types=['songs'],
                             limit=5,
                             os='windows') #nb: if on windows...
        for track in tracks:
            data = track.get('results').get('songs').get('data')
            if data is not None:
                data = data[0]
                track_data = self.repack_data(data)
                if a_song.isrc == track_data['isrc']:
                    self.__commit_song(track_data)
                    return f"https://music.apple.com/us/album/{track_data['album_id']}\
                    ?i={track_data['song_id']}"
        else: #pylint: disable=w0120
            if best_match and len(tracks) > 0:
                track_data = self.repack_data(data[0])
                return f"https://music.apple.com/us/album/{track_data['album_id']}?\
                i={track_data['song_id']}"

        # we never found a match, so
        raise song.NoMatchFoundError("No match found for this song.")

    def song_by_isrc(self, isrc: str):
        """Search Apple Music for a song by its ISRC. Returns None if none found."""
        data = None
        track = self.songs_by_isrc([isrc]).get('data').get(0)

        if track is not None:
            data = self.repack_data(track)
        return data

    @staticmethod
    def repack_data(data) -> dict:
        """Pack data section [0 section] of json into a dict."""
        return {
                'song_id' : data['id'],
                'album_id' : data['attributes']['url'].split('/')[-1].split('?i=')[0],
                'isrc' : data['attributes']['isrc'],
                'artist_name' : data['attributes']['artistName'],
                'track_name' : data['attributes']['name']
            }

    @classmethod
    def __commit_song(cls, data: dict):
        """Add a song to the database."""
        cls.cur.execute("INSERT INTO ytmusic(songid, albumid, isrc, title, artist) VALUES (:song_id, :album_id, \
                        :isrc, :track_name, :artist_name) ON CONFLICT(songid, albumid) DO UPDATE SET isrc=:isrc, \
                        title=:track_name, artist=:artist_name", data)
        cls.con.commit()

    @staticmethod
    def __trim_url(url: str) -> str:
        """Strip the URL down to just the unique identifying part, the albumid & songid"""
        return url.split('/')[-1]