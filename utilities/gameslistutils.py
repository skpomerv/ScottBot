from discord.ext import commands
import os
import discord
import urllib
import time
from discord.ext.commands import Bot

class GamesListUtils(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    game_directory_location = os.getenv('GAMES_DIR')
    
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

        
    @commands.command(hidden=True)
    async def listgames(self, ctx):
        if ctx.author.guild_permissions.administrator == False:
            return
        for resp in self.generate_games_list():
                embed=discord.Embed(title="Games List",
                url=os.getenv('GAMES_URL')  ,
                description=resp,
                color=0xFF5733)
                await ctx.send(embed=embed)    

