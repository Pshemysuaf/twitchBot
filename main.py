import json
import logging
import os
from collections import defaultdict

import requests
import yaml
from dotenv import load_dotenv
from twitchio.ext import commands

logging.basicConfig(
    filename='results.log',
    level=logging.INFO,
    format='%(asctime)s %(message)s',
    datefmt='%m/%d/%Y %I:%M:%S %p'
)
with open('items.yaml', encoding="utf-8") as f:
    items = yaml.load(f, Loader=yaml.FullLoader)
load_dotenv(encoding="utf-8")

bot = commands.Bot(
    irc_token=os.environ['TMI_TOKEN'],
    client_id=os.environ['CLIENT_ID'],
    nick=os.environ['BOT_NICK'],
    prefix=os.environ['BOT_PREFIX'],
    initial_channels=[os.environ['CHANNEL']]
)

stats = defaultdict(int)


@bot.event
async def event_ready():
    print(f"{os.environ['BOT_NICK']} {os.environ['BOT_START_MSG']}!")
    await bot._ws.send_privmsg(os.environ['CHANNEL'], f"/me {os.environ['BOT_HELLO_MSG']}")


@bot.event
async def event_message(ctx):
    author = ctx.author.name
    if author.lower() == os.environ['BOT_NICK'].lower():
        return

    await bot.handle_commands(ctx)
    item_id = ctx.content.lower()
    try:
        item_id = int(item_id)
    except ValueError:
        pass
    if item_id in items:
        item_name = items[item_id]
        try:
            data = {
                "author": author,
                "item_id": item_id,
                "item_name": item_name
            }
            requests.post(
                os.environ['TARGET_STATS'],
                data=data,
                headers={
                    "Content-type": "application/json",
                    "User-Agent": os.environ['USER_AGENT'],
                    "x-api-key": os.environ['API_KEY'],
                },
                verify=False
            )
            logging.info(json.dumps(data))
            stats[item_id] += 1
            await ctx.channel.send(f"@{author} {os.environ['BOT_REQUEST_MSG']} {item_name}!")
        except requests.exceptions.SSLError as e:
            logging.error(e)


@bot.command(name='lista')
async def items_list(ctx):
    await ctx.send(
        " :) ".join([f"{item} - {items[item]}" for item in items])
    )


@bot.command(name='ranking')
async def ranking(ctx):
    await ctx.send(
        " :) ".join([f"{items[stat]}: {stats[stat]} pkt." for stat in dict(sorted(stats.items(), key=lambda kv: kv[1], reverse=True))])
    )


if __name__ == "__main__":
    bot.run()
