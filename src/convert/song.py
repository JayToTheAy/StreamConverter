"""Define a song."""

import re

class NoMatchFoundError(Exception):
    """Exception for when no match is found."""
    pass

class Song():
    """A song."""
    def __init__(self, source: str, uid: str, isrc: str, title: str, first_artist: str, attributes = None):
        self.source = source
        self.uid = uid
        self.isrc = (isrc.lower() if isinstance(isrc, str) else isrc)
        self.title = title
        self.first_artist = first_artist
        self.attributes = attributes

    def __eq__(self, other):
        if not isinstance(other, Song):
            return False

        return self.isrc.lower() == other.isrc.lower()

    def is_similar(self, other):
        """Returns true if the songs are similar."""
        our_filter = r"\({0,1}(official){0,1}( ){0,1}(music|lyric){1}( ){0,1}(video)\){0,1}"
        self_title = re.sub(our_filter, '', self.title, flags=re.I)
        other_title = re.sub(our_filter, '', other.title, flags=re.I)
        return self_title == other_title and self.first_artist == other.first_artist
