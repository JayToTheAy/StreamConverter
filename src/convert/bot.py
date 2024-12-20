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
from enum import Enum
import discord
from discord import app_commands
import spotify
import ytmusic
import applemusic
import song as sng
import config

MY_GUILD = discord.Object(id=config.MY_GUILD_ID)

SERVICES = Enum('Services', [('Spotify', 'spotify'),
                             ('Apple Music', 'applemusic'),
                             ('YT Music', 'ytmusic')
                             ])

class MyClient(discord.Client):
    """Client class"""
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # This copies the global commands over to your guild.
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)
        print(f'Copied globals to guild {MY_GUILD.id}')


# make API objs
sp = spotify.SpotifyConverter(config.SP_CLIENT_ID, config.SP_CLIENT_SCRT)
yt = ytmusic.YTMusicConverter()
am = applemusic.AppleMusicConverter(config.AP_SECRET_KEY, config.AP_KEY_ID, config.AP_TEAM_ID)

# back to discord
intents = discord.Intents.default()
client = MyClient(intents=intents)
tree = client.tree


@client.event
async def on_ready():
    """On-ready event"""
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')

@client.tree.command()
@app_commands.describe(
    service_from = "Service we're converting the song from",
    service_to = "Service we're converting the song to",
    url = "URL of the song",
    best_match = "If we can't find an exact match, should we search for a best match"
)
async def song(
        interaction: discord.Interaction,
        service_from: SERVICES,
        service_to: SERVICES,
        url: str,
        best_match: bool = False
):
    """Find this song on another streaming platform."""
    print("AAAA! AAA! AAA!")
    print(url)
    # convert to song obj
    picked_service = service_from.value if service_from is not None else None
    song_obj = None
    match picked_service:
        case 'spotify':
            print("Spotify")
            song_obj = sp.uri_to_song(url)
        case 'applemusic':
            print("Apple Music")
            song_obj = am.url_to_song(url)
        case 'ytmusic':
            print('YT Music')
            song_obj = yt.url_to_song(url)
        case _:
            raise Exception("No service matched.")
    print(song_obj.title)
    # convert song obj to new service
    picked_service = service_to.value if service_to is not None else None
    url = " "
    match picked_service:
        case 'spotify':
            print("Spotify")
            try:
                url = sp.song_to_url(song_obj)
            except sng.NoMatchFoundError:
                await interaction.response.send_message("No match found.", ephemeral=True)
        case 'applemusic':
            print("Apple Music")
            try:
                url = am.song_to_url(song_obj)
            except sng.NoMatchFoundError:
                await interaction.response.send_message("No match found.", ephemeral=True)
        case 'ytmusic':
            print('YT Music')
            try:
                url = yt.song_to_url(song_obj)
            except sng.NoMatchFoundError:
                await interaction.response.send_message("No match found.", ephemeral=True)
        case _:
            raise Exception("No service matched.")

    print(url)
    if url == " ":
        await interaction.response.send_message("No match found.", ephemeral=True)
    await interaction.response.send_message(url)

@client.tree.command()
async def refresh(interaction: discord.Interaction, guild_id: str = None):
    """Sync command tree for a specified guild, or globally."""
    if interaction.user.id != int(config.OWNER_ID):
        await interaction.response.send_message('You must be the owner to use this command!',
                                                ephemeral=True)
        return

    print(f'Syncing for {guild_id if guild_id is not None else 'Global'}...')
    if guild_id is not None:
        guild = discord.Object(id=guild_id)
        await tree.sync(guild=guild)
    else:
        await tree.sync()

    await interaction.response.send_message("Commands have been synced globally. This may take up to an hour to propagate.",
                                                    ephemeral=True)

if __name__ == "__main__":
    client.run(config.TOKEN)