import os
import asyncio
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import discord
from discord.ext import commands
import yt_dlp
import imageio_ffmpeg


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
# BOT SETUP
# =========================

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None
)

FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()


# =========================
# READY
# =========================

@bot.event
async def on_ready():

    print(f"IZUNA ONLINE: {bot.user}")
    print(f"Bot ID: {bot.user.id}")
    print(f"Owner ID: {OWNER_ID}")
    print(f"FFmpeg: {FFMPEG_PATH}")


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
        await ctx.send("❌ Join a voice channel first.")
        return

    channel = ctx.author.voice.channel

    try:

        if ctx.voice_client:
            await ctx.voice_client.move_to(channel)
        else:
            await channel.connect()

        await ctx.send(
            f"🔊 Izuna joined **{channel.name}**!"
        )

    except Exception as e:

        print("JOIN ERROR:", repr(e))

        await ctx.send(
            "❌ Could not join voice."
        )


# =========================
# TEST SOUND
# =========================

@bot.command()
@owner_only()
async def testsound(ctx):

    if not ctx.author.voice:
        await ctx.send("❌ Join a voice channel first.")
        return

    channel = ctx.author.voice.channel

    try:

        voice = ctx.voice_client

        if voice is None:
            voice = await channel.connect()

        elif voice.channel != channel:
            await voice.move_to(channel)

        if voice.is_playing():
            voice.stop()

        await ctx.send(
            "🔊 Testing Izuna audio for 5 seconds..."
        )

        ffmpeg_options = {
            "before_options": "-f lavfi",
            "options": "-f s16le -ar 48000 -ac 2"
        }

        source = discord.FFmpegPCMAudio(
            "sine=frequency=1000:duration=5",
            executable=FFMPEG_PATH,
            **ffmpeg_options
        )

        voice.play(
            source,
            after=lambda error: print(
                "TEST AUDIO ERROR:",
                repr(error)
            ) if error else print(
                "TEST AUDIO FINISHED"
            )
        )

        await ctx.send(
            "✅ Test sound started."
        )

    except Exception as e:

        print(
            "TEST SOUND ERROR:",
            repr(e)
        )

        await ctx.send(
            f"❌ Test failed:\n```{str(e)[:1000]}```"
        )


# =========================
# PLAY
# =========================

@bot.command()
@owner_only()
async def play(ctx, *, query=None):

    if not ctx.author.voice:
        await ctx.send(
            "❌ Join a voice channel first."
        )
        return

    if not query:
        await ctx.send(
            "❌ Use: `!play song name`"
        )
        return

    channel = ctx.author.voice.channel

    # =========================
    # CONNECT
    # =========================

    try:

        voice = ctx.voice_client

        if voice is None:
            voice = await channel.connect()

        elif voice.channel != channel:
            await voice.move_to(channel)

    except Exception as e:

        print(
            "VOICE ERROR:",
            repr(e)
        )

        await ctx.send(
            "❌ I couldn't connect to the voice channel."
        )

        return

    # =========================
    # STOP OLD AUDIO
    # =========================

    if voice.is_playing():
        voice.stop()

    await ctx.send(
        f"🔎 Searching SoundCloud for **{query}**..."
    )

    # =========================
    # YT-DLP
    # =========================

    ydl_options = {
        "format": "bestaudio/best",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": True,
        "source_address": "0.0.0.0"
    }

    try:

        loop = asyncio.get_running_loop()

        def search_soundcloud():

            with yt_dlp.YoutubeDL(
                ydl_options
            ) as ydl:

                info = ydl.extract_info(
                    f"scsearch1:{query}",
                    download=False
                )

                if not info:
                    raise Exception(
                        "No SoundCloud result found."
                    )

                if "entries" in info:

                    entries = info["entries"]

                    if not entries:
                        raise Exception(
                            "No SoundCloud result found."
                        )

                    info = entries[0]

                audio_url = info.get("url")

                if not audio_url:
                    raise Exception(
                        "No playable audio URL found."
                    )

                return {
                    "url": audio_url,
                    "title": info.get(
                        "title",
                        "Unknown"
                    )
                }

        data = await loop.run_in_executor(
            None,
            search_soundcloud
        )

        audio_url = data["url"]
        title = data["title"]

        print(
            "AUDIO URL FOUND"
        )

        print(
            "TITLE:",
            title
        )

        # =========================
        # FFMPEG AUDIO CONVERSION
        # =========================

        ffmpeg_options = {
            "before_options": (
                "-reconnect 1 "
                "-reconnect_streamed 1 "
                "-reconnect_delay_max 5"
            ),
            "options": (
                "-vn "
                "-f s16le "
                "-ar 48000 "
                "-ac 2"
            )
        }

        source = discord.FFmpegPCMAudio(
            audio_url,
            executable=FFMPEG_PATH,
            **ffmpeg_options
        )

        # =========================
        # CALLBACK
        # =========================

        def after_play(error):

            if error:

                print(
                    "AUDIO PLAY ERROR:",
                    repr(error)
                )

            else:

                print(
                    "AUDIO FINISHED"
                )

        # =========================
        # PLAY
        # =========================

        voice.play(
            source,
            after=after_play
        )

        await ctx.send(
            f"🎵 **Now playing:** {title}"
        )

    except Exception as e:

        print(
            "PLAY ERROR:",
            repr(e)
        )

        await ctx.send(
            "❌ **Play failed.**\n"
            f"```{str(e)[:1500]}```"
        )


# =========================
# STOP
# =========================

@bot.command()
@owner_only()
async def stop(ctx):

    if (
        ctx.voice_client
        and ctx.voice_client.is_playing()
    ):

        ctx.voice_client.stop()

        await ctx.send("⏹️ Stopped.")

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

    if (
        ctx.voice_client
        and ctx.voice_client.is_playing()
    ):

        ctx.voice_client.pause()

        await ctx.send("⏸️ Paused.")

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

    if (
        ctx.voice_client
        and ctx.voice_client.is_paused()
    ):

        ctx.voice_client.resume()

        await ctx.send("▶️ Resumed.")

    else:

        await ctx.send(
            "❌ Audio isn't paused."
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
            "❌ I'm not in a voice channel."
        )


# =========================
# ERRORS
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
