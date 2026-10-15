import asyncio
import time
from collections import defaultdict, deque
from config import settings

class AIProtectionError(RuntimeError):
    pass

class AIProtection:
    """In-memory guardrails; state resets when the bot restarts."""
    def __init__(self):
        self.user_last = {}
        self.guild_requests = defaultdict(deque)
        self.user_requests = defaultdict(deque)
        self.semaphore = asyncio.Semaphore(settings.ai_max_concurrent)

    def check(self, *, user_id: int, guild_id: int):
        now = time.monotonic()
        last = self.user_last.get(user_id, 0)
        remaining = settings.ai_user_cooldown_seconds - (now - last)
        if remaining > 0:
            raise AIProtectionError(f"Slow down a little — try again in {int(remaining) + 1}s.")

        window = 60
        user_key = (guild_id, user_id)
        user_queue = self.user_requests[user_key]
        while user_queue and now - user_queue[0] > window:
            user_queue.popleft()
        if len(user_queue) >= settings.ai_user_requests_per_minute:
            raise AIProtectionError("You've reached the AI request limit. Try again in a minute.")

        guild_queue = self.guild_requests[guild_id]
        while guild_queue and now - guild_queue[0] > window:
            guild_queue.popleft()
        if len(guild_queue) >= settings.ai_guild_requests_per_minute:
            raise AIProtectionError("This server has reached its AI request limit. Try again in a minute.")

        self.user_last[user_id] = now
        user_queue.append(now)
        guild_queue.append(now)

protection = AIProtection()
