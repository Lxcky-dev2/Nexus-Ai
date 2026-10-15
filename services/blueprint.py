import json
import re

MAX_ROLES = 15
MAX_CATEGORIES = 12
MAX_CHANNELS = 40

def extract_json(text: str) -> dict:
    """Parse a JSON object, allowing a surrounding markdown code fence."""
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("The AI response did not contain a JSON object.")
    data = json.loads(cleaned[start:end + 1])
    return validate_blueprint(data)

def clean_name(value, *, limit=90):
    if not isinstance(value, str):
        raise ValueError("Names must be text.")
    value = value.strip()
    if not value or len(value) > limit:
        raise ValueError(f"Names must be between 1 and {limit} characters.")
    return value

def validate_blueprint(data):
    if not isinstance(data, dict):
        raise ValueError("Blueprint must be a JSON object.")
    name = clean_name(data.get("server_name", "NEXUS Community"), limit=80)
    description = str(data.get("description", "A community Discord server"))[:500]
    roles = data.get("roles", [])
    categories = data.get("categories", [])
    if not isinstance(roles, list) or not isinstance(categories, list):
        raise ValueError("Roles and categories must be lists.")
    if len(roles) > MAX_ROLES or len(categories) > MAX_CATEGORIES:
        raise ValueError("Blueprint exceeds the allowed role/category limits.")
    clean_roles = []
    for role in roles:
        if isinstance(role, str):
            role_name = clean_name(role, limit=100)
        elif isinstance(role, dict):
            role_name = clean_name(role.get("name", ""), limit=100)
        else:
            raise ValueError("Each role must be a name or object.")
        if role_name.lower() not in {r.lower() for r in clean_roles}:
            clean_roles.append(role_name)

    clean_categories = []
    total_channels = 0
    for category in categories:
        if not isinstance(category, dict):
            raise ValueError("Each category must be an object.")
        cat_name = clean_name(category.get("name", ""), limit=100)
        channels = category.get("channels", [])
        if not isinstance(channels, list):
            raise ValueError("Category channels must be a list.")
        total_channels += len(channels)
        clean_channels = []
        for channel in channels:
            if isinstance(channel, str):
                channel_name = clean_name(channel, limit=100)
                channel_type = "text"
            elif isinstance(channel, dict):
                channel_name = clean_name(channel.get("name", ""), limit=100)
                channel_type = channel.get("type", "text")
            else:
                raise ValueError("Each channel must be a name or object.")
            if channel_type not in ("text", "voice"):
                channel_type = "text"
            clean_channels.append({"name": channel_name, "type": channel_type})
        clean_categories.append({"name": cat_name, "channels": clean_channels})
    if total_channels > MAX_CHANNELS:
        raise ValueError(f"Blueprint has {total_channels} channels; maximum is {MAX_CHANNELS}.")
    return {
        "server_name": name,
        "description": description,
        "roles": clean_roles,
        "categories": clean_categories,
    }

def preview_text(bp):
    lines = [
        f"**{bp['server_name']} — proposed server blueprint**",
        bp["description"],
        "",
        f"**Roles ({len(bp['roles'])})**",
    ]
    lines += [f"• {r}" for r in bp["roles"]] or ["• None"]
    lines += ["", f"**Categories and channels ({sum(len(c['channels']) for c in bp['categories'])} channels)**"]
    for cat in bp["categories"]:
        lines.append(f"**{cat['name']}**")
        lines.extend(f"• {'🔊' if ch['type'] == 'voice' else '#'} {ch['name']}" for ch in cat["channels"])
    lines += ["", "Nothing has been created yet. An administrator must run `/builder apply` to build this plan."]
    return "\n".join(lines)
