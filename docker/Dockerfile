# Use the official Python image from the Docker Hub
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

ENV TOKEN=""
ENV API_URL="https://api.network.hoosat.fi"
ENV PRICE_CHANNEL_ID=""
ENV HASHRATE_CHANNEL_ID=""
ENV MARKETCAP_CHANNEL_ID=""
ENV HOOSAT_LISTING_WALLET_CHANNEL=""
ENV TRON_USDT_LISTING_WALLET_CHANNEL=""
ENV GUILD_ID=""

# Copy the requirements.txt file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Run the bot
CMD ["python", "bot.py"]
