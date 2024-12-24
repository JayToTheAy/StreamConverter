"""The bones that make the app-command bot on discord

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
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from os import environ
from enum import Enum
from dotenv import load_dotenv
import discord
from discord import app_commands
import spotify
import ytmusic
import applemusic
import song as sng

# constants
load_dotenv()
DISCORD_TOKEN = environ.get("DISCORD_TOKEN")
print(DISCORD_TOKEN)
OWNER_ID = environ.get("OWNER_ID")
MY_GUILD_ID = environ.get("MY_GUILD_ID")

SP_CLIENT_ID = environ.get("SP_CLIENT_ID")
SP_CLIENT_SCRT = environ.get("SP_CLIENT_SCRT")
SP_REDIRECT_URI = environ.get("SP_REDIRECT_URI")

AP_SECRET_KEY = environ.get("AP_SECRET_KEY")
AP_KEY_ID = environ.get("AP_KEY_ID")
AP_TEAM_ID = environ.get("AP_TEAM_ID")

MY_GUILD = discord.Object(id=MY_GUILD_ID)
# endregion


# region Define Classes
class NoServiceMatchedError(Exception):
    """Exception for when no service is matched."""

    pass


SERVICES = Enum(
    "Services",
    [("Spotify", "spotify"), ("Apple Music", "applemusic"), ("YT Music", "ytmusic")],
)


class MyClient(discord.Client):
    """Client class"""

    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # This copies the global commands over to your guild.
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)
        print(f"Copied globals to guild {MY_GUILD.id}")


# endregion


# make API objs
sp = spotify.SpotifyConverter(SP_CLIENT_ID, SP_CLIENT_SCRT)
yt = ytmusic.YTMusicConverter()
am = applemusic.AppleMusicConverter(AP_SECRET_KEY, AP_KEY_ID, AP_TEAM_ID)

# back to discord
intents = discord.Intents.default()
client = MyClient(intents=intents)
tree = client.tree


@client.event
async def on_ready():
    """On-ready event"""
    print(f"Logged in as {client.user} (ID: {client.user.id})")
    print("------")


# region Song Command
@client.tree.command()
@app_commands.describe(
    service_from="Service we're converting the song from",
    service_to="Service we're converting the song to",
    url="URL of the song",
    best_match="If we can't find an exact match, should we search for a best match",
)
async def song(
    interaction: discord.Interaction,
    service_from: SERVICES,
    service_to: SERVICES,
    url: str,
    best_match: bool = False,
):
    """Find this song on another streaming platform."""
    # this can be a while with network calls, so defer completion to avoid a timeout.
    # we also want to clean up afterwards if it fails, so try/except it so we can
    # remove our follow-up message if we fail, and then raise the exception again.
    await interaction.response.defer(ephemeral=True)
    try:
        # convert to song obj
        print("URL received :", url)
        picked_service = service_from.value if service_from is not None else None
        song_obj = None
        try:
            match picked_service:
                case "spotify":
                    print("From: Spotify")
                    song_obj = sp.uri_to_song(url)
                case "applemusic":
                    print("From: Apple Music")
                    song_obj = am.url_to_song(url)
                case "ytmusic":
                    print("From: YT Music")
                    song_obj = yt.url_to_song(url)
                case _:
                    await interaction.followup.send(
                        "No service matched. Contact the \
                                                    bot owner about how you did this!",
                        ephemeral=True,
                    )
                    raise NoServiceMatchedError("No service matched.")
        except sng.NoMatchFoundError:
            await interaction.followup.send(
                "No match found for this URL!", ephemeral=True
            )

        # convert song obj to new service
        picked_service = service_to.value if service_to is not None else None
        url = " "
        try:
            match picked_service:
                case "spotify":
                    print("To: Spotify")
                    url = sp.song_to_url(song_obj)
                case "applemusic":
                    print("To: Apple Music")
                    url = am.song_to_url(song_obj, best_match=best_match)
                case "ytmusic":
                    print("To: YT Music")
                    url = yt.song_to_url(song_obj, best_match=best_match)
                case _:
                    await interaction.followup.send(
                        "No service matched. Contact the \
                                                    bot owner about how you did this!",
                        ephemeral=True,
                    )
                    raise NoServiceMatchedError("No service matched.")
        except sng.NoMatchFoundError:
            await interaction.followup.send(
                "No match found for this URL!", ephemeral=True
            )

        # send out what url we got
        if url == " ":
            await interaction.followup.send("No match found.", ephemeral=True)
        await interaction.followup.send(url)

    # if we get a generic error, un-promise the followup, then continue raising
    except Exception as e:
        print(f"Error: {e} of class {e.__class__}")
        await interaction.followup.send(
            "An error occurred! Check your inputs.", ephemeral=True
        )
        raise e


# endregion

# region UPC Command

@client.tree.command()
@app_commands.describe(
    upc="Album barcode to search for"
)
async def upc(
    interaction: discord.Interaction,
    upc: int
):
    """Gets the Spotify album corresponding to a UPC.
    This will accept any UPC, from a physical release for example,
    and go off and fetch the corresponding Spotify album."""
    await interaction.response.defer(ephemeral=True)
    try:
        release = sp.get_release_for_barcode(upc)
        digi = sp.get_digital_releases_from_title_and_artist(release['title'],
                                                    release['artists'][0]['name'])
        url = next(sp.find_sp_albums_from_upcs)
        sp.find_sp_albums_from_upcs.close()
        await interaction.followup.send(
            url
        )
    except Exception as e:
        await interaction.followup.send(
            "An error occurred.",
            ephemeral=True
        )
        raise e
# endregion

@client.tree.command()
async def refresh(interaction: discord.Interaction, guild_id: str = None):
    """Sync command tree for a specified guild, or globally."""
    if interaction.user.id != int(OWNER_ID):
        await interaction.response.send_message(
            "You must be the owner to use this command!", ephemeral=True
        )
        return

    print(f"Syncing for {guild_id if guild_id is not None else 'Global'}...")
    if guild_id is not None:
        guild = discord.Object(id=guild_id)
        await tree.sync(guild=guild)
    else:
        await tree.sync()

    await interaction.response.send_message(
        "Commands have been synced globally. \
                                            This may take up to an hour to propagate.",
        ephemeral=True,
    )


if __name__ == "__main__":
    client.run(DISCORD_TOKEN)
