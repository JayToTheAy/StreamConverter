"""Define a song.

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

import re


class NoMatchFoundError(Exception):
    """Exception for when no match is found."""

    pass


class Song:
    """A song."""

    def __init__(
        self,
        source: str,
        uid: str,
        isrc: str,
        title: str,
        first_artist: str,
        attributes=None,
    ):
        self.source = source
        self.uid = uid
        self.isrc = isrc.lower() if isinstance(isrc, str) else isrc
        self.title = title
        self.first_artist = first_artist
        self.attributes = attributes

    def __eq__(self, other):
        if not isinstance(other, Song):
            return False

        return self.isrc.lower() == other.isrc.lower()

    def is_similar(self, other):
        """Returns true if the songs are similar."""
        our_filter = (
            r"\({0,1}(official){0,1}( ){0,1}(music|lyric){1}( ){0,1}(video)\){0,1}"
        )
        self_title = re.sub(our_filter, "", self.title, flags=re.I)
        other_title = re.sub(our_filter, "", other.title, flags=re.I)
        return self_title == other_title and self.first_artist == other.first_artist
