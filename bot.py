import os
import asyncio
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import discord
from discord.ext import commands
import yt_dlp
import imageio_ffmpeg


# =========================
# OWNER IDS
# =========================

OWNER_IDS = {
    1323235462281957457,
    1294964677419466922,
    1506653600594530374
}


# =========================
# FFMPEG
# =========================

FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()


# =========================
# RENDER WEB SERVER
# =========================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Izuna is online!")

    def log_message(self, format, *args):
        return


def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()


web_thread = threading.Thread(target=run_web_server)
web_thread.daemon = True
web_thread.start()


# =========================
# DISCORD INTENTS
# =========================

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True


# =========================
# BOT
# =========================

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None
)


# =========================
# OWNER ONLY CHECK
# =========================

def owner_only():

    async def predicate(ctx):

        if ctx.author.id in OWNER_IDS:
            return True

        await ctx.send(
            "🛡️ **Izuna is controlled by its owners only.**"
        )

        return False

    return commands.check(predicate)


# =========================
# BOT READY
# =========================

@bot.event
async def on_ready():

    print(f"✅ Izuna is online as {bot.user}")
    print(f"🆔 Bot ID: {bot.user.id}")


# =========================
# JOIN
# =========================

@bot.command()
@owner_only()
async def join(ctx):

    if ctx.author.voice is None:
        await ctx.send(
            "❌ You must join a voice channel first."
        )
        return

    channel = ctx.author.voice.channel

    if ctx.voice_client:
        await ctx.voice_client.move_to(channel)
    else:
        await channel.connect()

    await ctx.send(
        f"🎧 Joined **{channel.name}**"
    )


# =========================
# CONTRO1
# BOOGEYMAN SOUND
# =========================

@bot.command()
@owner_only()
async def contro1(ctx):

    if ctx.author.voice is None:
        await ctx.send(
            "❌ Join a voice channel first."
        )
        return

    channel = ctx.author.voice.channel

    if ctx.voice_client is None:
        voice = await channel.connect()
    else:
        voice = ctx.voice_client

        if voice.channel != channel:
            await voice.move_to(channel)

    base_folder = os.path.dirname(
        os.path.abspath(__file__)
    )

    audio_file = os.path.join(
        base_folder,
        "BOOGEYMAN_extreme_clipped.mp3"
    )

    if not os.path.isfile(audio_file):

        await ctx.send(
            "❌ Audio file not found:\n"
            "`BOOGEYMAN_extreme_clipped.mp3`"
        )
        return

    if voice.is_playing():
        voice.stop()

    try:

        source = discord.FFmpegPCMAudio(
            audio_file,
            executable=FFMPEG_PATH,
            options="-vn"
        )

        def after_playing(error):

            if error:
                print(
                    f"❌ Contro1 audio error: {error}"
                )
            else:
                print(
                    "✅ Contro1 audio finished."
                )

        voice.play(
            source,
            after=after_playing
        )

        await ctx.send(
            "👹 **CONTRO1 SOUND PLAYING...**"
        )

    except Exception as e:

        print(
            f"❌ Contro1 error: {e}"
        )

        await ctx.send(
            "❌ Could not play Contro1 sound."
        )


# =========================
# CONTRO2
# JOINED ULTRA CORRUPTED
# =========================

@bot.command()
@owner_only()
async def contro2(ctx):

    if ctx.author.voice is None:
        await ctx.send(
            "❌ Join a voice channel first."
        )
        return

    channel = ctx.author.voice.channel

    if ctx.voice_client is None:
        voice = await channel.connect()
    else:
        voice = ctx.voice_client

        if voice.channel != channel:
            await voice.move_to(channel)

    base_folder = os.path.dirname(
        os.path.abspath(__file__)
    )

    audio_file = os.path.join(
        base_folder,
        "joined_ultra_corrupted_extreme_harsh_fx.mp3"
    )

    if not os.path.isfile(audio_file):

        await ctx.send(
            "❌ Audio file not found:\n"
            "`joined_ultra_corrupted_extreme_harsh_fx.mp3`"
        )
        return

    if voice.is_playing():
        voice.stop()

    try:

        source = discord.FFmpegPCMAudio(
            audio_file,
            executable=FFMPEG_PATH,
            options="-vn"
        )

        def after_playing(error):

            if error:
                print(
                    f"❌ Contro2 audio error: {error}"
                )
            else:
                print(
                    "✅ Contro2 audio finished."
                )

        voice.play(
            source,
            after=after_playing
        )

        await ctx.send(
            "🔊 **CONTRO2 SOUND PLAYING...**"
        )

    except Exception as e:

        print(
            f"❌ Contro2 error: {e}"
        )

        await ctx.send(
            "❌ Could not play Contro2 sound."
        )


# =========================
# TEST SOUND
# =========================

@bot.command()
@owner_only()
async def testsound(ctx):

    if ctx.author.voice is None:
        await ctx.send(
            "❌ Join a voice channel first."
        )
        return

    channel = ctx.author.voice.channel

    if ctx.voice_client is None:
        voice = await channel.connect()
    else:
        voice = ctx.voice_client

        if voice.channel != channel:
            await voice.move_to(channel)

    if voice.is_playing():
        voice.stop()

    ffmpeg_options = {
        "before_options": "-f lavfi",
        "options": "-f s16le -ar 48000 -ac 2"
    }

    try:

        source = discord.FFmpegPCMAudio(
            "sine=frequency=1000:duration=5",
            executable=FFMPEG_PATH,
            **ffmpeg_options
        )

        voice.play(source)

        await ctx.send(
            "🔊 **Test sound playing for 5 seconds.**"
        )

    except Exception as e:

        print(
            f"❌ Test sound error: {e}"
        )

        await ctx.send(
            "❌ Test sound failed."
        )


# =========================
# PLAY SOUNDCLOUD
# =========================

@bot.command()
@owner_only()
async def play(ctx, *, query=None):

    if query is None:
        await ctx.send(
            "❌ Usage: `!play song name`"
        )
        return

    if ctx.author.voice is None:
        await ctx.send(
            "❌ Join a voice channel first."
        )
        return

    channel = ctx.author.voice.channel

    if ctx.voice_client is None:
        voice = await channel.connect()
    else:
        voice = ctx.voice_client

        if voice.channel != channel:
            await voice.move_to(channel)

    await ctx.send(
        f"🔎 Searching SoundCloud for **{query}**..."
    )

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

            with yt_dlp.YoutubeDL(ydl_options) as ydl:

                return ydl.extract_info(
                    f"scsearch1:{query}",
                    download=False
                )

        info = await loop.run_in_executor(
            None,
            search_soundcloud
        )

        if not info or "entries" not in info:

            await ctx.send(
                "❌ No SoundCloud result found."
            )
            return

        entries = info.get("entries")

        if not entries:

            await ctx.send(
                "❌ No SoundCloud result found."
            )
            return

        track = entries[0]

        audio_url = track.get("url")

        title = track.get(
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

        voice.play(source)

        await ctx.send(
            f"🎵 Now playing: **{title}**"
        )

    except Exception as e:

        print(
            f"❌ SoundCloud error: {e}"
        )

        await ctx.send(
            "❌ Could not play that SoundCloud track."
        )


# =========================
# STOP
# =========================

@bot.command()
@owner_only()
async def stop(ctx):

    if ctx.voice_client is None:

        await ctx.send(
            "❌ Izuna is not in a voice channel."
        )
        return

    if ctx.voice_client.is_playing():

        ctx.voice_client.stop()

        await ctx.send(
            "⏹️ **Stopped.**"
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

    if ctx.voice_client is None:

        await ctx.send(
            "❌ Izuna is not in a voice channel."
        )
        return

    if ctx.voice_client.is_playing():

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

    if ctx.voice_client is None:

        await ctx.send(
            "❌ Izuna is not in a voice channel."
        )
        return

    if ctx.voice_client.is_paused():

        ctx.voice_client.resume()

        await ctx.send(
            "▶️ **Resumed.**"
        )

    else:

        await ctx.send(
            "❌ Nothing is paused."
        )


# =========================
# LEAVE
# =========================

@bot.command()
@owner_only()
async def leave(ctx):

    if ctx.voice_client is None:

        await ctx.send(
            "❌ Izuna is not in a voice channel."
        )
        return

    await ctx.voice_client.disconnect()

    await ctx.send(
        "👋 **Izuna left the voice channel.**"
    )


# =========================
# HELP
# =========================

@bot.command(name="help")
@owner_only()
async def help_command(ctx):

    embed = discord.Embed(
        title="👹 Izuna Commands",
        description="Owner-only Discord bot commands",
        color=discord.Color.dark_red()
    )

    embed.add_field(
        name="🎧 Voice",
        value=(
            "`!join` — Join your voice channel\n"
            "`!contro1` — Play Boogeyman sound\n"
            "`!contro2` — Play second sound\n"
            "`!testsound` — Test audio\n"
            "`!play <song>` — Play SoundCloud\n"
            "`!stop` — Stop audio\n"
            "`!pause` — Pause audio\n"
            "`!resume` — Resume audio\n"
            "`!leave` — Leave voice channel"
        ),
        inline=False
    )

    embed.set_footer(
        text="Izuna • Owner controlled"
    )

    await ctx.send(
        embed=embed
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

    if isinstance(
        error,
        commands.MissingRequiredArgument
    ):

        await ctx.send(
            "❌ Missing command argument."
        )
        return

    print(
        f"❌ Command error: {error}"
    )


# =========================
# START BOT
# =========================

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:

    raise RuntimeError(
        "DISCORD_TOKEN environment variable is missing."
    )

bot.run(TOKEN)
