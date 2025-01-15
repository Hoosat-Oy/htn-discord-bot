import os
import discord 
import requests
import asyncio

# Replace this with your bot's token
TOKEN = os.getenv('TOKEN')
PRICE_CHANNEL_ID = int(os.getenv('PRICE_CHANNEL_ID'))
HASHRATE_CHANNEL_ID = int(os.getenv('HASHRATE_CHANNEL_ID'))
MARKETCAP_CHANNEL_ID = int(os.getenv('MARKETCAP_CHANNEL_ID'))
HOOSAT_LISTING_WALLET_CHANNEL = int(os.getenv('HOOSAT_LISTING_WALLET_CHANNEL'))
TRON_USDT_LISTING_WALLET_CHANNEL = int(os.getenv('TRON_USDT_LISTING_WALLET_CHANNEL'))
API_URL = os.getenv('API_URL')
FUNDING_HTN_WALLET = "hoosat:qqqht7hgt5jay507ragnk73rkjgwvjqzq238krdd9mpfryr6jcah28ejmxruv"
FUNDUNG_TRON_USDT_WALLET = "TQQzQS1hepsZNuCdhBnGYryCCDegpiASHm"

client = discord.Client(intents=discord.Intents.default())

async def fetch_tron_usdt_wallet_balance(wallet_address, contract_address="TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"): 
    url = "https://api.trongrid.io/v1/accounts"
    try:
        response = requests.get(f"{url}/{wallet_address}")
        response.raise_for_status()
        data = response.json()
        
        # Access the trc20 token balances
        trc20_tokens = data.get("data", [{}])[0].get("trc20", [])
        for token in trc20_tokens:
            if contract_address in token:
                # Convert balance from Sun (10^6 precision) to USDT value
                balance = int(token[contract_address]) / (10 ** 6)
                return balance

        # Return 0.0 if no balance found for the specified contract
        return 0.0

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

async def update_funding_tron_usdt_wallet_balance(channel):
    try:
        balance = await fetch_htn_wallet_balance(FUNDING_HTN_WALLET)
        if balance >= 1_000_000:
            formatted_balance = f"{balance / 1_000_000:.2f}M"
        elif balance >= 1_000:
            formatted_balance = f"{balance / 1_000:.2f}K"
        else:
            formatted_balance = f"{balance:.2f}"
        formatted_balance = formatted_balance.replace('.', '․')
        activity = discord.Activity(type=discord.ActivityType.watching, name=f"Balance: {formatted_balance}")
        await client.change_presence(activity=activity)
        new_name = f"💸 {formatted_balance} TRX-USDT LISTING"
        await channel.edit(name=new_name)
        print(f"Updated channel name to: {new_name}")

    except Exception as e:
        print(f"An error occurred: {e}")

async def fetch_htn_wallet_balance(address): 
    try:
        response = requests.get(API_URL + f"/addresses/{address}/balance")
        data = response.json()
        balance = int(data['balance']) / 100_000_000
        return balance
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

async def update_funding_htn_wallet_balance(channel):
    try:
        balance = await fetch_htn_wallet_balance(FUNDING_HTN_WALLET)
        if balance >= 1_000_000:
            formatted_balance = f"{balance / 1_000_000:.2f}M"
        elif balance >= 1_000:
            formatted_balance = f"{balance / 1_000:.2f}K"
        else:
            formatted_balance = f"{balance:.2f}"
        formatted_balance = formatted_balance.replace('.', '․')
        activity = discord.Activity(type=discord.ActivityType.watching, name=f"Balance: {formatted_balance}")
        await client.change_presence(activity=activity)
        new_name = f"💸 {formatted_balance} HTN LISTING"
        await channel.edit(name=new_name)
        print(f"Updated channel name to: {new_name}")

    except Exception as e:
        print(f"An error occurred: {e}")

async def fetch_price():
    response = requests.get(API_URL + "/info/price")
    data = response.json()
    price = data['price']
    return price

async def update_price(channel):
    try:
        price = await fetch_price()
        formatted_price = f"{price:.6f}".replace('.', '․')
        activity = discord.Activity(type=discord.ActivityType.watching, name=f"Price: ${formatted_price}")
        await client.change_presence(activity=activity)
        new_name = f"💰 ${formatted_price} HTN"
        await channel.edit(name=new_name)
        print(f"Updated channel name to: {new_name}")
    except Exception as e:
        print(f"An error occurred: {e}")


async def fetch_hashrate(): 
    response = requests.get(API_URL + "/info/hashrate?stringOnly=false")
    data = response.json()
    hashrate = data['hashrate']
    return hashrate


async def update_hashrate(channel):
    try:
        hashrate = await fetch_hashrate()
        formatted_hashrate = f"{hashrate:.2f}".replace('.', '․')
        activity = discord.Activity(type=discord.ActivityType.watching, name=f"Hashrate: {formatted_hashrate} Th/s")
        await client.change_presence(activity=activity)
        new_name = f"⛏️ {formatted_hashrate} Th/s"
        await channel.edit(name=new_name)
        print(f"Updated channel name to: {new_name}")
    except Exception as e:
        print(f"An error occurred: {e}")


async def fetch_marketcap(): 
    response = requests.get(API_URL + "/info/marketcap?stringOnly=false")
    data = response.json()
    marketcap = data['marketcap']
    return marketcap


async def update_marketcap(channel):
    try:
        marketcap = await fetch_marketcap()
        marketcapDivided = marketcap / 1000
        formatted_marketcap = f"{marketcapDivided:.2f} K"
        if marketcap >= 1000000: 
            marketcapDivided = marketcap / 1000000
            formatted_marketcap = f"{marketcapDivided:.2f} M"
        activity = discord.Activity(type=discord.ActivityType.watching, name=f"marketcap: {formatted_marketcap} USDT")
        await client.change_presence(activity=activity)
        new_name = f"💹 {formatted_marketcap} USDT"
        await channel.edit(name=new_name)
        print(f"Updated channel name to: {new_name}")
    except Exception as e:
        print(f"An error occurred: {e}")


async def update_channel_name():
    await client.wait_until_ready()
    priceChannel = client.get_channel(PRICE_CHANNEL_ID)
    if priceChannel is None:
        print(f"Channel with ID {PRICE_CHANNEL_ID} not found.")
        return
    hashrateChannel = client.get_channel(HASHRATE_CHANNEL_ID)
    if hashrateChannel is None:
        print(f"Channel with ID {HASHRATE_CHANNEL_ID} not found.")
        return
    marketcapChannel = client.get_channel(MARKETCAP_CHANNEL_ID)
    if marketcapChannel is None:
        print(f"Channel with ID {MARKETCAP_CHANNEL_ID} not found.")
        return
    hoosatListingWalletChannel = client.get_channel(HOOSAT_LISTING_WALLET_CHANNEL)
    if hoosatListingWalletChannel is None:
        print(f"Channel with ID {HOOSAT_LISTING_WALLET_CHANNEL} not found.")
        return
    tronUSDTListingWalletChannel = client.get_channel(TRON_USDT_LISTING_WALLET_CHANNEL)
    if tronUSDTListingWalletChannel is None:
        print(f"Channel with ID {TRON_USDT_LISTING_WALLET_CHANNEL} not found.")
        return
    while not client.is_closed():
        await update_price(priceChannel)
        await update_hashrate(hashrateChannel)
        await update_marketcap(marketcapChannel)
        await update_funding_htn_wallet_balance(hoosatListingWalletChannel)
        await update_funding_tron_usdt_wallet_balance(tronUSDTListingWalletChannel)
        await asyncio.sleep(60)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    client.loop.create_task(update_channel_name())

client.run(TOKEN)