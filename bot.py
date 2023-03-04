#!/usr/bin/python3.9

# Requires the following pip installs
# nextcord
# python_dotenv
# python-Levenshtein
# thefuzz

#imports
import os
import nextcord
import urllib
import time
from nextcord.ext import commands
from nextcord.ext.commands import Bot
from dotenv import load_dotenv

# Cog Libraries
from utilities.oscommands import OSCommands
from utilities.gameslistutils import GamesListUtils
from utilities.edhmaker import EDHMaker
from utilities.kingdoms import Kingdoms
from utilities.dungeonsanddorks import DungeonsAndDorks
from utilities.cardmaker import CardMaker

def main():
    #get file directory
    bot_dir = os.path.dirname(__file__)
    if bot_dir == "":
        bot_dir = "."
    print("Working in dir '{}'".format(bot_dir))

    load_dotenv()
    TOKEN = os.getenv('DISCORD_TOKEN')
    GUILDS = os.getenv('DND_GUILDS')

    # Generate intents for the bot
    intents = nextcord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix='!', intents=intents)
    
    #Enable cogs
    bot.add_cog(GamesListUtils(bot))
    bot.add_cog(OSCommands(bot))
    bot.add_cog(EDHMaker(bot, bot_dir+'/utilities/edhmaker_data' ))
    bot.add_cog(Kingdoms(bot, bot_dir+'/utilities/kingdoms_data'))
    bot.add_cog(DungeonsAndDorks(bot, GUILDS.split(",")))
    #bot.add_cog(CardMaker(bot, GUILDS.split(","),bot_dir+'/utilities/edhmaker_data',os.getenv('FAKE_CARD_DIR')))

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


if __name__ == "__main__":
    main()
