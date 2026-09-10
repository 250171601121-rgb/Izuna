import os
import asyncio

import discord
from discord.ext import commands
import yt_dlp
import imageio_ffmpeg


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
# BOT READY
# =========================

@bot.event
async def on_ready():
    print(f"✅ Izuna is online as {bot.user}")
    print(f"🆔 Bot ID: {bot.user.id}")


# =========================
# MODERATOR CHECK
# =========================

def moderator_only():
    return commands.has_permissions(manage_messages=True)


# =========================
# JOIN VOICE
# =========================

@bot.command()
@moderator_only()
async def join(ctx):

    if ctx.author.voice is None:
        await ctx.send("❌ Join a voice channel first.")
        return

    channel = ctx.author.voice.channel

    if ctx.voice_client:
        await ctx.voice_client.move_to(channel)
    else:
        await channel.connect()

    await ctx.send(f"🔊 Joined **{channel.name}**!")


# =========================
# PLAY MUSIC / SOUND
# =========================

@bot.command()
@moderator_only()
async def play(ctx, *, query=None):

    if ctx.author.voice is None:
        await ctx.send("❌ Join a voice channel first.")
        return

    if query is None:
        await ctx.send("❌ Use: `!play song name or YouTube URL`")
        return

    voice = ctx.voice_client

    if voice is None:
        voice = await ctx.author.voice.channel.connect()

    elif voice.channel != ctx.author.voice.channel:
        await voice.move_to(ctx.author.voice.channel)

    # Stop currently playing audio
    if voice.is_playing():
        voice.stop()

    await ctx.send(f"🔎 Searching for **{query}**...")

    ydl_options = {
        "format": "bestaudio/best",
        "noplaylist": True,
        "default_search": "ytsearch1",
        "quiet": True,
        "no_warnings": True,
    }

    try:

        loop = asyncio.get_running_loop()

        def get_audio():
            with yt_dlp.YoutubeDL(ydl_options) as ydl:
                info = ydl.extract_info(query, download=False)

                if "entries" in info:
                    info = info["entries"][0]

                return info

        info = await loop.run_in_executor(None, get_audio)

        audio_url = info["url"]
        title = info.get("title", "Unknown")

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

        await ctx.send(f"🎵 Now playing: **{title}**")

    except Exception as e:
        print(f"PLAY ERROR: {e}")
        await ctx.send("❌ I couldn't play that audio.")


# =========================
# STOP
# =========================

@bot.command()
@moderator_only()
async def stop(ctx):

    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏹️ Stopped the audio.")
    else:
        await ctx.send("❌ Nothing is playing.")


# =========================
# LEAVE VOICE
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
# COMMAND ERROR
# =========================

@bot.event
async def on_command_error(ctx, error):

    if isinstance(error, commands.MissingPermissions):
        await ctx.send(
            "🛡️ **Moderator only.** "
            "You don't have permission to use this command."
        )

    elif isinstance(error, commands.CommandNotFound):
        pass

    else:
        print(f"ERROR: {error}")


# =========================
# START BOT
# =========================

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError("❌ DISCORD_TOKEN is not configured.")

bot.run(TOKEN)
