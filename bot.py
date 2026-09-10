import os
import asyncio
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import discord
from discord.ext import commands
import yt_dlp
import imageio_ffmpeg


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


# =========================
# MODERATOR CHECK
# =========================

def moderator_only():
    return commands.has_permissions(manage_messages=True)


# =========================
# JOIN
# =========================

@bot.command()
@moderator_only()
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

        await ctx.send(f"🔊 Izuna joined **{channel.name}**!")

    except Exception as e:
        print("JOIN ERROR:", repr(e))
        await ctx.send(f"❌ Could not join voice: `{e}`")


# =========================
# PLAY
# =========================

@bot.command()
@moderator_only()
async def play(ctx, *, query=None):

    if not ctx.author.voice:
        await ctx.send("❌ Join a voice channel first.")
        return

    if not query:
        await ctx.send("❌ Use: `!play song name`")
        return

    channel = ctx.author.voice.channel

    # Connect to voice
    try:
        voice = ctx.voice_client

        if voice is None:
            voice = await channel.connect()

        elif voice.channel != channel:
            await voice.move_to(channel)

    except Exception as e:
        print("VOICE ERROR:", repr(e))
        await ctx.send("❌ I couldn't connect to the voice channel.")
        return

    # Stop previous audio
    if voice.is_playing():
        voice.stop()

    await ctx.send(f"🔎 Searching for **{query}**...")

    ydl_options = {
        "format": "bestaudio/best",
        "noplaylist": True,
        "default_search": "ytsearch1",
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": True,
        "source_address": "0.0.0.0",
    }

    try:

        loop = asyncio.get_running_loop()

        def search_youtube():

            with yt_dlp.YoutubeDL(ydl_options) as ydl:

                info = ydl.extract_info(
                    f"ytsearch1:{query}",
                    download=False
                )

                if not info:
                    raise Exception("No result found.")

                if "entries" in info:
                    entries = info["entries"]

                    if not entries:
                        raise Exception("No YouTube result found.")

                    info = entries[0]

                return {
                    "url": info["url"],
                    "title": info.get("title", "Unknown")
                }

        data = await loop.run_in_executor(
            None,
            search_youtube
        )

        audio_url = data["url"]
        title = data["title"]

        print("AUDIO URL FOUND")
        print("TITLE:", title)

        ffmpeg_options = {
            "before_options": (
                "-reconnect 1 "
                "-reconnect_streamed 1 "
                "-reconnect_delay_max 5"
            ),
            "options": "-vn"
        }

        source = discord.FFmpegPCMAudio(
            audio_url,
            executable=FFMPEG_PATH,
            **ffmpeg_options
        )

        def after_play(error):

            if error:
                print("AUDIO PLAY ERROR:", repr(error))

        voice.play(
            source,
            after=after_play
        )

        await ctx.send(
            f"🎵 **Now playing:** {title}"
        )

    except Exception as e:

        print("PLAY ERROR:", repr(e))

        await ctx.send(
            f"❌ Play failed.\n```{str(e)[:1500]}```"
        )


# =========================
# STOP
# =========================

@bot.command()
@moderator_only()
async def stop(ctx):

    if ctx.voice_client and ctx.voice_client.is_playing():

        ctx.voice_client.stop()

        await ctx.send("⏹️ Stopped.")

    else:

        await ctx.send("❌ Nothing is playing.")


# =========================
# PAUSE
# =========================

@bot.command()
@moderator_only()
async def pause(ctx):

    if ctx.voice_client and ctx.voice_client.is_playing():

        ctx.voice_client.pause()

        await ctx.send("⏸️ Paused.")

    else:

        await ctx.send("❌ Nothing is playing.")


# =========================
# RESUME
# =========================

@bot.command()
@moderator_only()
async def resume(ctx):

    if ctx.voice_client and ctx.voice_client.is_paused():

        ctx.voice_client.resume()

        await ctx.send("▶️ Resumed.")

    else:

        await ctx.send("❌ Audio isn't paused.")


# =========================
# LEAVE
# =========================

@bot.command()
@moderator_only()
async def leave(ctx):

    if ctx.voice_client:

        await ctx.voice_client.disconnect()

        await ctx.send("👋 Izuna left the voice channel.")

    else:

        await ctx.send("❌ I'm not in a voice channel.")


# =========================
# ERRORS
# =========================

@bot.event
async def on_command_error(ctx, error):

    if isinstance(error, commands.MissingPermissions):

        await ctx.send(
            "🛡️ **Moderator only.**"
        )

    elif isinstance(error, commands.CommandNotFound):

        pass

    else:

        print(
            "COMMAND ERROR:",
            repr(error)
        )


# =========================
# START
# =========================

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError(
        "DISCORD_TOKEN is not configured."
    )

print("🚀 Starting Izuna...")

bot.run(TOKEN)
