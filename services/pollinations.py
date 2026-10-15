import logging
from openai import AsyncOpenAI, APIConnectionError, APIStatusError, RateLimitError
from config import settings

log = logging.getLogger("nexus.pollinations")

class AIServiceError(RuntimeError):
    """Safe, user-facing AI service error."""

_client = None

def get_client():
    global _client
    if not settings.pollinations_api_key:
        raise AIServiceError(
            "The AI API key is not configured. Ask the bot owner to set POLLINATIONS_API_KEY."
        )
    if _client is None:
        _client = AsyncOpenAI(
            base_url="https://gen.pollinations.ai/v1",
            api_key=settings.pollinations_api_key,
            timeout=45.0,
            max_retries=1,
        )
    return _client

async def ask(messages, *, max_tokens=1200, temperature=0.4):
    try:
        response = await get_client().chat.completions.create(
            model=settings.pollinations_model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        content = response.choices[0].message.content
        if not content:
            raise AIServiceError("The AI returned an empty response. Try again.")
        return content.strip()
    except AIServiceError:
        raise
    except RateLimitError:
        raise AIServiceError("The AI service is rate-limiting requests. Please try again shortly.")
    except APIStatusError as exc:
        # Log status only; never log headers, request bodies, or secrets.
        log.warning("Pollinations returned HTTP %s", exc.status_code)
        if exc.status_code == 401:
            message = "The Pollinations API key was rejected. Check the server's environment settings."
        elif exc.status_code == 402:
            message = "The Pollinations account needs available Pollen balance for this request."
        elif exc.status_code == 403:
            message = "The Pollinations API key does not have permission for this request."
        else:
            message = "The AI service returned an error. Please try again later."
        raise AIServiceError(message) from None
    except APIConnectionError:
        raise AIServiceError("NEXUS could not connect to the AI service. Try again shortly.") from None
    except Exception:
        log.exception("Unexpected AI service failure")
        raise AIServiceError("The AI request failed unexpectedly. Check the bot logs.") from None
