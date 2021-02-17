'''discord-stock-ticker'''
from os import getenv
from datetime import datetime
from random import choice
import logging
import asyncio
import discord
from pycoingecko import CoinGeckoAPI
from redis import Redis, exceptions

from utils.yahoo import get_stock_price_async

CURRENCY = 'usd'

ALERTS = [
    'discord.gg/CQqnCYEtG7',
    'markets be closed',
    'gme to the moon',
    'what about second breakfast'
]


class Ticker(discord.Client):
    '''
    Discord client for watching stock/crypto prices
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Check that at least a ticker is set
        if not getenv("TICKER"):
            logging.error('TICKER not set!')
            return

        # Use different updates based on security type
        if getenv('CRYPTO_NAME'):
            logging.info('crypo ticker')
            api = CoinGeckoAPI()
            self.sm_task = self.loop.create_task(self.crypto_update_name(api))
            self.bg_task = self.loop.create_task(self.crypto_update_activity(api))
        else:
            logging.info('stock ticker')
            self.sm_task = self.loop.create_task(self.stock_update_name())
            self.bg_task = self.loop.create_task(self.stock_update_activity())


    async def on_ready(self):
        '''
        Log that we have successfully connected
        '''

        logging.info('logged in')

        # Use redis to store stats
        r = Redis()

        # We want to know some stats
        servers = [x.name for x in list(self.guilds)]

        try:
            for server in servers:
                r.incr(server)
        except exceptions.ConnectionError:
            logging.info('No redis server found, not storing stats')

        logging.info('servers: ' + str(servers))


    async def stock_update_name(self):
        '''
        Update the bot name based on stock price
        '''

        # Get config
        ticker = getenv("TICKER")
        name = getenv("STOCK_NAME", ticker)
        old_price = ''

        await self.wait_until_ready()
        logging.info('name ready')

        # Loop as long as the bot is running
        while not self.is_closed():

            # Dont bother updating if markets closed
            if (datetime.now().hour >= 17) or (datetime.now().hour < 8):
                logging.info('markets are closed')
                await asyncio.sleep(3600)
                continue

            logging.info('name started')
            
            # Grab the current price data
            data = await get_stock_price_async(ticker)
            data = data.get('quoteSummary', {}).get('result', []).pop().get('price', {})
            price = data.get('regularMarketPrice', {}).get('raw', 0.00)
            logging.info(f'name price retrived {price}')

            # Only update on price change
            if old_price != price:

                await self.user.edit(
                    username=f'{name} - ${price}'
                )

                old_price = price
                logging.info('name updated')

            else:
                logging.info('no price change')

            # Only update every hour
            await asyncio.sleep(3600)

            logging.info('name sleep ended')
    

    async def stock_update_activity(self):
        '''
        Update the bot activity based on stock price
        '''

        # Get config
        ticker = getenv("TICKER")
        old_price = ''

        await self.wait_until_ready()
        logging.info('activity ready')

        # Loop as long as the bot is running
        while not self.is_closed():

            # If markets are closed, utilize activity for other messages
            if (datetime.now().hour >= 16) or (datetime.now().hour < 7):
                logging.info('markets are closed')
                await self.change_presence(
                    activity=discord.Activity(
                        type=discord.ActivityType.watching,
                        name=choice(ALERTS)
                    )
                )
                await asyncio.sleep(600)
                continue

            logging.info('activity started')
            
            # Grab the current price data w/ day difference
            data = await get_stock_price_async(ticker)
            data = data.get('quoteSummary', {}).get('result', []).pop().get('price', {})
            price = data.get('regularMarketPrice', {}).get('raw', 0.00)
            diff = price - data.get('regularMarketPreviousClose', {}).get('raw', 0.00)
            diff = round(diff, 2)
            if diff > 0:
                diff = '+' + str(diff)

            logging.info(f'activity price retrived {price}')

            # Only update on price change
            if old_price != price:

                # Change activity
                await self.change_presence(
                    activity=discord.Activity(
                        type=discord.ActivityType.watching,
                        name=f'${price} / {diff}'
                    )
                )

                logging.info('activity updated')

                # Change name via nickname if set
                if getenv('SET_NICKNAME'):
                    
                    for server in self.guilds:
                        await server.me.edit(
                            nick=f'{ticker} - ${price}'
                        )
                        logging.info(f'updated nick in {server.name}')

                old_price = price

            else:
                logging.info('no price change')

            # Only update every min
            await asyncio.sleep(int(getenv('FREQUENCY', 60)))
            logging.info('activity sleep ended')
    

    async def crypto_update_name(self, gapi: CoinGeckoAPI):
        '''
        Update the bot name based on crypto price
        '''

        # Get config
        name = getenv('CRYPTO_NAME')
        ticker = getenv("TICKER")
        old_price = ''

        await self.wait_until_ready()
        logging.info('name ready')

        # Loop as long as the bot is running
        while not self.is_closed():

            logging.info('name started')

            # Grab the current price data
            data = gapi.get_price(ids=name, vs_currencies=CURRENCY)
            price = data.get(name, {}).get(CURRENCY)
            logging.info(f'name price retrived {price}')

            # Only update on price change
            if old_price != price:

                await self.user.edit(
                    username=f'{ticker} - ${price}'
                )
                
                old_price = price
                logging.info('name updated')

            else:
                logging.info('no price change')

            # Only update every hour
            await asyncio.sleep(3600)
            logging.info('name sleep ended')
    

    async def crypto_update_activity(self, gapi: CoinGeckoAPI):
        '''
        Update the bot activity based on crypto price
        '''

        # Get config
        name = getenv('CRYPTO_NAME')
        ticker = getenv("TICKER")
        old_price = ''

        await self.wait_until_ready()
        logging.info('activity ready')

        # Loop as long as the bot is running
        while not self.is_closed():

            logging.info('activity started')       

            # Grab the current price data
            data = gapi.get_price(ids=name, vs_currencies=CURRENCY)
            price = data.get(name, {}).get(CURRENCY)
            logging.info(f'activity price retrived {price}')

            # Only update on price change
            if old_price != price:

                # Change activity
                await self.change_presence(
                    activity=discord.Activity(
                        type=discord.ActivityType.watching,
                        name=f'${price}'
                    )
                )

                logging.info('activity updated')

                # Change name via nickname if set
                if getenv('SET_NICKNAME'):
                    
                    for server in self.guilds:
                        await server.me.edit(
                            nick=f'{ticker} - ${price}'
                        )
                        logging.info(f'updated nick in {server.name}')

                old_price = price

            else:
                logging.info('no price change')

            # Only update every min
            await asyncio.sleep(int(getenv('FREQUENCY', 60)))
            logging.info('activity sleep ended')


if __name__ == "__main__":

    logging.basicConfig(
        filename='discord-stock-ticker.log',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S',
        format='%(asctime)s %(levelname)-8s %(message)s',
    )

    client = Ticker()
    client.run(getenv('DISCORD_BOT_TOKEN'))
