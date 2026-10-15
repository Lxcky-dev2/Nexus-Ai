import discord
from discord import app_commands
from discord.ext import commands
from config import settings
from services.pollinations import ask, AIServiceError
from services.ai_protection import protection, AIProtectionError

class AICog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ask", description="Ask NEXUS AI a question.")
    @app_commands.describe(prompt="What do you want NEXUS to help with?")
    async def ask_command(self, interaction: discord.Interaction, prompt: str):
        if len(prompt) > settings.max_ai_chars:
            await interaction.response.send_message(
                f"That prompt is too long (maximum {settings.max_ai_chars} characters).",
                ephemeral=True,
            )
            return
        try:
            if interaction.guild_id is None:
                await interaction.response.send_message("Use NEXUS AI inside a server so per-server limits can apply.", ephemeral=True)
                return
            protection.check(user_id=interaction.user.id, guild_id=interaction.guild_id)
        except AIProtectionError as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return
        await interaction.response.defer(thinking=True)
        try:
            async with protection.semaphore:
                answer = await ask([
                {"role": "system", "content": "You are NEXUS, a helpful Discord community assistant. Be clear, friendly, and concise. Never claim to have performed Discord actions unless a command actually did them."},
                {"role": "user", "content": prompt},
            ], max_tokens=700)
            # Discord message limit is 2000 characters.
            await interaction.followup.send(answer[:1900])
        except AIServiceError as exc:
            await interaction.followup.send(str(exc), ephemeral=True)

async def setup(bot):
    await bot.add_cog(AICog(bot))
