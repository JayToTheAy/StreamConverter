## What is This?

This is a Discord Bot to convert links from one streaming platform to another. Got a Spotify video you want to share with a friend who uses Apple Music? Just run

> /song Spotify Apple_Music <https://open.spotify.com/track/1s4bn1Oi01ujaWZKL4DaRq?si=9e96edfb82644b17>

and the bot will return the Apple Music url:

> <https://music.apple.com/us/album/1646535908?i=1646536068>

The syntax for the command is /song [platform_from] [platform_to] [url].

Results are cached into a sqlite3 db, to minimize waiting for network calls and to reduce hits against those APIs.

## Parts

Source code is all located under src/. There are really two parts to this project: the Discord bot portion, in bot.py, and the rest, which is a series of platform-specific modules that handle converting a link to an intermediary "song" object, and converting from a song object to a platform's url for that song.

Songs (really, recordings) are equal if their ISRCs are equal, and a match is made if the song is equal or the title and artist are equal. Optionally, a best match can be found on a platform by passing in best_match = True, which grabs the first result from a search of title + artist, regardless of if they match.

## Setup

Setting up the bot requires having a .env file with all the necessary keys (see .example-env; fill out those None fields, and rename it to .env). To use individual convert files, just create a conversion object (i.e. SpotifyConverter) and feed it the necessary keys as parameters.

Run the setup.py folder to generate necessary sqlite db tables, or the bot will scream at you when it can't find those tables.

## Notes
One module is intentionally left out from this code, which is necessary for ytmusic:
* musicfetch.py - I'm unsure if this API is really meant for mass hits, so for now, I'm leaving out my code to slightly ease up on that.
This affects ytmusic.py. You can mock up a musicfetch.py yourself that returns None for all its functions, and things will work without erroring.

Please note that conversions to and from YTMusic are a bit unreliable; YTMusic includes any old video that YTMusic has, including ones that are fan songs with weird titles and from non-artist channels ('Cecily Smith (fan lyric video) - Will Connolly' uploaded by SuperLegitMusicVideos') and may not have an ISRC to search off of, and will be returned by the API with weird fields (from this example, the title will be exactly that of the video, and the artist will be SuperLegitMusicVideos) -- this doesn't make for a great time searching for matches on other platforms.

But, people like using YTMusic, so we try our best.

## License
[Licensed under AGPL v3](https://github.com/JayToTheAy/spotify_convert/blob/main/LICENSE); Copyright Jacob Humble and additional contributors, as present by commit.
