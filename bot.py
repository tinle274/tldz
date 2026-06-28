import discord
from discord.ext import commands
from discord import app_commands
import os
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("discord_bot")

TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = os.getenv("BOT_PREFIX", "!")

intents = discord.Intents.default()
# Privileged intents — enable in Discord Dev Portal → Bot → Privileged Gateway Intents
# then uncomment:
# intents.message_content = True   # needed for prefix commands to read message text
# intents.members = True            # needed for member join/leave events and role info

bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)


@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
    logger.info(f"Connected to {len(bot.guilds)} guild(s)")

    try:
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} slash command(s) globally")
    except Exception as e:
        logger.error(f"Failed to sync slash commands: {e}")

    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening,
            name="/help",
        )
    )


@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Missing argument: `{error.param.name}`. Use `{PREFIX}help {ctx.command}` for usage.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to use this command.")
    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.send("I don't have the required permissions to do that.")
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"This command is on cooldown. Try again in {error.retry_after:.1f}s.")
    else:
        logger.error(f"Unhandled error in command '{ctx.command}': {error}", exc_info=error)
        await ctx.send("An unexpected error occurred.")


@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
    elif isinstance(error, app_commands.BotMissingPermissions):
        await interaction.response.send_message("I don't have the required permissions to do that.", ephemeral=True)
    elif isinstance(error, app_commands.CommandOnCooldown):
        await interaction.response.send_message(
            f"This command is on cooldown. Try again in {error.retry_after:.1f}s.", ephemeral=True
        )
    else:
        logger.error(f"Unhandled slash command error: {error}", exc_info=error)
        if not interaction.response.is_done():
            await interaction.response.send_message("An unexpected error occurred.", ephemeral=True)


async def load_cogs():
    cogs_dir = os.path.join(os.path.dirname(__file__), "cogs")
    for filename in sorted(os.listdir(cogs_dir)):
        if filename.endswith(".py") and not filename.startswith("_"):
            cog = f"cogs.{filename[:-3]}"
            try:
                await bot.load_extension(cog)
                logger.info(f"Loaded cog: {cog}")
            except Exception as e:
                logger.error(f"Failed to load cog {cog}: {e}")


async def main():
    if not TOKEN:
        raise ValueError(
            "DISCORD_TOKEN is not set. Add it to your .env file or Replit Secrets."
        )
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
