import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import discord
from discord.ext import commands
import yt_dlp
import imageio_ffmpeg


# =========================
# SETTINGS
# =========================

OWNER_ID = 1323235462281957457
TOKEN = os.getenv("DISCORD_TOKEN")

FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()


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
# DISCORD
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
# READY
# =========================

@bot.event
async def on_ready():

    print(f"IZUNA ONLINE: {bot.user}")
    print(f"Bot ID: {bot.user.id}")
    print(f"Owner ID: {OWNER_ID}")


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
# JOIN
# =========================

@bot.command()
@owner_only()
async def join(ctx):

    if not ctx.author.voice:

        await ctx.send(
            "❌ Join a voice channel first."
        )

        return

    channel = ctx.author.voice.channel

    if ctx.voice_client:

        await ctx.voice_client.move_to(channel)

    else:

        await channel.connect()

    await ctx.send(
        f"🔊 Joined **{channel.name}**"
    )


# =========================
# PLAY SOUNDCLOUD
# =========================

@bot.command()
@owner_only()
async def play(ctx, *, query=None):

    if not query:

        await ctx.send(
            "❌ Use: `!play song name`"
        )

        return

    if not ctx.author.voice:

        await ctx.send(
            "❌ Join a voice channel first."
        )

        return

    voice = ctx.voice_client

    if not voice:

        voice = await ctx.author.voice.channel.connect()

    if voice.is_playing():

        voice.stop()

    await ctx.send(
        f"🔎 Searching SoundCloud for **{query}**..."
    )

    ydl_opts = {

        "format": "bestaudio/best",

        "noplaylist": True,

        "quiet": True,

        "no_warnings": True,

    }

    try:

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:

            info = ydl.extract_info(
                f"scsearch1:{query}",
                download=False
            )

            if not info.get("entries"):

                await ctx.send(
                    "❌ No SoundCloud track found."
                )

                return

            track = info["entries"][0]

            audio_url = track["url"]

            title = track.get(
                "title",
                "Unknown"
            )

            webpage_url = track.get(
                "webpage_url",
                ""
            )

        ffmpeg_options = {

            "before_options":
                "-reconnect 1 "
                "-reconnect_streamed 1 "
                "-reconnect_delay_max 5",

            "options":
                "-vn"

        }

        source = discord.FFmpegPCMAudio(
            audio_url,
            executable=FFMPEG_PATH,
            **ffmpeg_options
        )

        voice.play(source)

        await ctx.send(
            f"▶️ **Now playing:** {title}\n"
            f"🔗 {webpage_url}"
        )

    except Exception as e:

        print(
            "SOUNDCLOUD PLAY ERROR:",
            repr(e)
        )

        await ctx.send(
            "❌ This SoundCloud track could not be played."
        )


# =========================
# STOP
# =========================

@bot.command()
@owner_only()
async def stop(ctx):

    if ctx.voice_client and ctx.voice_client.is_playing():

        ctx.voice_client.stop()

        await ctx.send(
            "⏹️ Music stopped."
        )

    else:

        await ctx.send(
            "❌ Nothing is playing."
        )


# =========================
# PAUSE
# =========================

@bot.command()
@owner_only()
async def pause(ctx):

    if ctx.voice_client and ctx.voice_client.is_playing():

        ctx.voice_client.pause()

        await ctx.send(
            "⏸️ Music paused."
        )

    else:

        await ctx.send(
            "❌ Nothing is playing."
        )


# =========================
# RESUME
# =========================

@bot.command()
@owner_only()
async def resume(ctx):

    if ctx.voice_client and ctx.voice_client.is_paused():

        ctx.voice_client.resume()

        await ctx.send(
            "▶️ Music resumed."
        )

    else:

        await ctx.send(
            "❌ Music is not paused."
        )


# =========================
# LEAVE
# =========================

@bot.command()
@owner_only()
async def leave(ctx):

    if ctx.voice_client:

        await ctx.voice_client.disconnect()

        await ctx.send(
            "👋 Izuna left the voice channel."
        )

    else:

        await ctx.send(
            "❌ Izuna is not in a voice channel."
        )


# =========================
# ERROR HANDLER
# =========================

@bot.event
async def on_command_error(ctx, error):

    if isinstance(error, commands.CheckFailure):
        return

    if isinstance(error, commands.CommandNotFound):
        return

    print(
        "COMMAND ERROR:",
        repr(error)
    )


# =========================
# START
# =========================

if not TOKEN:

    raise RuntimeError(
        "DISCORD_TOKEN is not configured."
    )

print("🚀 Starting Izuna...")

bot.run(TOKEN)
