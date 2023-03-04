import subprocess
from nextcord.ext import commands
from nextcord.ext.commands import Bot

# Runs some trivial simple commands and spits out results
class OSCommands(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    def shift(self, inp, shamt):
        res = ""
        for ch in inp:
            if not ch.isalpha():
                res = res + ch
                continue
    
            choff = ord('A') if ch.isupper() else ord('a')
            res = res + chr((ord(ch) + shamt-choff)%26 + choff)
        return res

    # Runs the fortune command
    @commands.command(brief='Generates a random fortune!', description='Generates a random fortune using the linux command "fortune" and posts it for all to see.')
    async def fortune(self, ctx):
        proc = subprocess.Popen(["/usr/games/fortune"], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()
        await ctx.send("```" + out.decode('utf-8') + "```")

    # Runs a cipher
    @commands.command(brief='Performs a cipher on the given string', description='Performs a set of ceasar cipers on a astring and posts it for all to see, for multiple words, wrap the arg in quotes')
    async def cipher(self, ctx, *args):
        if len(args) < 1:
            await ctx.send("This command needs an argument!")
            return

        rstring = "Result:\n```"

        for i in range(0,26):
            rstring = rstring + (f"Shift {i} = {self.shift(args[0].rstrip(),i)}\n")

        rstring = rstring + "```"
        await ctx.send(rstring)

