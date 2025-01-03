"""Converts between YTMusic links and Song objects.

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
from ytmusicapi import YTMusic
import musicfetch
import song


class YTMusicConverter(YTMusic):
    """Converts between songs and URLs.
    This can lag due to the latency to the musicfetch API, so when called,
    it should be in a context that can handle a 5 second latency.

    Note: Hits against this can be wrong for a lot of reasons:
    * The content ID that Musicfetch got from YT is wrong.
    * There was no match, so we're matching on title and artist, which can be wrong.
    * The titles and artists given on a YT music are video name and channel, which is...
    inherently kind of wrong. 'Cecily Smith (lyric) by SuperLegitVideos is not ideal.

    Nonetheless, people do want to convert from YTMusic, so..."""

    # TABLE ytmusic(uid, isrc, title, first_artist)
    con = sqlite3.connect("../db/songs.db")  # this is relative to the convert pkg
    cur = con.cursor()

    def __init__(self):
        super().__init__()

    def url_to_song(self, url: str) -> song.Song:
        """Turn a YouTube Music URL into a Song object we can use for searching.

        Args:
            url (str): YTMusic URL

        Raises:
            song.NoMatchFoundError: No match found for this URL

        Returns:
            song.Song: Song obj from the URL
        """
        # check the db first
        uri = self.__strip_url(url)
        self.cur.execute("SELECT * FROM ytmusic WHERE uid=?", [uri])
        track = self.cur.fetchone()
        if track is not None:
            return song.Song(
                source="spotify",
                uid=track[0],
                isrc=track[1],
                title=track[2],
                first_artist=track[3],
            )

        # if db came up empty, query for data on the uri:
        tracks = self.search(uri, limit=1)
        isrc = musicfetch.fetch_isrc(url)  # note: this can miss; if so, returns None
        for track in tracks:
            if track is not None:
                self.__commit_song(
                    track["videoId"], isrc, track["title"], track["artists"][0]["name"]
                )

                return song.Song(
                    source="ytmusic",
                    uid=track["videoId"],
                    isrc=isrc,
                    title=track["title"],
                    first_artist=track["artists"][0]["name"],
                    attributes=track,
                )

        raise song.NoMatchFoundError("No match found for this URL.")

    def song_to_url(self, a_song: song.Song, best_match: bool = False) -> str:
        """Match a song obj to a YouTube Music URL.

        Args:
            a_song (song.Song): Song obj to match against
            best_match (bool, optional): If true, return the best match. Defaults to False.

        Raises:
            song.NoMatchFoundError: No match found for this song.

        Returns:
            str: url to the song we matched with
        """
        # first, check the database for the isrc if we have an isrc
        if a_song.isrc is not None:
            self.cur.execute(
                "SELECT uid FROM ytmusic WHERE isrc=? limit 1", [a_song.isrc]
            )
            track = self.cur.fetchone()
            if track is not None:
                url = f"https://music.youtube.com/watch?v={track[0]}"
                return url

            # if nothing was returned from the DB, search YTMusic by isrc
            tracks = self.search(f"{a_song.isrc}", filter="songs", limit=1)
            for track in tracks:
                if track is not None:
                    # now, false friends exist, so we need to confirm the isrcs match
                    found_isrc = musicfetch.fetch_isrc(
                        f"https://music.youtube.com/watch?v={track['videoId']}"
                    )
                    if found_isrc is not None:
                        if found_isrc.lower() == a_song.isrc.lower():
                            self.__commit_song(
                                track["videoId"],
                                a_song.isrc,
                                track["title"],
                                track["artists"][0]["name"],
                            )
                            return (
                                f"https://music.youtube.com/watch?v={track['videoId']}"
                            )

        # if we don't have an isrc, search by title and artist
        tracks = self.search(
            f"{a_song.title} {a_song.first_artist}", filter="songs", limit=5
        )
        for track in tracks:
            if track is not None:
                uid = track["videoId"]
                isrc = None
                title = track["title"]
                first_artist = track["artists"][0]["name"]
                # check if they're similar, stripping out some stuff like (OFFICIAL VIDEO)
                found_song = song.Song(
                    source="ytmusic",
                    uid=uid,
                    isrc=isrc,
                    title=title,
                    first_artist=first_artist,
                )
                if a_song.is_similar(found_song):
                    isrc = musicfetch.fetch_isrc(
                        f"https://music.youtube.com/watch?v={uid}"
                    )
                    self.__commit_song(uid, isrc, title, first_artist)
                    return f"https://music.youtube.com/watch?v={uid}"
        else:  # pylint: disable=w0120
            if best_match and len(tracks) > 0:
                return f"https://music.youtube.com/watch?v={tracks[0]['videoId']}"

        # we never found a match, so
        raise song.NoMatchFoundError("No match found for this song.")

    @classmethod
    def __commit_song(cls, uid: str, isrc: str, title: str, first_artist: str):
        """Commit a song to the database."""
        data = {
            "uid": uid,
            "isrc": isrc.lower(),
            "title": title,
            "first_artist": first_artist,
        }

        print(f"Made a commit to ytmusic: {isrc}")
        # this is an upsert; sometimes an isrc won't be found so we'll have a null, but later,
        # it gets found as we keep querying musicfetch, so we want to update the record
        cls.cur.execute(
            "INSERT INTO ytmusic(uid, isrc, title, first_artist) VALUES (:uid, :isrc, \
                        :title, :first_artist) ON CONFLICT(uid) DO UPDATE SET isrc=:isrc, \
                        title=:title, first_artist=:first_artist",
            data,
        )
        cls.con.commit()

    @staticmethod
    def __strip_url(url: str) -> str:
        """Strip a URL down to the videoID.

        Args:
            url (str): A YouTube URL.

        Returns:
            str: videoID
        """
        if "/watch?v=" in url:
            url = url.split("/watch?v=")[1]
        if "&" in url:
            url = url.split("&")[0]
        return url
