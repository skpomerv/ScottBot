#!/usr/bin/python3.9
#imports
import os
import discord
import urllib
import time
import asyncio
from discord.ext import commands
from discord.ext.commands import Bot
from dotenv import load_dotenv

# Cog Libraries
from utilities.oscommands import OSCommands
from utilities.gameslistutils import GamesListUtils
from utilities.edhmaker import EDHMaker
from utilities.kingdoms import Kingdoms
#from utilities.dungeonsanddorks import DungeonsAndDorks

def main():

    #get file directory
    bot_dir = os.path.dirname(__file__)
    if bot_dir == "":
        bot_dir = "."
    print("Working in dir '{}'".format(bot_dir))


    load_dotenv()
    TOKEN = os.getenv('DISCORD_TOKEN')


    # Generate intents for the bot
    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix='!', intents=intents)

    #Enable cogs
    loop = asyncio.get_event_loop()
    loop.run_until_complete(setup(bot, bot_dir))

    @bot.event
    async def on_ready():
        print(f'{bot.user} has connected to Discord!')
        for guild in bot.guilds:
            print(
                f'{bot.user} is connected to the following guild:\n'
                f'{guild.name}(id: {guild.id})'
            )
    
        members = '\n - '.join([member.name for member in guild.members])
        print(f'Guild Members:\n - {members}')

    bot.run(TOKEN)

async def setup(bot, bot_dir):
    await bot.add_cog(GamesListUtils(bot))
    await bot.add_cog(OSCommands(bot))
    await bot.add_cog(EDHMaker(bot, bot_dir+'/utilities/edhmaker_data' ))
    await bot.add_cog(Kingdoms(bot, bot_dir+'/utilities/kingdoms_data'))
#    await bot.add_cog(DungeonsAndDorks(bot))

if __name__ == "__main__":
    main()
