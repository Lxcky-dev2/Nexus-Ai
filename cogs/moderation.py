import re
from datetime import timedelta
from datetime import timedelta
import discord
from discord import app_commands
from discord.ext import commands
from services.modlog import send_modlog

INVITE_RE = re.compile(r"(?:discord\.gg/|discord(?:app)?\.com/invite/)[A-Za-z0-9-]+", re.I)

def moderator(interaction: discord.Interaction):
    return bool(interaction.guild and interaction.user.guild_permissions.manage_messages)

class ModerationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="timeout", description="Timeout a member.")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout(self, interaction: discord.Interaction, member: discord.Member, minutes: app_commands.Range[int, 1, 40320], reason: str = "No reason provided"):
        if member.id == interaction.user.id or member.top_role >= interaction.user.top_role and interaction.guild.owner_id != interaction.user.id:
            await interaction.response.send_message("You cannot timeout that member due to role hierarchy.", ephemeral=True)
            return
        try:
            await member.timeout(discord.utils.utcnow() + timedelta(minutes=minutes), reason=reason[:500])
            await interaction.response.send_message(f"Timed out {member.mention} for {minutes} minutes.", ephemeral=True)
            await send_modlog(interaction.guild, f"⏳ {member} timed out by {interaction.user} for {minutes} minutes. Reason: {reason[:500]}")
        except discord.Forbidden:
            await interaction.response.send_message("I can't timeout that member. Check role hierarchy and Moderate Members permission.", ephemeral=True)

    @app_commands.command(name="kick", description="Kick a member.")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        if member.id == interaction.user.id or member.top_role >= interaction.user.top_role and interaction.guild.owner_id != interaction.user.id:
            await interaction.response.send_message("You cannot kick that member due to role hierarchy.", ephemeral=True)
            return
        try:
            await member.kick(reason=reason[:500])
            await interaction.response.send_message(f"Kicked {member}.", ephemeral=True)
            await send_modlog(interaction.guild, f"👢 {member} kicked by {interaction.user}. Reason: {reason[:500]}")
        except discord.Forbidden:
            await interaction.response.send_message("I can't kick that member. Check my role and Kick Members permission.", ephemeral=True)

    @app_commands.command(name="ban", description="Ban a member.")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        if member.id == interaction.user.id or member.top_role >= interaction.user.top_role and interaction.guild.owner_id != interaction.user.id:
            await interaction.response.send_message("You cannot ban that member due to role hierarchy.", ephemeral=True)
            return
        try:
            await member.ban(reason=reason[:500], delete_message_seconds=0)
            await interaction.response.send_message(f"Banned {member}.", ephemeral=True)
            await send_modlog(interaction.guild, f"🔨 {member} banned by {interaction.user}. Reason: {reason[:500]}")
        except discord.Forbidden:
            await interaction.response.send_message("I can't ban that member. Check my role and Ban Members permission.", ephemeral=True)

    @app_commands.command(name="purge", description="Delete a number of recent messages.")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def purge(self, interaction: discord.Interaction, amount: app_commands.Range[int, 1, 100]):
        if not isinstance(interaction.channel, (discord.TextChannel, discord.Thread)):
            await interaction.response.send_message("Use this in a text channel.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        try:
            deleted = await interaction.channel.purge(limit=amount, reason=f"Purged by {interaction.user}")
            await interaction.followup.send(f"Deleted {len(deleted)} messages.", ephemeral=True)
            await send_modlog(interaction.guild, f"🧹 {interaction.user} purged {len(deleted)} messages in #{interaction.channel}.")
        except discord.Forbidden:
            await interaction.followup.send("I need Manage Messages permission in this channel.", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        # Basic invite-link guardrail. Enable Message Content Intent in the Developer Portal.
        if INVITE_RE.search(message.content):
            member = message.author
            if not isinstance(member, discord.Member):
                return
            # Only remove links from members who lack Manage Messages; admins/mods can post them.
            if not member.guild_permissions.manage_messages:
                try:
                    await message.delete()
                    await message.channel.send(
                        f"{member.mention}, Discord invite links aren't allowed here.",
                        delete_after=6,
                        allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False),
                    )
                    await send_modlog(message.guild, f"🔗 Removed a Discord invite link from {member} in #{message.channel}.")
                except discord.Forbidden:
                    pass

async def setup(bot):
    await bot.add_cog(ModerationCog(bot))
