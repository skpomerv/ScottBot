import nextcord
from nextcord.ext import commands
from nextcord.ext.commands import Bot

import json 
import re
import requests
#import collections
from random import sample
from random import choice
from random import randint
from thefuzz import process

class HBrawlMaker(commands.Cog):

    serverTextChannel = []

    def __init__(self, bot, data_dir):
        # Discord specific stuff
        super().__init__()
        self.bot = bot

        # Brawl Deck maker stuff
        self.original_json =    data_dir + '/AtomicCards.json' 
        self.legal_json =       data_dir + '/LegalCMDR.json'
        self.cmdr_json =        data_dir + '/CandidateCMDR.json'
        self.land_json =        data_dir + '/Lands.json'

        print("Downloading the MTGJSON AtomicCards.json file, this make take a moment...");
        # Thanks MTGJSON!
        json_url = 'https://mtgjson.com/api/v5/AtomicCards.json'
        req = requests.get(json_url, allow_redirects=True)
        open(self.original_json, 'wb').write(req.content)        

        print("Done. Some partner jsons will be generated to make life easier to work with.")


        # Make some of the JSONs a bit easier to work with
        self.generateLegalJSON()
        self.generateLandJSON()
        self.generateCandidateCommanderJSON()

        
    ### Tools for Loading Dictionaries ###

    def getDict(self):
        cardDict = None
        with open(self.original_json) as json_file:
            cardDict = json.load(json_file)["data"]
        return cardDict

    def getLegalDict(self):
        cardDict = None
        with open(self.legal_json) as json_file:
            cardDict = json.load(json_file)
        return cardDict         

    def getCommanderDict(self): 
        cardDict = None
        with open(self.cmdr_json) as json_file:
            cardDict = json.load(json_file)
        return cardDict

    def getLandDict(self): 
        cardDict = None
        with open(self.land_json) as json_file:
            cardDict = json.load(json_file)
        return cardDict

    ### JSON Generators ###

    # Makes a json of all known legal nonland cards.
    def generateLegalJSON(self):
        myDict = {}
        cardDict = self.getDict()

        for key, val in cardDict.items():
            if (('legalities' in val[0]) and ('types' in val[0])):
                if (('historicbrawl' in val[0]["legalities"]) & ('Land' not in val[0]['types'])) :
                    if (val[0]["legalities"]["historicbrawl"] != "Banned"):
                        if ('text' in val[0]) and ("draft" in val[0]['text']):
                            continue
                        myDict[key] = val

        f = open(self.legal_json, "w")
        json.dump(myDict, f)
        f.close()


    # Makes a json of all legal lands
    def generateLandJSON(self):
        myDict = {}
        cardDict = self.getDict()

        for key, val in cardDict.items():
            if (('legalities' in val[0]) and ('types' in val[0])):
                if (('historicbrawl' in val[0]["legalities"]) & ('Land' in val[0]['types'])) :
                    if (val[0]["legalities"]["historicbrawl"] != "Banned"):
                        if ('text' in val[0]) and ("draft" in val[0]['text']):
                            continue
                        myDict[key] = val

        f = open(self.land_json, "w")
        json.dump(myDict, f)
        f.close()

    # Makes a json of all known legal commanders
    def generateCandidateCommanderJSON(self): 
        myDict = {}
        #Let's save some time and get the legal dictionary instead of the illegal one.
        cardDict = self.getLegalDict()

        for key, val in cardDict.items():
            # If it's a legendary creature or planeswalker, it can be a commander
            if (('supertypes' in val[0]) & ('types' in val[0])): # I don't trust python short circuiting
                if (('Legendary' in val[0]['supertypes']) & ( ('Planeswalker' in val[0]['types']) or ('Creature' in val[0]['types']))):
                    if ('text' in val[0]) and ("draft" in val[0]['text']): #okay maybe I do
                        continue
                    myDict[key] = val 

        f = open(self.cmdr_json, "w")
        json.dump(myDict, f)
        f.close()


    ### Deck Generators ###

    # Gets all color identity colors that aren't in this list of provided cards.
    # Returns two lists, first list is the legal one, the illegal one is the second list
    def getColors(self, cardList):
        # Though I anticipate I'll only use this for commanders I'm being conservative
        # and loading all cards...
        cardData = self.getDict() 
        
        current_legal_colors = ['W', 'U', 'B', 'R', 'G']
       
        # This loop looks slow but card colors and the number of cards provided to getColors is
        # always small
        for card in cardList:
            for color in cardData[card][0]['colorIdentity']:
                if color in current_legal_colors:
                    current_legal_colors.remove(color)
 
        return [x for x in ['W', 'U', 'B', 'R', 'G'] if x not in current_legal_colors ], current_legal_colors
    
    # Gets a dictionary and selects a random card from it.
    # Color restrictions is an array of characters 'w' 'u' 'b' 'r' and 'g'. These are the "illegal colors"
    # cardCount is an integer of how many cards to return
    # card_restrictions are cards not allowed to be selected by the algorithm, perhaps because a
    #           previous step already added it to the deck (the commander cant also be in the 99)
    # role should either be 'land', 'commander', 'partner' or 'nonland' to determine the working data set.
    def getXRandomCardsFromDict(self, color_restrictions, card_restrictions, cardCount, role):
        cardList = []
        cardDict = None
        if role == 'commander':
            cardDict = self.getCommanderDict()
        elif role == 'partner':
            cardDict = self.getPartnerDict()
        elif role == 'nonland':
            cardDict = self.getLegalDict()
        elif role == 'land':
            cardDict = self.getLandDict()
        else:
            return None;
        # Filter cards that contain our filter colors.
        # I could statically compute these but that performance gain probably isn't worth it. 
        for key, val in cardDict.items():
            if key not in card_restrictions:
                addCard = True

                for c in color_restrictions:
                    if (c in val[0]['colorIdentity']):
                        addCard = False
                        break

                if addCard:
                    cardList.append(key)

        if cardCount > len(cardList):
            return None

        # Grab n cards from the list
        # Unlike random.choices, sample grabs without relacement so there arent duplicate choices.
        return sample(cardList, cardCount) 

    # Generates a (probably) terrible Brawl deck
    # At the moment there are no color restriction options
    # Returns a map that maps keys (cardnames) to a small dict of ['isCMDR', and 'count']
    def makeDeck(self, cmdrList=[]):
        colorToLand = { "W":"Plains", "B":"Swamp", "U":"Island", "G":"Forest", "R":"Mountain" }
        deckList = []

        # get a commander if we don't have one yet
        if len(cmdrList) == 0:
            # get commander
            cmdrList = self.getXRandomCardsFromDict([], [], 1, 'commander')

        landCount = randint(33,42)
        basicLandCount = int(landCount * .66)
        nonlandCount = 100-len(cmdrList)-landCount

        # Find out the colors I am using and the colors I'm not.
        legalColors, illegalColors = self.getColors(cmdrList)

        # I know it's backwards, but we're starting with the basic lands.

        # The below code block is equivalent to
        # if len(legalColors) <= 1 then basicMul = basicLandCount
        # else basicMul = basicLandCount / len(legalColors)
        # It is done this way to make sure the variable exists in the
        # scope, and as a bonus the branch prediction should make this
        # run like 0.00...001% faster! 
        basicMul = basicLandCount
        basicTypes = 1
        if len(legalColors) > 1:
            basicMul = int( basicLandCount / len(legalColors) ) 
            basicTypes = len(legalColors)

        # Computing the nonbasic land count as basicMul * basics probably has a remainder.
        nonBasicLandCount = landCount - (basicMul * basicTypes)


        # omit illegal colors, ban previously added cards from being readded, add nonlandcount cards (minus number of commanders)
        nonLandList = self.getXRandomCardsFromDict(illegalColors, cmdrList, nonlandCount, 'nonland')
        nbLandList = self.getXRandomCardsFromDict(illegalColors, cmdrList+nonLandList, int(nonBasicLandCount), 'land')

        deckList = deckList + nonLandList + nbLandList

        # For the sake of ease I'm going to actually make this a dict with an inner dict of "isCMDR" and "count"
        # for the value. I should have make the lists a dict from the get-go but I forgot I could have
        # multiple basic lands when I first planned this method rip lmao.
        # The reason I use an inner dict as opposed to a list is for understandability, not speed.
        finalDict = {}
        for c in cmdrList:
            innerMap = { "isCMDR":True, "count":1 }
            finalDict[c] = innerMap

        for c in deckList:
            innerMap = {"isCMDR":False, "count":1 }
            finalDict[c] = innerMap

        # Mapping basic lands is only mostly trivial
        randBasic = ""
        if len(legalColors) == 0:
            finalDict["Wastes"] = { "isCMDR":False, "count":basicMul }
            randBasic = "Wastes"
        else:
            randBasic = colorToLand[choice(legalColors)]
            for color in legalColors:
                finalDict[colorToLand[color]] = { "isCMDR":False, "count":basicMul }

        # Sanity check, if we are missing a card or two, we can just add some basic lands.
        # Some people reported this as an issue, but I am not able to recreate this yet...
        rounding_err = 100 - sum(finalDict[k]["count"] for k in finalDict)
        if rounding_err > 0:
            print("Deck produced a list with a weird length? Repairing...")
            print("CardCount is {}, Dict:\n{}".format(100-rounding_err, finalDict))
            finalDict[randBasic]["count"] = basicMul + rounding_err

        return finalDict


    # Converts the deck arg into a string that looks pretty to humans
    def dictToString(self, deck):
        myString = ""
        for key in deck:
            myString = myString + "{}x {}".format(deck[key]['count'], key)
            if deck[key]['isCMDR']:
                myString = myString + " *CMDR*"
            myString = myString + "\n"
        return myString


    #Takes a commander name and returns the dictionary entry of the best match.
    def findBestCardMatch(self, cmdrname, cmdrDict):
        return process.extractOne(cmdrname,cmdrDict.keys())

    # grabs all commanders of a given color identity then returns an commander or set
    # of commanders.
    def getCMDROnColor(self, color_identity):
        #in this we make a list of list entries. It's a bit wonky but makes life easier
        legalCmdrs = []
        allCmdrs = self.getCommanderDict()
        # remove ordering for comparisons against commanders,
        # duplicates don't matter
        cidset = set(color_identity)

        # It's a bit naive but I'm just gonna assemble all legal commander combos and pick one
        for k, v in allCmdrs.items():
            if cidset == set(v[0]['colorIdentity']):
                    legalCmdrs.append([k]) # k is a list here so we can support pairs of commanders.

            if len(legalCmdrs) == 0:
                return None

            return sample(legalCmdrs, 1)[0]
                                

        # Looks at entries in Tuple t and returns a list containing each word.
    def tupleToColorID(self, t):
        cid = []
        colorConverter = { "white":"W", "black":"B", "blue":"U", "green":"G", "red":"R",
                           "w":"W", "b":"B", "g":"G", "u":"U", "r":"R"  }
        for k,v in colorConverter.items():
            if k.lower() in (color.lower() for color in t):
                cid.append(v)
        return cid



    ### Begin Random Card Shit ###

    # Creates a easier-to-work-with mana dict. explicitColorless indicates whether the mana provided MUST be colorless. I.E. is the mana provided by a player or a cost for a card.
    def convertManaToDict(self, manaCost, explicitColorless=True):
        manaDict = { } #initialize colorless since it's not initialized.
        
        if explicitColorless:
            manaDict['c'] = 0
        else:
            manaDict['colorless'] = 0

        tokens = re.findall("{(.*?)}", manaCost) #.* is not super fast, but it's good enough for this

        td = self.getLegalDict()

        #tokenize string
        #print("Tokenized String: {}".format(tokens))

        for t in tokens:
            if t.isnumeric():
                if explicitColorless:
                    manaDict['c'] = manaDict['c'] + int(t)
                else:
                    manaDict['colorless'] = manaDict['colorless'] + int(t)
                continue
            newKey = t.lower()
            if "/" in newKey:
                newKeyList = newKey.split("/")
                newKeyList.sort()
                newKey = "/".join(newKeyList)
            if newKey in manaDict:
                manaDict[newKey] = manaDict[newKey] + 1
            else:
                manaDict[newKey] = 1

        return manaDict

    ### Small Sanity Check to see if a command is in the correct channel. Returns true if the post should be ignored. ###
    def channel_check(self, ctx):
        return not((len(self.serverTextChannel) == 0) or (ctx.channel.id in self.serverTextChannel))

    ### Begin Discord Commands ###

    @commands.command(brief='Sets this text channel for Brawl function', description='Sets this text channel for Brawl function and prohibits use of brawl cog commands in other channels', hidden=True)
    async def setBrawlChannel(self, ctx, *args):
        if ctx.author.guild_permissions.administrator == False:
            return

        self.serverTextChannel.append(ctx.channel.id)
        await ctx.send(f"Set Brawl channel list to: {self.serverTextChannel}")
        return

    @commands.command(brief='Sets this text channel for Brawl function', description='Sets this text channel for Brawl function and prohibits use of brawl cog commands in other channels', hidden=True)
    async def resetBrawlChannel(self, ctx, *args): 
        if ctx.author.guild_permissions.administrator == False:
            return
        self.serverTextChannel = []
        await ctx.send("Reset Brawl channel to have no restrictions.")
        return

    @commands.command(brief='Generates a Historic Brawl deck. Do "!brawl help" for more info.', description='Makes a random Brawl deck that is probably not good. Note double faced cards (which use "//" may need to be hand modified to be supported by whatever you shove this into. For further help type "!brawl help"')
    async def brawl(self, ctx, *args):

        if self.channel_check(ctx):
            return

        # If no arguments, make an historic brawl deck using whatever.
        if len(args) == 0:
            myString = self.dictToString(self.makeDeck())
            await ctx.send("Here's your deck!\n```" + myString + "```")
            return

        # Help options
        elif args[0].lower() == "help":
            myString =  """ Here is what I have so far:
`!brawl` - generates a random deck with a random commander and random colors.
`!brawl commander "Kozilek, the Great Distortion"` - generates a deck with Kozilek, the Great Distortion as the commander. This searches for the closest legal Commander.
`!brawl nonland "Relic of Progenitus" - Generates a deck with Relic of Progenitus as the commander. The quotes are necessary. 'Card' searches for the closest legal nonland.
`!brawl land "Boseju, Who Endures"` - The same as above, but for nonbasic lands. Can also get the same partner treatment.
`!brawl colors red white blue` - generates a deck with a commander or that has the color identity of red, white, and blue.
`!brawl colors none` - generates a colorless brawl deck.
                        """
            await ctx.send(myString)
            return

        # if arg[0] is "commander" then args[1] (and potentially args[2]) are commanders
        elif (args[0].lower() == "commander"):         
            if len(args) < 2:
                await ctx.send("No commander specified. Either call this with a commander or do not add the commander arg.")
                return
            
            potential_cmdr_list = [] 
            potential_cmdr_list.append(self.findBestCardMatch(args[1], self.getCommanderDict())[0])
               
            myString = self.dictToString(self.makeDeck(cmdrList=potential_cmdr_list))
            await ctx.send("Here's your deck with commander {}:\n```{}```".format(potential_cmdr_list, myString))
            return

        elif (args[0].lower() == "nonland"):
            if len(args) < 2:
                await ctx.send("No commander specified. Either call this with a card or do not add the forcecmdr arg.")
                return
            potential_cmdr_list = [] 
            potential_cmdr_list.append(self.findBestCardMatch(args[1], self.getLegalDict())[0])
               
            myString = self.dictToString(self.makeDeck(cmdrList=potential_cmdr_list))
            await ctx.send("Here's your deck with commander {}:\n```{}```".format(potential_cmdr_list, myString))
            return

        elif (args[0].lower() == "land"):
            if len(args) < 2:
                await ctx.send("No commander specified. Either call this with a card or do not add the forcecmdr arg.")
                return
            potential_cmdr_list = [] 
            potential_cmdr_list.append(self.findBestCardMatch(args[1], self.getLandDict())[0])
               
            myString = self.dictToString(self.makeDeck(cmdrList=potential_cmdr_list))
            await ctx.send("Here's your deck with commander(s) {}:\n```{}```".format(potential_cmdr_list, myString))
            return

        elif (args[0].lower() == "color") or (args[0].lower() == "colors"): 

            potential_cmdr_list = self.getCMDROnColor(self.tupleToColorID(args)) 
            if potential_cmdr_list is not None:
                myString = self.dictToString(self.makeDeck(cmdrList=potential_cmdr_list))
                await ctx.send("Here's your deck with color selection {}:\n```{}```".format(self.tupleToColorID(args), myString))
                return
            else:
                await ctx.send("There is no commander with this color combo in Historic Brawl :(")
                return

        else:
            await ctx.send("I'm not sure what you want? Make sure after !brawl you type the type of restriction you're giving. Check with !brawl help for current options.")
            return


