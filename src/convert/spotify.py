"""Convert between Spotify URLs and Song objects.

Copyright (C) 2024  Jacob Humble

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>."""

import sqlite3
import spotipy
import song


class SpotifyConverter(spotipy.Spotify):
    """Converts between songs and URLs."""

    con = sqlite3.connect("../db/songs.db")  # this is relative to the convert pkg
    cur = con.cursor()

    """A converter for Spotify."""

    def __init__(self, client_id: str, client_secret: str):
        auth_manager = spotipy.SpotifyClientCredentials(
            client_id=client_id, client_secret=client_secret
        )
        super().__init__(auth_manager=auth_manager)

    def uri_to_song(self, url: str) -> song.Song:
        """Generate a Song obj from a Spotify track URI.
        Args:
            url (str): Any valid spotify track URI.

        Raises:
            NoMatchFoundError: No match was found for this URL.

        Returns:
            song.Song: Song object containing data on that song.
        """

        # check the db first
        uri = self.__uid_strip(url)
        self.cur.execute("SELECT * FROM spotify WHERE uid=?", [uri])
        track = self.cur.fetchone()
        if track is not None:
            return song.Song(
                source="spotify",
                uid=track[0],
                isrc=track[1],
                title=track[2],
                first_artist=track[3],
            )

        # if db came up empty:
        track = self.track(url)
        if track is not None:
            self.__commit_song(
                track["id"],
                track["external_ids"]["isrc"],
                track["name"],
                track["artists"][0]["name"],
            )

            result_song = song.Song(
                source="spotify",
                uid=track["id"],
                isrc=track["external_ids"]["isrc"],
                title=track["name"],
                first_artist=track["artists"][0]["name"],
                attributes=track,
            )
            return result_song

        raise song.NoMatchFoundError("No match found for this URL.")

    def song_to_url(self, a_song: song.Song) -> tuple[str, str]:
        """Convert a song to its spotify ID and URL.

        Args:
            a_song (song.Song): A song object to search for.

        Raises:
            NoMatchFoundError: No match found for this song.

        Returns:
            tuple[str, str]: Tuple of the Spotify URI and the URL to play the song from.
        """

        # first, check the database for the isrc if we have an isrc
        if a_song.isrc is not None:
            self.cur.execute(
                "SELECT uid FROM spotify WHERE isrc=? limit 1", [a_song.isrc]
            )
            track = self.cur.fetchone()
            if track is not None:
                uid = (track[0],)
                url = f"https://open.spotify.com/track/{uid}"
                return uid, url

            # if nothing was returned from the DB, search Spotify by isrc
            track = self.search(q=f"isrc:{a_song.isrc}", limit=1, type="track")
            if track is not None:
                uid = track["tracks"]["items"][0]["id"]
                url = track["tracks"]["items"][0]["external_urls"]["spotify"]
                title = track["tracks"]["items"][0]["name"]
                first_artist = track["tracks"]["items"][0]["artists"][0]["name"]

                # add the track to the database
                self.__commit_song(uid, a_song.isrc, title, first_artist)
                return uid, url

        # if we failed to find a match, search by name and artist
        track = self.search(
            q=f"track:{a_song.title} artist:{a_song.first_artist}",
            limit=1,
            type="track",
        )
        if track is not None:
            uid = track["tracks"]["items"][0]["id"]
            url = track["tracks"]["items"][0]["external_urls"]["spotify"]
            title = track["tracks"]["items"][0]["name"]
            isrc = track["tracks"]["items"][0]["external_ids"]["isrc"]
            first_artist = track["tracks"]["items"][0]["artists"][0]["name"]

            # only commit exact matches
            if a_song["title"] == title and first_artist == a_song["first_artist"]:
                self.__commit_song(uid, isrc, title, first_artist)
                return uid, url

        # if we never got a match -- raise an exception
        raise song.NoMatchFoundError("No match found for this song.")

    @staticmethod
    def __uid_strip(uid: str) -> str:
        """Strip the Spotify URI to just the ID."""
        if "spotify:track:" in uid:
            return uid.split(":")[-1]
        if "track/" in uid:
            uid = uid.split("/")[-1]
            if "?" in uid:
                return uid.split("?")[0]

        return uid  # assume it's already just the ID

    @classmethod
    def __commit_song(cls, spotify_uid: str, isrc: str, title: str, first_artist: str):
        """Add a song to the database."""
        print(f"Made a commit to spotify: {isrc}")
        cls.cur.execute(
            "INSERT INTO spotify VALUES (?, ?, ?, ?)",
            [spotify_uid, isrc.lower(), title, first_artist],
        )
        cls.con.commit()


# cur.execute("CREATE TABLE spotify(uid, isrc, title, first_artist)")
