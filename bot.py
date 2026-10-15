import logging
import discord
from discord.ext import commands
from config import settings

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("nexus")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

class NexusBot(commands.Bot):
    async def setup_hook(self):
        for extension in (
            "cogs.ai",
            "cogs.builder",
            "cogs.moderation",
        ):
            await self.load_extension(extension)
            log.info("Loaded %s", extension)
        if settings.sync_commands:
            synced = await self.tree.sync()
            log.info("Synced %s application commands", len(synced))

bot = NexusBot(
    command_prefix="!",
    intents=intents,
    allowed_mentions=discord.AllowedMentions(
        everyone=False, users=True, roles=False, replied_user=False
    ),
)

@bot.event
async def on_ready():
    log.info("Logged in as %s (ID: %s)", bot.user, bot.user.id)

if __name__ == "__main__":
    if not settings.discord_token:
        raise RuntimeError("DISCORD_BOT_TOKEN is missing. Set it in .env.")
    bot.run(settings.discord_token, log_handler=None)
