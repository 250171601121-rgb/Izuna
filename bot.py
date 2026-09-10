import os
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"✅ Izuna is online as {bot.user}")


@bot.command()
async def hello(ctx):
    await ctx.send(f"Hello {ctx.author.mention}! 👋")


@bot.command()
@commands.has_permissions(manage_messages=True)
async def mod(ctx):
    await ctx.send("🛡️ Moderator command activated!")


@bot.command()
async def join(ctx):
    if ctx.author.voice is None:
        await ctx.send("❌ You must join a voice channel first.")
        return

    channel = ctx.author.voice.channel
    await channel.connect()
    await ctx.send(f"🔊 Joined **{channel.name}**!")


@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Left the voice channel.")
    else:
        await ctx.send("❌ I'm not in a voice channel.")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You need moderator permissions to use this command.")


TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN is not configured.")

bot.run(TOKEN)
