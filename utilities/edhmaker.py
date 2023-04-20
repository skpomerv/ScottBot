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

class EDHMaker(commands.Cog):

    serverTextChannel = []

    def __init__(self, bot, data_dir):
        # Discord specific stuff
        super().__init__()
        self.bot = bot

        # EDH Deck maker stuff
        self.original_json =    data_dir + '/AtomicCards.json' 
        self.legal_json =       data_dir + '/LegalCMDR.json'
        self.cmdr_json =        data_dir + '/CandidateCMDR.json'
        self.partner_json =     data_dir + '/PartnerCMDR.json'
        self.land_json =        data_dir + '/Lands.json'

        # Thanks MTGJSON!
        json_url = 'https://mtgjson.com/api/v5/AtomicCards.json'
        req = requests.get(json_url, allow_redirects=True)
        open(self.original_json, 'wb').write(req.content)        

        # Make some of the JSONs a bit easier to work with
        self.generateLegalJSON()
        self.generateLandJSON()
        self.generateCandidateCommanderJSON()
        self.generatePartnersJSON()

        
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
    
    def getPartnerDict(self):
        cardDict = None
        with open(self.partner_json) as json_file:
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
                if (('commander' in val[0]["legalities"]) & ('Land' not in val[0]['types'])) :
                    if (val[0]["legalities"]["commander"] != "Banned"):
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
                if (('commander' in val[0]["legalities"]) & ('Land' in val[0]['types'])) :
                    if (val[0]["legalities"]["commander"] != "Banned"):
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

        #if a card is a legendary creature, it can be a commander
        for key, val in cardDict.items():
            notAdded = True

            # If it's a legendary creature, it can be a commander
            if (('supertypes' in val[0]) & ('types' in val[0])): # I don't trust python short circuiting
                if (('Legendary' in val[0]['supertypes']) & ('Creature' in val[0]['types'])):
                    if ('text' in val[0]) and ("draft" in val[0]['text']): #okay maybe I do
                        continue
                    myDict[key] = val 
                    notAdded = False
            # If the card is not a legendary creature, it may still be a commander if the rules text says so
            if notAdded:
                if ('text' in val[0]):
                    if("can be your commander" in val[0]['text']):
                        myDict[key] = val 

        f = open(self.cmdr_json, "w")
        json.dump(myDict, f)
        f.close()


    # Makes a json of all known partner commanders
    def generatePartnersJSON(self): 
        myDict = {}
        #Let's save some time and get the legal dictionary instead of the illegal one.
        cardDict = self.getCommanderDict()

        #if a card is a legendary creature, it can be a commander
        for key, val in cardDict.items():
            # If the card is not a legendary creature, it may still be a commander if the rules text says so
            if ('text' in val[0]):
                if (("partner" in val[0]['text']) | ( "friends forever" in val[0]['text']) ):
                    myDict[key] = val 

        f = open(self.partner_json, "w")
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

    # Returns true if a card is a partner card, false otherwise
    def isPartner(self, card):
        cardDict = self.getPartnerDict()
        return card in cardDict
    
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

    # Generates a (probably) terrible EDH deck
    # At the moment there are no color restriction options
    # Returns a map that maps keys (cardnames) to a small dict of ['isCMDR', and 'count']
    def makeDeck(self, cmdrList=[]):
        colorToLand = { "W":"Plains", "B":"Swamp", "U":"Island", "G":"Forest", "R":"Mountain" }
        deckList = []

        # get a commander if we don't have one yet
        if len(cmdrList) == 0:
            # get commander
            cmdrList = self.getXRandomCardsFromDict([], [], 1, 'commander')
            if self.isPartner(cmdrList[0]):
                cmdrList.append(self.getXRandomCardsFromDict([], [], 1, 'partner')[0])

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
        if len(legalColors) == 0:
            finalDict["Wastes"] = { "isCMDR":False, "count":basicMul }
        for color in legalColors:
            finalDict[colorToLand[color]] = { "isCMDR":False, "count":basicMul }


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
    def findBestCMDRMatch(self, cmdrname):
        return process.extractOne(cmdrname,self.getCommanderDict().keys())

    # grabs all commanders of a given color identity then returns an commander or set
    # of commanders.
    def getCMDROnColor(self, color_identity):
        #in this we make a list of list entries. It's a bit wonky but makes life easier
        legalCmdrs = []
        allCmdrs = self.getCommanderDict()
        allPartners = self.getPartnerDict()
        # remove ordering for comparisons against commanders,
        # duplicates don't matter
        cidset = set(color_identity)

        # It's a bit naive but I'm just gonna assemble all legal commander combos and pick one
        for k, v in allCmdrs.items():
            if cidset == set(v[0]['colorIdentity']):
                legalCmdrs.append([k]) # k is a list here so we can support pairs of commanders.

        # slow, but all partner combos here are pretty small.
        for k,v in allPartners.items():
            if set(v[0]['colorIdentity']).issubset(cidset): 
                
                partner1 = k
                p2mincolors = set(cidset).difference(v[0]['colorIdentity'])

                for k2, v2 in allPartners.items():
                    # if we aren't looking at ourselves and
                    # partner 2's color identity is a superset of the minimum colors and
                    # partner 2's color identity is a subset of the total colors and
                    # we have not put a reverse ordering in the list already
                    if (k != k2) and (p2mincolors.issubset(set(v2[0]['colorIdentity']))) and (cidset.issuperset(set(v2[0]['colorIdentity']))) and ([k2, k] not in legalCmdrs):
                        legalCmdrs.append([k, k2])
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

    # Recursively tries to see if it is possible to cast a card
    def __isCardCastableDecision(self, cardMana, providedMana):
        #print(" Testing case:\n  {}\n  {}\n  cml={}".format(cardMana, providedMana, len(cardMana.keys())))

        if sum(cardMana.values()) > sum(providedMana.values()): #base case, for cards like reaper king
        #    print("x cardMana < providedMana")
            return False

        if len(cardMana.keys()) == 1:
            if cardMana['colorless'] <= sum(providedMana.values()):
        #        print("colorless total is less than providedmana total")
                return True
            return False

        #grab a random key from cardMana
        ccombo = None
        for k in cardMana:
            if k != "colorless":
                ccombo = k
                break

        ncm = cardMana.copy()
        ncm[k] = ncm[k]-1
        if ncm[k] <= 0:
            ncm.pop(k)

        for c in ccombo.split("/"):

            if c.isnumeric():
                ncm2 = ncm.copy() #gross, but rare
                if 'colorless' in ncm2:
                    ncm2['colorless'] = ncm2['colorless'] + int(c)
                else:
                    ncm2['colorless'] = int(c)
                if self.__isCardCastableDecision(ncm2, providedMana):
                    return True

            elif c in providedMana:
                npm = providedMana.copy()
                npm[c] = npm[c] - 1 
                if npm[c] <= 0:
                    npm.pop(c)
                if self.__isCardCastableDecision(ncm, npm):
                    return True

        #print("Fell through!")
        return False


    # Returns true if the card's mana cost is a subset of the provided mana cost. If providedMana is none, automatically return true.
    def isCardCastable(self, cardMana, providedMana):

        if (providedMana == None) or (len(cardMana) == 0):
            return True

        if sum(cardMana.values()) > sum(providedMana.values()):
            return False

        cMana = cardMana.copy()
        pMana = providedMana.copy()

        if "colorless" not in cMana.keys():
            cMana['colorless'] = 0


        keysToPop = []

        # For the simple case of W B U R G
        for k in cMana.keys():
            # for the simple-case
            if ("/" in k) or (k == "colorless"):
                continue
            if k in pMana:
                pMana[k] = pMana[k] - cMana[k]
                keysToPop.append(k)
                if pMana[k] < 0:
                    return False
            else:
                return False

        for ktp in keysToPop:
            cMana.pop(ktp)

        #print("Entering Recursive Case:\n  cMana={}\n  pMana={}".format(cMana, pMana))
            
        return self.__isCardCastableDecision(cMana, pMana) 
        


    # Gets a random card that is legal in commander based on restrictions.
    def getRandomCard(self, color_restrictions=[], type_restrictions=[ 'Planeswalker', 'Creature', 'Sorcery', 'Instant', 'Artifact', 'Enchantment','Instant','Land' ], cmc_restriction=-1, cmcstrict=False, ccost=None):
        cardList = []
        cardDict = self.getLegalDict()
        
        # Filter cards that contain our filter colors.
        # I could statically compute these but that performance gain probably isn't worth it. 
        for key, val in cardDict.items():
            addCardColor = True  

            for c in color_restrictions:
                if (c in val[0]['colorIdentity']):
                    addCard = False
                    break
            if not addCardColor:
                continue

            addCardType = False
            for t in type_restrictions:
               if (t in val[0]['types']):
                    addCardType = True
                    break 
            if not addCardType:
                continue

            addCardCMC = True
            if cmc_restriction >= 0:
                if cmcstrict:
                    addCardCMC = val[0]['manaValue'] == cmc_restriction
                else:
                    addCardCMC = val[0]['manaValue'] <= cmc_restriction

            if not addCardCMC:
                continue

            # Disabled due to being too costly
            #if not (ccost == None):
            #    if not self.isCardCastable( self.convertManaToDict(val[0]['manaCost'], False), ccost):
            #        continue

            cardList.append((key,val))
       
        if len(cardList) == 0:
            return None, None
        return choice(cardList)

    # Returns a string with all the card's info
    def cardStringifier(self, myCard, cardStats):

        ret = "Your Card Was:```\n{}".format(myCard)
        if 'manaCost' in cardStats[0]:
            ret = ret + " {}".format(cardStats[0]['manaCost'])
        ret = ret + "\n\n"
        if 'supertypes' in cardStats[0]:
            ret = ret + "{} ".format(" ".join(cardStats[0]['supertypes']))
        if 'types' in cardStats[0]:
            ret = ret + "{}".format(" ".join(cardStats[0]['types']))
        if 'subtypes' in cardStats[0]:
            ret = ret + " - {}".format(" ".join(cardStats[0]['subtypes']))
        ret = ret + "\n\n"
        if 'text' in cardStats[0]:
            ret = ret + "{}".format(cardStats[0]['text'])
        ret = ret + "\n\n"
        if ('power' in cardStats[0]) and ('toughness' in cardStats[0]):
            ret = ret + "Power:{} / Toughness:{}".format(cardStats[0]['power'],cardStats[0]['toughness'])
        if 'loyalty' in cardStats[0]:
            ret = ret + "Loyalty:{}".format(cardStats[0]['loyalty'])
        ret = ret + "```"
        return ret

    ### Small Sanity Check to see if a command is in the correct channel. Returns true if the post should be ignored. ###
    def channel_check(self, ctx):
        return not((len(self.serverTextChannel) == 0) or (ctx.channel.id in self.serverTextChannel))

    ### Begin Discord Commands ###

    @commands.command(brief='Sets this text channel for EDH function', description='Sets this text channel for EDH function and prohibits use of edh cog commands in other channels', hidden=True)
    async def setEDHChannel(self, ctx, *args):
        if ctx.author.guild_permissions.administrator == False:
            return

        self.serverTextChannel.append(ctx.channel.id)
        await ctx.send(f"Set EDH channel list to: {self.serverTextChannel}")
        return

    @commands.command(brief='Sets this text channel for EDH function', description='Sets this text channel for EDH function and prohibits use of edh cog commands in other channels', hidden=True)
    async def resetEDHChannel(self, ctx, *args): 
        if ctx.author.guild_permissions.administrator == False:
            return
        self.serverTextChannel = []
        await ctx.send("Reset EDH channel to have no restrictions.")
        return

    @commands.command(brief='Generates an EDH deck. Do "!edh help" for more info.', description='Makes a random EDH deck that is probably not good. Note double faced cards (which use "//" may need to be hand modified to be supported by whatever you shove this into. For further help type "!edh help"')
    async def edh(self, ctx, *args):

        if self.channel_check(ctx):
            return

        # If no arguments, make an edh deck using whatever.
        if len(args) == 0:
            myString = self.dictToString(self.makeDeck())
            await ctx.send("Here's your deck!\n```" + myString + "```")
            return

        # Help options
        elif args[0].lower() == "help":
            myString =  """ Here is what I have so far:
`!edh` - generates a random deck with a random commander and random colors.
`!edh commander "Kozilek, the Great Distortion"` - generates a deck with Kozilek, the Great Distortion as the commander. The quotes are necessary.
`!edh commander "Fblthp, the Lost" "Norin, the Wary"` - generates a deck with Fblthp and Norin as though they had partner. The quotes are necessary.
`!edh colors red white blue` - generates a deck with a commander or pair of commanders that has the color identity of red, white, and blue.
`!edh colors none` - generates a colorless edh deck.
                        """
            await ctx.send(myString)
            return

        # if arg[0] is "commander" then args[1] (and potentially args[2]) are commanders
        elif (args[0].lower() == "commander") or (args[0].lower() == "commanders"):         
            if len(args) < 2:
                await ctx.send("No commander specified. Either call this with a commander or do not add the commander arg.")
                return
            
            potential_cmdr_list = [] 
            potential_cmdr_list.append(self.findBestCMDRMatch(args[1])[0])
            if len(args) > 2:
                potential_cmdr_list.append(self.findBestCMDRMatch(args[2])[0]) 
               
            myString = self.dictToString(self.makeDeck(cmdrList=potential_cmdr_list))
            await ctx.send("Here's your deck with commander(s) {}:\n```{}```".format(potential_cmdr_list, myString))
            return
        elif (args[0].lower() == "color") or (args[0].lower() == "colors"): 

            potential_cmdr_list = self.getCMDROnColor(self.tupleToColorID(args)) 
            myString = self.dictToString(self.makeDeck(cmdrList=potential_cmdr_list))
            await ctx.send("Here's your deck with color selection {}:\n```{}```".format(self.tupleToColorID(args), myString))
            return
        else:
            await ctx.send("I'm not sure what you want? Make sure after !edh you type the type of restriction you're giving. Check with !edh help for current options.")
            return


    @commands.command(brief='Spits out a random card', description='Gets a random card. You can restrict a card to have specific requirements. Check with !randomcard help')
    async def randomcard(self, ctx, *args):
        if self.channel_check(ctx):
            return

        if len(args) == 0:
            myCard, cardStats = self.getRandomCard()
            if myCard == None:
                await ctx.send("No cards found. :(")
                return
            else:
                await ctx.send( self.cardStringifier(myCard, cardStats) )             
                return

        
        elif args[0].lower() == "help":
            myString =  """ Here is what I have so far:
`!randomcard` - generates a random card.
`!randomcard cmc=3` - generates a card with cmc less than or equal to 3.
`!randomcard cmcstrict=3` - generates a card with cmc of 3 exactly.
`!randomcard type=Instant` - generates a random instant
`!randomcard cmc=2 type=Creature type=Enchantment` - generates a card that is either a creature or enchantment with cmc less than or equal to 3.
                        """
            await ctx.send(myString)
            return

        #Set default args
        color_restrictions=[]
        type_restrictions=[ 'Planeswalker', 'Creature', 'Sorcery', 'Instant', 'Artifact', 'Enchantment','Instant','Land' ]
        my_types = [ ]
        cmc_restriction=-1
        cmcstrict=False

        for a in args:
            t_s = a.split("=")
            if len(t_s) <= 1:
                ctx.send("I didn't detect an assignment? Make sure not to use spaces between the '=' and the value.")
                return

            if a.lower().startswith("cmc="):
                if t_s[1].isnumeric():
                    cmc_restriction=int(t_s[1])
                    cmcstrict=False
                else:
                    ctx.send("CMC Restriction needs to be a number?")
                    return 
            if a.lower().startswith("cmcstrict="):
                if t_s[1].isnumeric():
                    cmc_restriction=int(t_s[1])
                    cmcstrict=True
                else:
                    ctx.send("CMC Restriction needs to be a number?")
                    return

            if a.lower().startswith("type"):
                if t_s[1].capitalize() not in type_restrictions:
                    ctx.send(" {} not a valid type. Valid types are: {}", t_s[1].capitalize(), type_restrictions)
                    return
                my_types.append(t_s[1].capitalize())

        
        if len(my_types) == 0:
            my_types = type_restrictions

        myCard, cardStats = self.getRandomCard(type_restrictions=my_types, cmc_restriction=cmc_restriction, cmcstrict=cmcstrict)
        if myCard == None:
            await ctx.send("No cards found. :(")
            return
        else:
            await ctx.send(self.cardStringifier(myCard, cardStats))  
            return
