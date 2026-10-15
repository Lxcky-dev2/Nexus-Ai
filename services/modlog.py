import discord

async def send_modlog(guild: discord.Guild, message: str):
    """Send to a configured channel ID if NEXUS_MODLOG_CHANNEL_ID is set."""
    import os
    raw_id = os.getenv("NEXUS_MODLOG_CHANNEL_ID", "").strip()
    if not raw_id.isdigit():
        return
    channel = guild.get_channel(int(raw_id))
    if channel is None:
        return
    try:
        await channel.send(message, allowed_mentions=discord.AllowedMentions.none())
    except discord.HTTPException:
        pass
