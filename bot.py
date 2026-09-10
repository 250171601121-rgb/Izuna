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
# SPOTIFY
# =========================

SPOTIFY_ACCESS_TOKEN = os.getenv(
    "SPOTIFY_ACCESS_TOKEN"
)


# =========================
# READY
# =========================

@bot.event
async def on_ready():

    print(f"IZUNA ONLINE: {bot.user}")
    print(f"Bot ID: {bot.user.id}")
    print(f"Owner ID: {OWNER_ID}")

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

            print(
                "SPOTIFY SEARCH ERROR:",
                response.text
            )

            await ctx.send(
                f"❌ Spotify search failed "
                f"({response.status_code})."
            )

            return

        data = response.json()

        tracks = (
            data
            .get("tracks", {})
            .get("items", [])
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

        spotify_url = (
            track["external_urls"]["spotify"]
        )

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
            "❌ Spotify error occurred."
        )


# =========================
# SPOTIFY PLAY
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

    params = {
        "q": query,
        "type": "track",
        "limit": 1
    }

    try:

        # Search Spotify
        search_response = requests.get(
            "https://api.spotify.com/v1/search",
            headers=headers,
            params=params,
            timeout=15
        )

        if search_response.status_code != 200:

            print(
                "SPOTIFY SEARCH ERROR:",
                search_response.text
            )

            await ctx.send(
                "❌ Spotify search failed."
            )

            return

        data = search_response.json()

        tracks = (
            data
            .get("tracks", {})
            .get("items", [])
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

        spotify_url = (
            track["external_urls"]["spotify"]
        )

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
                "❌ Spotify Premium is required "
                "for playback control."
            )

        elif play_response.status_code == 404:

            await ctx.send(
                "❌ No active Spotify device found.\n"
                "Open Spotify and select a device first."
            )

        else:

            print(
                "SPOTIFY PLAYBACK ERROR:",
                play_response.text
            )

            await ctx.send(
                f"❌ Spotify playback failed "
                f"({play_response.status_code})."
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
# PAUSE
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

    try:

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
                f"❌ Could not pause Spotify "
                f"({response.status_code})."
            )

    except Exception as e:

        print(
            "PAUSE ERROR:",
            repr(e)
        )

        await ctx.send(
            "❌ Spotify pause error."
        )


# =========================
# RESUME
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

    try:

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
                f"❌ Could not resume Spotify "
                f"({response.status_code})."
            )

    except Exception as e:

        print(
            "RESUME ERROR:",
            repr(e)
        )

        await ctx.send(
            "❌ Spotify resume error."
        )


# =========================
# NEXT
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

    try:

        response = requests.post(
            "https://api.spotify.com/v1/me/player/next",
            headers=headers,
            timeout=15
        )

        if response.status_code == 204:

            await ctx.send(
                "⏭️ Next Spotify song."
            )

        else:

            await ctx.send(
                f"❌ Could not skip "
                f"({response.status_code})."
            )

    except Exception as e:

        print(
            "NEXT ERROR:",
            repr(e)
        )

        await ctx.send(
            "❌ Spotify next-song error."
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
# START BOT
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
