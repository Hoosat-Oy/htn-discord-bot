import os
import discord
import asyncio
import aiohttp
import logging
from typing import Optional

from discord.ext import commands

def _get_env_int(name: str) -> Optional[int]:
    raw = os.getenv(name)
    if raw is None:
        return None
    raw = raw.strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        raise ValueError(f"{name} must be an integer")


TOKEN = os.getenv("TOKEN")
API_URL = os.getenv("API_URL")

PRICE_CHANNEL_ID = _get_env_int("PRICE_CHANNEL_ID")
HASHRATE_CHANNEL_ID = _get_env_int("HASHRATE_CHANNEL_ID")
MARKETCAP_CHANNEL_ID = _get_env_int("MARKETCAP_CHANNEL_ID")
HOOSAT_LISTING_WALLET_CHANNEL = _get_env_int("HOOSAT_LISTING_WALLET_CHANNEL")
TRON_USDT_LISTING_WALLET_CHANNEL = _get_env_int("TRON_USDT_LISTING_WALLET_CHANNEL")

GUILD_ID = _get_env_int("GUILD_ID")
FUNDING_HTN_WALLET = "hoosat:qqqht7hgt5jay507ragnk73rkjgwvjqzq238krdd9mpfryr6jcah28ejmxruv"
FUNDUNG_TRON_USDT_WALLET = "TQQzQS1hepsZNuCdhBnGYryCCDegpiASHm"

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
log = logging.getLogger("htn-discord-bot")

HTTP_TIMEOUT = aiohttp.ClientTimeout(total=15, connect=5, sock_read=10)
DEFAULT_HEADERS = {"User-Agent": "htn-discord-bot"}


def _format_number_compact(value: float, *, decimals: int = 2) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:.{decimals}f}M"
    if value >= 1_000:
        return f"{value / 1_000:.{decimals}f}K"
    return f"{value:.{decimals}f}"


def _dotless(s: str) -> str:
    return s.replace(".", "․")


def _none_if_exc(value):
    return None if isinstance(value, BaseException) else value


def _th_to_gh(th_s: float) -> float:
    return th_s * 1000.0


def _is_hoosat_address(address: str) -> bool:
    address = address.strip()
    return address.startswith("hoosat:") and len(address) > len("hoosat:")


async def fetch_json(session: aiohttp.ClientSession, url: str):
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.json()

async def fetch_tron_usdt_wallet_balance(session: aiohttp.ClientSession, wallet_address, contract_address="TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"): 
    url = "https://api.trongrid.io/v1/accounts"
    try:
        data = await fetch_json(session, f"{url}/{wallet_address}")
        
        # Access the trc20 token balances
        trc20_tokens = data.get("data", [{}])[0].get("trc20", [])
        for token in trc20_tokens:
            if contract_address in token:
                # Convert balance from Sun (10^6 precision) to USDT value
                balance = int(token[contract_address]) / (10 ** 6)
                return balance

        # Return 0.0 if no balance found for the specified contract
        return 0.0

    except (aiohttp.ClientError, asyncio.TimeoutError, KeyError, ValueError) as e:
        log.warning("Failed to fetch TRON USDT wallet balance: %s", e)
        return None

async def fetch_htn_wallet_balance(session: aiohttp.ClientSession, address): 
    try:
        if not API_URL:
            return None
        data = await fetch_json(session, API_URL + f"/addresses/{address}/balance")
        balance = int(data['balance']) / 100_000_000
        return balance
    except (aiohttp.ClientError, asyncio.TimeoutError, KeyError, ValueError) as e:
        log.warning("Failed to fetch HTN wallet balance: %s", e)
        return None

async def fetch_price(session: aiohttp.ClientSession):
    if not API_URL:
        raise RuntimeError("API_URL is not configured")
    data = await fetch_json(session, API_URL + "/info/price")
    price = data['price']
    return price


async def fetch_hashrate(session: aiohttp.ClientSession): 
    if not API_URL:
        raise RuntimeError("API_URL is not configured")
    data = await fetch_json(session, API_URL + "/info/hashrate?stringOnly=false")
    hashrate = data['hashrate']
    return hashrate


async def fetch_marketcap(session: aiohttp.ClientSession): 
    if not API_URL:
        raise RuntimeError("API_URL is not configured")
    data = await fetch_json(session, API_URL + "/info/marketcap?stringOnly=false")
    marketcap = data['marketcap']
    return marketcap

async def _edit_channel_name(channel: Optional[discord.abc.GuildChannel], new_name: str, *, label: str):
    if channel is None:
        return
    try:
        await channel.edit(name=new_name)
        log.info("Updated %s channel name to: %s", label, new_name)
    except Exception as e:
        log.warning("Failed to update %s channel: %s", label, e)


class HTNBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)
        self.http_session: Optional[aiohttp.ClientSession] = None
        self._bg_task: Optional[asyncio.Task] = None
        self._synced = False

    async def setup_hook(self) -> None:
        self.http_session = aiohttp.ClientSession(timeout=HTTP_TIMEOUT, headers=DEFAULT_HEADERS)

    async def close(self) -> None:
        try:
            if self._bg_task:
                self._bg_task.cancel()
        finally:
            if self.http_session and not self.http_session.closed:
                await self.http_session.close()
            await super().close()


bot = HTNBot()


@bot.tree.command(name="ping", description="Check bot latency")
async def ping(interaction: discord.Interaction):
    latency_ms = int(bot.latency * 1000)
    await interaction.response.send_message(f"Pong! {latency_ms}ms")


@bot.tree.command(name="price", description="Get current HTN price")
async def price(interaction: discord.Interaction):
    if not API_URL:
        await interaction.response.send_message("API_URL is not configured.", ephemeral=True)
        return
    if not bot.http_session:
        await interaction.response.send_message("HTTP session not ready.", ephemeral=True)
        return
    try:
        p = await fetch_price(bot.http_session)
        formatted = _dotless(f"{p:.6f}")
        await interaction.response.send_message(f"HTN price: ${formatted}")
    except Exception as e:
        log.warning("/price failed: %s", e)
        await interaction.response.send_message("Failed to fetch price.", ephemeral=True)


@bot.tree.command(name="hashrate", description="Get current HTN network hashrate")
async def hashrate(interaction: discord.Interaction):
    if not API_URL:
        await interaction.response.send_message("API_URL is not configured.", ephemeral=True)
        return
    if not bot.http_session:
        await interaction.response.send_message("HTTP session not ready.", ephemeral=True)
        return
    try:
        h = await fetch_hashrate(bot.http_session)
        gh = _th_to_gh(float(h))
        formatted = _dotless(f"{gh:.2f}")
        await interaction.response.send_message(f"HTN hashrate: {formatted} GH/s")
    except Exception as e:
        log.warning("/hashrate failed: %s", e)
        await interaction.response.send_message("Failed to fetch hashrate.", ephemeral=True)


@bot.tree.command(name="marketcap", description="Get current HTN market cap")
async def marketcap(interaction: discord.Interaction):
    if not API_URL:
        await interaction.response.send_message("API_URL is not configured.", ephemeral=True)
        return
    if not bot.http_session:
        await interaction.response.send_message("HTTP session not ready.", ephemeral=True)
        return
    try:
        mc = await fetch_marketcap(bot.http_session)
        compact = _format_number_compact(float(mc), decimals=2)
        await interaction.response.send_message(f"HTN market cap: {compact} USDT")
    except Exception as e:
        log.warning("/marketcap failed: %s", e)
        await interaction.response.send_message("Failed to fetch market cap.", ephemeral=True)


@bot.tree.command(name="status", description="Get HTN price/hashrate/marketcap in one message")
async def status(interaction: discord.Interaction):
    if not API_URL:
        await interaction.response.send_message("API_URL is not configured.", ephemeral=True)
        return
    if not bot.http_session:
        await interaction.response.send_message("HTTP session not ready.", ephemeral=True)
        return

    await interaction.response.defer()
    try:
        p, h, mc = await asyncio.gather(
            fetch_price(bot.http_session),
            fetch_hashrate(bot.http_session),
            fetch_marketcap(bot.http_session),
        )
        embed = discord.Embed(title="HTN Status")
        embed.add_field(name="Price", value=f"${_dotless(f'{p:.6f}')}" , inline=True)
        embed.add_field(name="Hashrate", value=f"{_dotless(f'{_th_to_gh(float(h)):.2f}')} GH/s", inline=True)
        embed.add_field(name="Market cap", value=f"{_format_number_compact(float(mc), decimals=2)} USDT", inline=True)
        await interaction.followup.send(embed=embed)
    except Exception as e:
        log.warning("/status failed: %s", e)
        await interaction.followup.send("Failed to fetch status.", ephemeral=True)


@bot.tree.command(name="wallets", description="Show funding wallet balances")
async def wallets(interaction: discord.Interaction):
    if not bot.http_session:
        await interaction.response.send_message("HTTP session not ready.", ephemeral=True)
        return

    await interaction.response.defer()
    try:
        htn_balance, usdt_balance = await asyncio.gather(
            fetch_htn_wallet_balance(bot.http_session, FUNDING_HTN_WALLET),
            fetch_tron_usdt_wallet_balance(bot.http_session, FUNDUNG_TRON_USDT_WALLET),
        )

        embed = discord.Embed(title="Funding Wallets")
        if htn_balance is None:
            embed.add_field(name="HTN", value="Unavailable", inline=True)
        else:
            embed.add_field(name="HTN", value=_dotless(_format_number_compact(float(htn_balance), decimals=2)), inline=True)

        if usdt_balance is None:
            embed.add_field(name="TRC20 USDT", value="Unavailable", inline=True)
        else:
            embed.add_field(name="TRC20 USDT", value=_dotless(_format_number_compact(float(usdt_balance), decimals=2)), inline=True)

        await interaction.followup.send(embed=embed)
    except Exception as e:
        log.warning("/wallets failed: %s", e)
        await interaction.followup.send("Failed to fetch wallet balances.", ephemeral=True)


@bot.tree.command(name="balance", description="Get HTN balance for a hoosat: address")
async def balance(interaction: discord.Interaction, address: str):
    if not API_URL:
        await interaction.response.send_message("API_URL is not configured.", ephemeral=True)
        return
    if not bot.http_session:
        await interaction.response.send_message("HTTP session not ready.", ephemeral=True)
        return

    address = address.strip()
    if not _is_hoosat_address(address):
        await interaction.response.send_message('Invalid address. Expected format like: `hoosat:...`', ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    try:
        bal, price_usdt = await asyncio.gather(
            fetch_htn_wallet_balance(bot.http_session, address),
            fetch_price(bot.http_session),
            return_exceptions=True,
        )

        if isinstance(bal, BaseException):
            log.warning("/balance balance fetch failed: %s", bal)
            bal = None
        if isinstance(price_usdt, BaseException):
            log.warning("/balance price fetch failed: %s", price_usdt)
            price_usdt = None

        if bal is None:
            await interaction.followup.send("Failed to fetch balance.")
            return

        embed = discord.Embed(title="Hoosat Address Balance")
        embed.add_field(name="Address", value=address, inline=False)
        embed.add_field(name="HTN", value=f"{_dotless(f'{float(bal):.8f}')} HTN", inline=True)

        if price_usdt is not None:
            usdt_value = float(bal) * float(price_usdt)
            embed.add_field(name="USDT", value=f"{_dotless(f'{usdt_value:.2f}')} USDT", inline=True)
        else:
            embed.add_field(name="USDT", value="Unavailable", inline=True)

        await interaction.followup.send(embed=embed)
    except Exception as e:
        log.warning("/balance failed: %s", e)
        await interaction.followup.send("Failed to fetch balance.")


async def update_channel_names_loop():
    await bot.wait_until_ready()
    if not bot.http_session:
        log.error("HTTP session missing; cannot start background loop")
        return

    price_channel = bot.get_channel(PRICE_CHANNEL_ID) if PRICE_CHANNEL_ID else None
    hashrate_channel = bot.get_channel(HASHRATE_CHANNEL_ID) if HASHRATE_CHANNEL_ID else None
    marketcap_channel = bot.get_channel(MARKETCAP_CHANNEL_ID) if MARKETCAP_CHANNEL_ID else None
    htn_wallet_channel = bot.get_channel(HOOSAT_LISTING_WALLET_CHANNEL) if HOOSAT_LISTING_WALLET_CHANNEL else None
    usdt_wallet_channel = bot.get_channel(TRON_USDT_LISTING_WALLET_CHANNEL) if TRON_USDT_LISTING_WALLET_CHANNEL else None

    if not any([price_channel, hashrate_channel, marketcap_channel, htn_wallet_channel, usdt_wallet_channel]):
        log.info("No channel IDs configured; background channel updater is disabled")
        return

    while not bot.is_closed():
        try:
            tasks = []
            if API_URL:
                tasks.extend([
                    fetch_price(bot.http_session),
                    fetch_hashrate(bot.http_session),
                    fetch_marketcap(bot.http_session),
                    fetch_htn_wallet_balance(bot.http_session, FUNDING_HTN_WALLET),
                    fetch_tron_usdt_wallet_balance(bot.http_session, FUNDUNG_TRON_USDT_WALLET),
                ])
                price_val, hashrate_val, marketcap_val, htn_balance, usdt_balance = await asyncio.gather(*tasks, return_exceptions=True)
            else:
                price_val = hashrate_val = marketcap_val = htn_balance = usdt_balance = None

            # Handle exceptions from gather(return_exceptions=True)
            if isinstance(price_val, BaseException):
                log.warning("Price fetch failed: %s", price_val)
            if isinstance(hashrate_val, BaseException):
                log.warning("Hashrate fetch failed: %s", hashrate_val)
            if isinstance(marketcap_val, BaseException):
                log.warning("Marketcap fetch failed: %s", marketcap_val)
            if isinstance(htn_balance, BaseException):
                log.warning("HTN wallet fetch failed: %s", htn_balance)
            if isinstance(usdt_balance, BaseException):
                log.warning("USDT wallet fetch failed: %s", usdt_balance)

            price_val = _none_if_exc(price_val)
            hashrate_val = _none_if_exc(hashrate_val)
            marketcap_val = _none_if_exc(marketcap_val)
            htn_balance = _none_if_exc(htn_balance)
            usdt_balance = _none_if_exc(usdt_balance)

            if price_val is not None and price_channel is not None:
                price_str = _dotless(f"{price_val:.6f}")
                await _edit_channel_name(price_channel, f"💰 ${price_str} HTN", label="price")

            if hashrate_val is not None and hashrate_channel is not None:
                gh = _th_to_gh(float(hashrate_val))
                hashrate_str = _dotless(f"{gh:.2f}")
                await _edit_channel_name(hashrate_channel, f"⛏️ {hashrate_str} GH/s", label="hashrate")

            if marketcap_val is not None and marketcap_channel is not None:
                mc_compact = _format_number_compact(float(marketcap_val), decimals=2)
                await _edit_channel_name(marketcap_channel, f"💹 {mc_compact} USDT", label="marketcap")

            if htn_balance is not None and htn_wallet_channel is not None:
                bal = _dotless(_format_number_compact(float(htn_balance), decimals=2))
                await _edit_channel_name(htn_wallet_channel, f"💸 {bal} HTN", label="htn wallet")

            if usdt_balance is not None and usdt_wallet_channel is not None:
                bal = _dotless(_format_number_compact(float(usdt_balance), decimals=2))
                await _edit_channel_name(usdt_wallet_channel, f"💸 {bal} TRC20 USDT", label="usdt wallet")

            # Update presence once per loop (avoid spamming change_presence)
            presence_parts = []
            if price_val is not None:
                presence_parts.append(f"${_dotless(f'{price_val:.6f}')}")
            if hashrate_val is not None:
                gh = _th_to_gh(float(hashrate_val))
                presence_parts.append(f"{_dotless(f'{gh:.2f}')} GH/s")
            if presence_parts:
                activity = discord.Activity(
                    type=discord.ActivityType.watching,
                    name=" | ".join(presence_parts)[:128],
                )
                await bot.change_presence(activity=activity)

        except Exception as e:
            log.warning("Background update loop error: %s", e)

        await asyncio.sleep(60)


@bot.event
async def on_ready():
    log.info("Logged in as %s", bot.user)

    if not bot._synced:
        try:
            if GUILD_ID:
                guild = discord.Object(id=GUILD_ID)
                bot.tree.copy_global_to(guild=guild)
                await bot.tree.sync(guild=guild)
                log.info("Synced app commands to guild %s", GUILD_ID)
            else:
                await bot.tree.sync()
                log.info("Synced app commands globally")
            bot._synced = True
        except Exception as e:
            log.warning("Failed to sync app commands: %s", e)

    if bot._bg_task is None:
        bot._bg_task = bot.loop.create_task(update_channel_names_loop())


if not TOKEN or not TOKEN.strip():
    raise RuntimeError("TOKEN is required")

bot.run(TOKEN)