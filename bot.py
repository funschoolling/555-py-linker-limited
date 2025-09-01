import base64
import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from dotenv import load_dotenv
from aiohttp import web
import asyncio
import aiohttp
from datetime import datetime, timedelta
import secrets

SECRET_KEY = "my_secret_key"

def encrypt_string(plain: str) -> str:
    key = SECRET_KEY
    enc_bytes = bytearray()
    for i, c in enumerate(plain.encode()):
        enc_bytes.append(c ^ ord(key[i % len(key)]))
    return base64.b64encode(enc_bytes).decode()

def decrypt_string(enc: str) -> str:
    key = SECRET_KEY
    data = base64.b64decode(enc.encode())
    dec_bytes = bytearray()
    for i, c in enumerate(data):
        dec_bytes.append(c ^ ord(key[i % len(key)]))
    return dec_bytes.decode()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

linked_accounts_file = decrypt_string("GwMcFQMXEg==")
CONFIG_FILE = decrypt_string("CwwIFhE=")
ADMIN_ROLE_NAME = "🔨Mod"
SUPPORTER_ROLE_NAME = "Supporter"
OWNER_ID = int(decrypt_string("ExUAFxYQBxQYEAcAHR0UFQ8FFQ=="))
BACKEND_URL = decrypt_string("GgYcCxAHAg1gWhQ7FQp2Ax0CBQgUGw4fGws=")
ROBLOX_API_URL = decrypt_string("HRsZCgERAw5tSgECUBUMQwcYHhUGBgpoBBkQAhZqDg==")

try:
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
except FileNotFoundError:
    config = {"gamepass_roles": []}

try:
    with open(linked_accounts_file, "r") as f:
        temp_accounts = json.load(f)
        if not isinstance(temp_accounts, dict) or ("discord_to_roblox" not in temp_accounts and "roblox_to_discord" not in temp_accounts):
            discord_to_roblox = {}
            roblox_to_discord = {}
            for discord_id, roblox_id in temp_accounts.items():
                discord_to_roblox[discord_id] = roblox_id
                roblox_to_discord[str(roblox_id)] = discord_id
            linked_accounts = {
                "discord_to_roblox": discord_to_roblox,
                "roblox_to_discord": roblox_to_discord,
                "force_linked_users": [],
                "generated_codes": {}
            }
        else:
            linked_accounts = temp_accounts
            if "force_linked_users" not in linked_accounts:
                linked_accounts["force_linked_users"] = []
            if "generated_codes" not in linked_accounts:
                linked_accounts["generated_codes"] = {}
except FileNotFoundError:
    linked_accounts = {"discord_to_roblox": {}, "roblox_to_discord": {}, "force_linked_users": [], "generated_codes": {}}

def save_linked_accounts():
    with open(linked_accounts_file, "w") as f:
        json.dump(linked_accounts, f, indent=2)

def is_admin(interaction: discord.Interaction) -> bool:
    role = discord.utils.get(interaction.guild.roles, name=ADMIN_ROLE_NAME)
    if role is None:
        return False
    return (role in interaction.user.roles) or (interaction.user.id == OWNER_ID)

def has_supporter_role(member: discord.Member) -> bool:
    role = discord.utils.get(member.guild.roles, name=SUPPORTER_ROLE_NAME)
    return role in member.roles if role else False

@bot.tree.command(name="link-roblox", description=decrypt_string("HxkUHBsTGQZ2XxQGB1IU"))
async def link_roblox(interaction: discord.Interaction, username: str):
    embed = discord.Embed(color=discord.Color.blue())
    user_id = await get_roblox_user_id(username)
    discord_id = str(interaction.user.id)
    if not user_id:
        embed.title = decrypt_string("DAkAHggIC1c=")
        embed.description = decrypt_string("BQoTDR0FFg9pURQVAAdZUBsAUlYNHRMPUg==") + f" `{username}`"
        embed.color = discord.Color.red()
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    roblox_id_str = str(user_id)
    if discord_id in linked_accounts["discord_to_roblox"]:
        embed.title = decrypt_string("DAkAHggIC1c=")
        embed.description = decrypt_string("BwoQGBgAGgViUgYVDV8AUA==")
        embed.color = discord.Color.red()
    elif roblox_id_str in linked_accounts["roblox_to_discord"]:
        embed.title = decrypt_string("DAkAHggIC1c=")
        embed.description = decrypt_string("Bh4cHgALDgFuVwgUVV8B")
        embed.color = discord.Color.red()
    else:
        linked_accounts["discord_to_roblox"][discord_id] = user_id
        linked_accounts["roblox_to_discord"][roblox_id_str] = discord_id
        save_linked_accounts()
        embed.title = decrypt_string("FBMeARoPAVMBWxcVEFYQ")
        embed.description = decrypt_string("FAkSBRYPAgdmUwYGAAYdHgAIVkMJXBsQEVE=") + f" `{username}`"
        embed.color = discord.Color.green()
    await interaction.response.send_message(embed=embed, ephemeral=True)

async def get_roblox_user_id(username: str) -> int:
    url = decrypt_string("HB8eDRILFzR2SRICVUg=")
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json={"usernames": [username]}) as response:
            if response.status == 200:
                user_data = await response.json()
                if user_data["data"]:
                    return user_data["data"][0]["id"]
    return None

async def has_gamepass(user_id: int, gamepass_id: int) -> bool:
    url = ROBLOX_API_URL.format(user_id=user_id, gamepass_id=gamepass_id)
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                gamepasses = await response.json()
                return bool(gamepasses.get("data", []))
    return False

async def remove_gamepass_roles(member: discord.Member):
    role_ids = [mapping["role_id"] for mapping in config["gamepass_roles"]]
    roles_to_remove = [role for role in member.roles if role.id in role_ids]
    if roles_to_remove:
        await member.remove_roles(*roles_to_remove)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(decrypt_string("FhYdDg8UGwVeUgMcQUo="))

async def handle(request):
    return web.Response(text=decrypt_string("FBQVCwYECwVvSxMBVFI="))

async def run_webserver():
    app = web.Application()
    app.router.add_get('/', handle)
    port = int(os.environ.get("PORT", 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(decrypt_string("GxseCg0DDQFsQxABUVEQBgAJHhYWYQs="))

async def main():
    await run_webserver()
    await bot.start(os.getenv("DISCORD_TOKEN"))

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(main())
