```python
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import discord
from discord.ext import commands
import requests


# =========================
# OWNER
# =========================

OWNER_ID = 1323235462281957457


# =========================
# RENDER WEB SERVER
# =========================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Izuna is running!")

    def log_message(self, format, *args):
        pass


def start_web_server():

    port = int(os.environ.get("PORT", 10000))

    server = HTTPServer(
        ("0.0.0.0", port),
        HealthHandler
    )

    print(f"Web server running on port {port}")

    server.serve_forever()


threading.Thread(
    target=start_web_server,
    daemon=True
).start()


# =========================
# DISCORD BOT
# =========================

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None
)


# =========================
# SPOTIFY SETTINGS
# =========================

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_ACCESS_TOKEN = os.getenv("SPOTIFY_ACCESS_TOKEN")


# =========================
# READY
# =========================

@bot.event
async def on_ready():

    print(f"IZUNA ONLINE: {bot.user}")
    print(f"Bot ID: {bot.user.id}")
    print(f"Owner ID: {OWNER_ID}")

    if SPOTIFY_CLIENT_ID:
        print("Spotify Client ID configured.")
    else:
        print("Spotify Client ID missing.")

    if SPOTIFY_ACCESS_TOKEN:
        print("Spotify access token configured.")
    else:
        print("Spotify access token missing.")


# =========================
# OWNER ONLY
# =========================

def owner_only():

    async def predicate(ctx):

        if ctx.author.id == OWNER_ID:
            return True

        await ctx.send(
            "🛡️ **Izuna is controlled by its owner only.**"
        )

        return False

    return commands.check(predicate)


# =========================
# SPOTIFY SEARCH
# =========================

@bot.command()
@owner_only()
async def spotify(ctx, *, query=None):

    if not query:
        await ctx.send(
            "❌ Use: `!spotify song name`"
        )
        return

    if not SPOTIFY_ACCESS_TOKEN:
        await ctx.send(
            "❌ Spotify access token is not configured."
        )
        return

    headers = {
        "Authorization":
            f"Bearer {SPOTIFY_ACCESS_TOKEN}"
    }

    params = {
        "q": query,
        "type": "track",
        "limit": 1
    }

    try:

        response = requests.get(
            "https://api.spotify.com/v1/search",
            headers=headers,
            params=params,
            timeout=15
        )

        if response.status_code != 200:

            await ctx.send(
                f"❌ Spotify search failed: "
                f"`HTTP {response.status_code}`"
            )

            print(
                "SPOTIFY SEARCH ERROR:",
                response.text
            )

            return

        data = response.json()

        tracks = data.get(
            "tracks",
            {}
        ).get(
            "items",
            []
        )

        if not tracks:

            await ctx.send(
                "❌ No Spotify track found."
            )

            return

        track = tracks[0]

        name = track["name"]

        artists = ", ".join(
            artist["name"]
            for artist in track["artists"]
        )

        spotify_url = track["external_urls"]["spotify"]

        await ctx.send(
            "🎵 **Spotify Result**\n\n"
            f"**Song:** {name}\n"
            f"**Artist:** {artists}\n"
            f"🔗 {spotify_url}"
        )

    except Exception as e:

        print(
            "SPOTIFY ERROR:",
            repr(e)
        )

        await ctx.send(
            "❌ Spotify error."
        )


# =========================
# PLAY ON SPOTIFY
# =========================

@bot.command()
@owner_only()
async def spotifyplay(ctx, *, query=None):

    if not query:
        await ctx.send(
            "❌ Use: `!spotifyplay song name`"
        )
        return

    if not SPOTIFY_ACCESS_TOKEN:
        await ctx.send(
            "❌ Spotify access token is not configured."
        )
        return

    headers = {
        "Authorization":
            f"Bearer {SPOTIFY_ACCESS_TOKEN}",
        "Content-Type":
            "application/json"
    }

    # Search
    params = {
        "q": query,
        "type": "track",
        "limit": 1
    }

    try:

        search_response = requests.get(
            "https://api.spotify.com/v1/search",
            headers=headers,
            params=params,
            timeout=15
        )

        if search_response.status_code != 200:

            await ctx.send(
                "❌ Spotify search failed."
            )

            print(
                search_response.text
            )

            return

        data = search_response.json()

        tracks = data.get(
            "tracks",
            {}
        ).get(
            "items",
            []
        )

        if not tracks:

            await ctx.send(
                "❌ Song not found on Spotify."
            )

            return

        track = tracks[0]

        track_uri = track["uri"]

        name = track["name"]

        artists = ", ".join(
            artist["name"]
            for artist in track["artists"]
        )

        spotify_url = track["external_urls"]["spotify"]

        # Start Spotify playback
        play_response = requests.put(
            "https://api.spotify.com/v1/me/player/play",
            headers=headers,
            json={
                "uris": [track_uri]
            },
            timeout=15
        )

        if play_response.status_code == 204:

            await ctx.send(
                "▶️ **Spotify playback started!**\n\n"
                f"🎵 **{name}**\n"
                f"👤 **{artists}**\n"
                f"🔗 {spotify_url}"
            )

        elif play_response.status_code == 403:

            await ctx.send(
                "❌ Spotify requires a Premium account "
                "for playback control."
            )

        elif play_response.status_code == 404:

            await ctx.send(
                "❌ No active Spotify device found.\n\n"
                "Open Spotify on your phone or PC "
                "and start a Spotify device first."
            )

        else:

            await ctx.send(
                f"❌ Spotify playback failed.\n"
                f"HTTP `{play_response.status_code}`"
            )

            print(
                "PLAYBACK ERROR:",
                play_response.text
            )

    except Exception as e:

        print(
            "SPOTIFY PLAY ERROR:",
            repr(e)
        )

        await ctx.send(
            "❌ Spotify playback error."
        )


# =========================
# PAUSE SPOTIFY
# =========================

@bot.command()
@owner_only()
async def spotify_pause(ctx):

    if not SPOTIFY_ACCESS_TOKEN:

        await ctx.send(
            "❌ Spotify access token is missing."
        )

        return

    headers = {
        "Authorization":
            f"Bearer {SPOTIFY_ACCESS_TOKEN}"
    }

    response = requests.put(
        "https://api.spotify.com/v1/me/player/pause",
        headers=headers,
        timeout=15
    )

    if response.status_code == 204:

        await ctx.send(
            "⏸️ Spotify paused."
        )

    else:

        await ctx.send(
            f"❌ Could not pause Spotify. "
            f"HTTP `{response.status_code}`"
        )


# =========================
# RESUME SPOTIFY
# =========================

@bot.command()
@owner_only()
async def spotify_resume(ctx):

    if not SPOTIFY_ACCESS_TOKEN:

        await ctx.send(
            "❌ Spotify access token is missing."
        )

        return

    headers = {
        "Authorization":
            f"Bearer {SPOTIFY_ACCESS_TOKEN}"
    }

    response = requests.put(
        "https://api.spotify.com/v1/me/player/play",
        headers=headers,
        timeout=15
    )

    if response.status_code == 204:

        await ctx.send(
            "▶️ Spotify resumed."
        )

    else:

        await ctx.send(
            f"❌ Could not resume Spotify. "
            f"HTTP `{response.status_code}`"
        )


# =========================
# NEXT SONG
# =========================

@bot.command()
@owner_only()
async def spotify_next(ctx):

    if not SPOTIFY_ACCESS_TOKEN:

        await ctx.send(
            "❌ Spotify access token is missing."
        )

        return

    headers = {
        "Authorization":
            f"Bearer {SPOTIFY_ACCESS_TOKEN}"
    }

    response = requests.post(
        "https://api.spotify.com/v1/me/player/next",
        headers=headers,
        timeout=15
    )

    if response.status_code == 204:

        await ctx.send(
            "⏭️ Skipped to next song."
        )

    else:

        await ctx.send(
            f"❌ Could not skip. "
            f"HTTP `{response.status_code}`"
        )


# =========================
# ERROR HANDLER
# =========================

@bot.event
async def on_command_error(ctx, error):

    if isinstance(
        error,
        commands.CheckFailure
    ):
        return

    if isinstance(
        error,
        commands.CommandNotFound
    ):
        return

    print(
        "COMMAND ERROR:",
        repr(error)
    )


# =========================
# START
# =========================

TOKEN = os.getenv(
    "DISCORD_TOKEN"
)

if not TOKEN:

    raise RuntimeError(
        "DISCORD_TOKEN is not configured."
    )

print(
    "🚀 Starting Izuna..."
)

bot.run(TOKEN)
```
