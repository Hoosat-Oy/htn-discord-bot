# HTN Discord Bot

Discord bot that:

- Renames configured voice/text channels to show HTN stats (price/hashrate/marketcap + funding wallet balances)
- Provides slash commands for on-demand stats

## Slash commands

- `/ping` — bot latency
- `/price` — current HTN price
- `/hashrate` — current hashrate
- `/marketcap` — current market cap
- `/status` — price/hashrate/marketcap in one embed
- `/wallets` — funding wallet balances (HTN + TRC20 USDT)

## Configuration (env vars)

Required:

- `TOKEN`

Optional (enables fetching):

- `API_URL` (default used in Dockerfiles: `https://api.network.hoosat.fi`)

Optional (enables background channel renames):

- `PRICE_CHANNEL_ID`
- `HASHRATE_CHANNEL_ID`
- `MARKETCAP_CHANNEL_ID`
- `HOOSAT_LISTING_WALLET_CHANNEL`
- `TRON_USDT_LISTING_WALLET_CHANNEL`

Optional (faster command sync while developing):

- `GUILD_ID` (sync commands to a single server)

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export TOKEN="..."
export API_URL="https://api.network.hoosat.fi"
python bot.py
```

## Run with Docker

Build:

```bash
docker build -t htn-discord-bot .
```

Run:

```bash
docker run --rm \
	-e TOKEN="..." \
	-e API_URL="https://api.network.hoosat.fi" \
	-e PRICE_CHANNEL_ID="..." \
	-e HASHRATE_CHANNEL_ID="..." \
	-e MARKETCAP_CHANNEL_ID="..." \
	-e HOOSAT_LISTING_WALLET_CHANNEL="..." \
	-e TRON_USDT_LISTING_WALLET_CHANNEL="..." \
	htn-discord-bot
```
