import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import discord
from discord.ext import commands
import yt_dlp
import imageio_ffmpeg


# =========================
# IZUNA CONFIG
# =========================

OWNER_ID = {
    1323235462281957457,
    1294964677419466922
}

FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()

AUDIO_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "audio",
    "boogeyman.kx4.dark.audio.mp3"
)


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
# DISCORD INTENTS
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
# BOT READY
# =========================

@bot.event
async def on_ready():

    print(f"IZUNA ONLINE: {bot.user}")
    print(f"Bot ID: {bot.user.id}")
    print(f"Owner ID: {OWNER_ID}")
    print(f"FFmpeg: {FFMPEG_PATH}")
    print(f"Audio file: {AUDIO_FILE}")

    if os.path.exists(AUDIO_FILE):
        print("Audio file found!")
    else:
        print("WARNING: Audio file NOT found!")


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
# JOIN VOICE
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
# TEST LOCAL AUDIO
# =========================

@bot.command()
@owner_only()
async def testsound(ctx):

    if not ctx.author.voice:

        await ctx.send(
            "❌ Join a voice channel first."
        )

        return

    channel = ctx.author.voice.channel

    try:

        # Connect to voice
        if ctx.voice_client:

            voice = ctx.voice_client

            if voice.channel != channel:
                await voice.move_to(channel)

        else:

            voice = await channel.connect()


        # Check audio file
        if not os.path.exists(AUDIO_FILE):

            await ctx.send(
                "❌ Audio file not found on the server."
            )

            print(
                "Missing audio file:",
                AUDIO_FILE
            )

            return


        # Stop previous audio
        if voice.is_playing():

            voice.stop()


        # FFmpeg options
        ffmpeg_options = {
            "options": "-vn"
        }


        # Play MP3
        source = discord.FFmpegPCMAudio(
            AUDIO_FILE,
            executable=FFMPEG_PATH,
            **ffmpeg_options
        )


        voice.play(
            source,
            after=lambda error: print(
                f"Audio finished. Error: {error}"
            )
        )


        await ctx.send(
            "🔊 **Izuna is playing the audio!**"
        )


    except Exception as e:

        print(
            "TESTSOUND ERROR:",
            repr(e)
        )

        await ctx.send(
            "❌ Could not play the audio."
        )


# =========================
# PLAY SOUNDCLOUD
# =========================

@bot.command()
@owner_only()
async def play(ctx, *, query=None):

    if not query:

        await ctx.send(
            "❌ Usage: `!play <song name>`"
        )

        return


    if not ctx.author.voice:

        await ctx.send(
            "❌ Join a voice channel first."
        )

        return


    channel = ctx.author.voice.channel


    try:

        if ctx.voice_client:

            voice = ctx.voice_client

            if voice.channel != channel:
                await voice.move_to(channel)

        else:

            voice = await channel.connect()


        await ctx.send(
            f"🔎 Searching SoundCloud for **{query}**..."
        )


        ydl_options = {
            "format": "bestaudio/best",
            "noplaylist": True,
            "quiet": True,
            "default_search": "scsearch1"
        }


        with yt_dlp.YoutubeDL(ydl_options) as ydl:

            info = ydl.extract_info(
                f"scsearch1:{query}",
                download=False
            )


        if not info:

            await ctx.send(
                "❌ Nothing found."
            )

            return


        if "entries" in info:

            entries = info.get("entries")

            if not entries:

                await ctx.send(
                    "❌ Nothing found."
                )

                return

            info = entries[0]


        audio_url = info.get("url")
        title = info.get(
            "title",
            "Unknown track"
        )


        if not audio_url:

            await ctx.send(
                "❌ Could not get the audio stream."
            )

            return


        if voice.is_playing():

            voice.stop()


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


        voice.play(
            source,
            after=lambda error: print(
                f"SoundCloud finished. Error: {error}"
            )
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
            "❌ Could not play that SoundCloud track."
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
            "⏸️ **Paused.**"
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
            "▶️ **Resumed.**"
        )

    else:

        await ctx.send(
            "❌ Nothing is paused."
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
            "⏹️ **Stopped.**"
        )

    else:

        await ctx.send(
            "❌ Nothing is playing."
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
            "👋 **Izuna left the voice channel.**"
        )

    else:

        await ctx.send(
            "❌ Izuna isn't in a voice channel."
        )


# =========================
# HELP
# =========================

@bot.command()
@owner_only()
async def help(ctx):

    embed = discord.Embed(
        title="🎵 Izuna Commands",
        description="Owner-only music controls",
        color=discord.Color.blurple()
    )

    embed.add_field(
        name="🔊 Voice",
        value=(
            "`!join` — Join your voice channel\n"
            "`!leave` — Leave voice channel"
        ),
        inline=False
    )

    embed.add_field(
        name="🎵 Music",
        value=(
            "`!testsound` — Play Izuna's local audio\n"
            "`!play <song>` — Search SoundCloud\n"
            "`!pause` — Pause\n"
            "`!resume` — Resume\n"
            "`!stop` — Stop"
        ),
        inline=False
    )

    await ctx.send(embed=embed)


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

TOKEN = os.environ.get("DISCORD_TOKEN")

if not TOKEN:

    raise RuntimeError(
        "DISCORD_TOKEN environment variable is missing."
    )


bot.run(TOKEN)
