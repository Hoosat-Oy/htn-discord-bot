import os
import discord 
import requests
import asyncio

# Replace this with your bot's token
TOKEN = os.getenv('TOKEN')
PRICE_CHANNEL_ID = int(os.getenv('PRICE_CHANNEL_ID'))
HASHRATE_CHANNEL_ID = int(os.getenv('HASHRATE_CHANNEL_ID'))
MARKETCAP_CHANNEL_ID = int(os.getenv('MARKETCAP_CHANNEL_ID'))
API_URL = os.getenv('API_URL')

client = discord.Client(intents=discord.Intents.default())

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
        new_name = f"💰 ${formatted_price} USDT"
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
    while not client.is_closed():
        await update_price(priceChannel)
        await update_hashrate(hashrateChannel)
        await update_marketcap(marketcapChannel)
        await asyncio.sleep(3600)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    client.loop.create_task(update_channel_name())

client.run(TOKEN)