import subprocess
from nextcord.ext import commands
from nextcord.ext.commands import Bot
from random import choice
from random import randrange 
import json
import os

# Runs some trivial simple commands and spits out results
class OSCommands(commands.Cog):

    def __init__(self, bot, data_dir):
        super().__init__()
        self.bot = bot

        # Read in the words for the !robin command        
        with open(data_dir+"words.txt") as wordfile:
            self.words_dict = wordfile.readlines()

        # Read in past quotes for the !quote and !addquote command
        self.quotefile=data_dir+"quotes.json"

    def get_saved_quotes(self):
        with open(self.quotefile) as file:
            return json.load(file)
        return None

    def add_quote(self, guild_id, quote):
        #if file does not exist, make a new file
        if not os.path.exists(self.quotefile):
            with open (self.quotefile, 'w') as file:
                file.write("{}")

        file_data = None
        with open(self.quotefile, "r+") as file:
            dkey = str(guild_id)
            #print(f"Adding {quote} to {guild_id}")
            file_data = json.load(file)

            #print(f"file_data: {file_data}")

            if dkey not in file_data:
                file_data[dkey] = []

            #print("file_data[guild_id]")
            file_data[dkey].append(quote)
            #print(f"file_data: {file_data}")
            # Go back to start of file
         
        with open(self.quotefile, "w") as file:
            json.dump(file_data, file, indent=2)

        return len(file_data[dkey]) - 1


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
        proc = subprocess.Popen(["/usr/games/fortune"], stdout=subprocess.PIPE)
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

    @commands.command(brief='Inserts a random word into the string "Holy _, Batman!"', description='Inserts a random word into the string "Holy _, Batman!"')
    async def robin(self, ctx):
        await ctx.send(f"Holy {choice(self.words_dict).strip()}, Batman!")
        return          

    @commands.command(brief='Adds a random quote to the quote pool.', description='Inserts a quote into the pool of random quotes. Make sure to credit the source!')
    async def addquote(self, ctx, *args):
        quote = " ".join(args)
        nqn = self.add_quote(ctx.guild.id, quote)
        await ctx.send(f"Added the quote (#{nqn})!") 


    @commands.command(brief='Returns a random quote (or quote with specific number)', description='Says a random quote!')
    async def quote(self, ctx, *args):
        try:
            savedquotes = self.get_saved_quotes()[str(ctx.guild.id)]

            quotenum = randrange(1,len(savedquotes)+1)
            if len(args) > 0:
                quotenum = int(args[0])
                if (quotenum < 1):
                    await ctx.send(f"I need a positive number!")
                    return
                    
                if quotenum > len(savedquotes):
                    await ctx.send(f"We only have {len(savedquotes)} quotes saved!")
                    return
                
            await ctx.send(f"Quote #{quotenum}: {savedquotes[quotenum-1]}")
        except:
            await ctx.send("Had issues with loading quotes, or your argument wasn't a number within 0 and the number of quotes!")
        
