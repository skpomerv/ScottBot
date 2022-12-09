from discord.ext import commands
import os
import discord
import urllib
import time
from discord.ext.commands import Bot

# A small class to list the games in one of my directories and spit out fast URLS for them.
# This is spammy so only administrators of a discord server can call this.
class GamesListUtils(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.game_directory_location = os.getenv('GAMES_DIR')
        print("GAMES_DIR detected as {}".format(self.game_directory_location)) 


    # generates a list of the games in GAMES_DIR and spits out their GAMES_URL+extension
    # so people can download the games easier 
    def generate_games_list(self):
        base_url=os.getenv('GAMES_URL')
    
        response_list=[]
        rstr=""
    
        glist = os.listdir(self.game_directory_location)
        glist.sort()
    
        for t in glist:
            new_string = "[{}]({})\n".format(t, base_url+urllib.parse.quote(t))
    
            if ((len(rstr) + len(new_string)) > 2999):
                response_list.append(rstr)
                rstr = ""
    
            rstr=rstr + new_string
       
        response_list.append(rstr)
    
        return response_list 

    # Lists all games in a directory and spits out their corresponding urls. 
    @commands.command(hidden=True)
    async def listgames(self, ctx):
        if ctx.author.guild_permissions.administrator == False:
            return
        # Delete bot posts of the last 20 messages
        past_messages= await ctx.channel.history(limit=20).flatten()
        for message in past_messages:
            if message.author == self.bot.user:
                await message.delete()

        for resp in self.generate_games_list():
                embed=discord.Embed(title="Games List",
                url=os.getenv('GAMES_URL')  ,
                description=resp,
                color=0xFF5733)
                await ctx.send(embed=embed)    

