from __future__ import annotations
import json
import asyncio
import aiohttp
from dataclasses import dataclass
from PIL import Image, ImageFont, ImageDraw
from io import BytesIO
from enum import IntEnum
import traceback
import pyperclip
import os
import base64
import copy

# class to manipulate a vector2-type structure
dataclass(slots=True)
class v2():
    x : int|float = 0
    y : int|float = 0
    
    def __init__(self : v2, X : int|float, Y : int|float):
        self.x = X
        self.y = Y
    
    # operators
    def __add__(self : v2, other : v2|tuple|list|int|float) -> v2:
        if isinstance(other, float) or isinstance(other, int):
            return v2(self.x + other, self.y + other)
        else:
            return v2(self.x + other[0], self.y + other[1])
    
    def __radd__(self : v2, other : v2|tuple|list|int|float) -> v2:
        return self.__add__(other)

    def __mul__(self : v2, other : v2|tuple|list|int|float) -> v2:
        if isinstance(other, float) or isinstance(other, int):
            return v2(self.x * other, self.y * other)
        else:
            return v2(self.x * other[0], self.y * other[1])

    def __rmul__(self : v2, other : v2|tuple|list|int|float) -> v2:
        return self.__mul__(other)

    # for access via []
    def __getitem__(self : v2, key : int) -> int|float:
        if key == 0:
            return self.x
        elif key == 1:
            return self.y
        else:
            raise IndexError("Index out of range")

    def __setitem__(self : v2, key : int, value : int|float) -> None:
        if key == 0:
            self.x = value
        elif key == 1:
            self.y = value
        else:
            raise IndexError("Index out of range")

    # len is fixed at 2
    def __len__(self : v2) -> int:
        return 2

    # to convert to an integer tuple (needed for pillow)
    @property
    def i(self : v2) -> tuple[int, int]:
        return (int(self.x), int(self.y))

# General enum
class PartyMode(IntEnum):
    normal = 0 # normal parties
    extended = 1 # 8 man party (Versusia)
    babyl = 2 # 12 man party (Babyl)

class GBFTMR():
    VERSION = (2, 3)
    ASSET_TABLE = [ # asset urls used depending on asset type
        [ # 0 leader
            "https://prd-game-a1-granbluefantasy.akamaized.net/assets_en/img/sp/assets/leader/s/{}.jpg",
            "https://prd-game-a1-granbluefantasy.akamaized.net/assets_en/img/sp/assets/leader/quest/{}.jpg",
            "http://prd-game-a1-granbluefantasy.akamaized.net/assets_en/img/sp/assets/leader/my/{}.png",
            "https://prd-game-a1-granbluefantasy.akamaized.net/assets_en/img/sp/assets/leader/job_change/{}.png",
            "https://prd-game-a1-granbluefantasy.akamaized.net/assets_en/img/sp/assets/leader/job_change/{}.png"
        ],
        [ # 1 weapon
            "https://prd-game-a-granbluefantasy.akamaized.net/assets_en/img/sp/assets/weapon/s/{}.jpg",
            "https://prd-game-a-granbluefantasy.akamaized.net/assets_en/img/sp/assets/weapon/m/{}.jpg",
            "https://prd-game-a-granbluefantasy.akamaized.net/assets_en/img/sp/assets/weapon/b/{}.png",
            "https://prd-game-a-granbluefantasy.akamaized.net/assets_en/img/sp/assets/weapon/b/{}.png",
            "https://prd-game-a-granbluefantasy.akamaized.net/assets_en/img/sp/assets/weapon/b/{}.png"
        ],
        [ # 2 summon
            "https://prd-game-a-granbluefantasy.akamaized.net/assets_en/img/sp/assets/summon/s/{}.jpg",
            "https://prd-game-a1-granbluefantasy.akamaized.net/assets_en/img/sp/assets/summon/m/{}.jpg",
            "https://prd-game-a1-granbluefantasy.akamaized.net/assets_en/img/sp/assets/summon/my/{}.png",
            "https://prd-game-a-granbluefantasy.akamaized.net/assets_en/img/sp/assets/summon/b/{}.png",
            "https://prd-game-a-granbluefantasy.akamaized.net/assets_en/img/sp/assets/summon/b/{}.png"
        ],
        [ # 3 character
            "https://prd-game-a1-granbluefantasy.akamaized.net/assets_en/img/sp/assets/npc/s/{}.jpg",
            "https://prd-game-a1-granbluefantasy.akamaized.net/assets_en/img/sp/assets/npc/quest/{}.jpg",
            "https://prd-game-a1-granbluefantasy.akamaized.net/assets_en/img/sp/assets/npc/my/{}.png",
            "https://prd-game-a-granbluefantasy.akamaized.net/assets_en/img_low/sp/assets/npc/b/{}.png",
            "https://media.skycompass.io/assets/customizes/characters/1138x1138/{}.png"
        ],
        [ # 4 skin
            "assets/{}",
            "assets/{}",
            "assets/{}",
            "assets/{}",
            "assets/{}"
        ],
        [ # 5 empty weapon
            "https://prd-game-a-granbluefantasy.akamaized.net/assets_en/img/sp/assets/weapon/s/{}.jpg",
            "https://prd-game-a1-granbluefantasy.akamaized.net/assets_en/img/sp/deckcombination/base_empty_weapon_sub.png",
            "",
            "",
            ""
        ],
        [ # 6 empty character
            "https://prd-game-a1-granbluefantasy.akamaized.net/assets_en/img/sp/assets/npc/s/{}.jpg",
            "https://prd-game-a1-granbluefantasy.akamaized.net/assets_en/img/sp/deckcombination/base_empty_npc.jpg",
            "",
            "",
            ""
        ]
    ]
    DISPLAY_TABLE = ["squareicon", "partyicon", "fullart", "homeart", "skycompass"] # asset type, index must match the url above
    NULLCHARACTER = [3030182000, 3020072000] # lyria and young cat, need to be hardcoded
    def __init__(self : GBFTMR, path : str = "", client : None|aiohttp.ClientSession = None) -> None:
        self.path = path # working directory path
        self.client = client # aiohttp client
        if path != "" and self.client is None:
            raise Exception("A valid ClientSession is expected when the working directory path is specified")
        print("GBF Thumbnail Maker Remake v{}.{}".format(self.VERSION[0], self.VERSION[1]))
        self.cache = {} # asset memory cache
        self.classes = None # class cache
        self.class_modified = False # flag, class cache has been modified
        self.boss = {} # boss cache
        self.stamp = {} # stamp cache
        self.template = {} # template cache
        # load caches
        self.loadBosses()
        self.loadStamps()
        self.loadTemplates()
        # gradient mask
        tmp = Image.open(self.path+"assets/mask.png")
        self.mask = tmp.convert('L')
        tmp.close()

    # process Exception into readable string
    def pexc(self : GBFTMR, e : Exception) -> str:
        return "".join(traceback.format_exception(type(e), e, e.__traceback__))

    # load templates
    def loadTemplates(self : GBFTMR) -> None:
        try:
            with open(self.path+"template.json", mode="r", encoding="utf-8") as f:
                self.template = json.load(f)
        except Exception as e:
            print(self.pexc(e))

    # load bosses
    def loadBosses(self : GBFTMR) -> None:
        try:
            with open(self.path+"boss.json", mode="r", encoding="utf-8") as f:
                self.boss = json.load(f)
            # patch
            for s in self.boss:
                if len(self.boss[s]) == 3:
                    self.boss[s].append(False)
        except:
            pass

    # save bosses
    def saveBosses(self : GBFTMR) -> None:
        try:
            with open(self.path+"boss.json", mode="w", encoding="utf-8") as f:
                json.dump(self.boss, f, ensure_ascii=False)
            print("'boss.json' updated")
        except:
            pass

    # load stamps
    def loadStamps(self : GBFTMR) -> None:
        try:
            with open(self.path+"stamp.json", mode="r", encoding="utf-8") as f:
                self.stamp = json.load(f)
        except:
            pass

    # save stamps
    def saveStamps(self : GBFTMR) -> None:
        try:
            with open(self.path+"stamp.json", mode="w", encoding="utf-8") as f:
                json.dump(self.stamp, f, ensure_ascii=False)
            print("'stamp.json' updated")
        except:
            pass

    # load classes
    def loadClasses(self : GBFTMR) -> None:
        try:
            self.class_modified = False
            with open(self.path+"classes.json", mode="r", encoding="utf-8") as f:
                self.classes = json.load(f)
        except:
            self.classes = {}

    # save classes
    def saveClasses(self : GBFTMR) -> None:
        try:
            if self.class_modified:
                with open(self.path+"classes.json", mode='w', encoding='utf-8') as outfile:
                    json.dump(self.classes, outfile)
        except:
            pass

    # check if the cache folder exists (and create it if needed)
    def checkDiskCache(self : GBFTMR) -> None:
        if not os.path.isdir(self.path + 'cache'):
            os.mkdir(self.path + 'cache')

    # retrieve an asset at the given url
    async def getAsset(self : GBFTMR, url : str) -> bytes:
        response = await self.client.get(url, headers={'connection':'keep-alive'})
        if response.status != 200:
            raise Exception()
        return await response.read()

    # process a boss bookmark string and return ids
    def bookmarkString(self : GBFTMR, s : str) -> tuple[str|None, str|None, str|None, str|None]:
        if s.startswith("$$boss:"):
            s = s.replace("$$boss:", "").split('|')
            if len(s) == 3:
                s.append(False)
            elif len(s) >= 4:
                if s[3] == "1" or s[3].lower() == "true":
                    s[3] = True
                else:
                    s[3] = False
                if len(s) >= 5:
                    s = s[:4]
            return tuple(s)
        else:
            return None, None, None, None

    # add/edit a boss to the cache
    async def addBoss(self : GBFTMR) -> None:
        print("Input an Enemy ID with a valid Appear animation (Leave blank to cancel)")
        s = input()
        if s == "": return
        if s.lower() == "cc": # cc let you copy from clipboard directly
            try:
                s = pyperclip.paste()
            except:
                s = "cc"
        # process the bookmark string
        # in order: enemy id, background file, enemy icon, name fix flag
        eid, bg, eico, fix = self.bookmarkString(s)
        # check if valid
        if eid is None: # not, so we ask the user
            eid = s
            print("Input a background file name (Leave blank to skip)")
            s = input()
            if s.lower() == "cc":
                try:
                    s = pyperclip.paste()
                except:
                    s = "cc"
            elif s != "":
                bg = s
            print("Input another Enemy ID to set a different icon (Leave blank to skip or input None to disable)")
            s = input()
            if s != "":
                if s.lower() != "none":
                    if s.lower() == "cc":
                        try:
                            s = pyperclip.paste()
                        except:
                            s = "cc"
                    eico = s
            else:
                eico = eid
        print("Generating a preview...")
        img = await self.generateBackground(eid, bg, eico, False if fix is None else fix)
        if img is None:
            print("An error occured, check if the ID you provided are correct")
            return
        else:
            img.show() # open and show the image
            img.close()
        # let the user fix if needed
        print("Input 'fix' if the name is wrong (Anything else to ignore)")
        fix = (input().lower() == 'fix')
        # saving
        while True:
            print("Input a boss name to save those settings (Leave blank to cancel)")
            s = input().lower()
            if s == "": return
            if s in self.boss:
                print(s, "already exists, overwrite? ('y' to confirm)")
                if input().lower() != 'y':
                    continue
            self.boss[s] = [eid, bg, eico, fix]
            self.saveBosses()
            break

    # add/edit a stamp to the cache
    async def addStamp(self : GBFTMR) -> None:
        while True:
            print("Input a stamp url (Leave blank to cancel)")
            s = input()
            if s == "": return
            if s.lower() == "cc":
                try:
                    s = pyperclip.paste()
                except:
                    s = "cc"
            try:
                await self.getAsset(s)
                url = s
                break
            except:
                print("Invalid URL")
        while True:
            print("Input a stamp name to save those settings (Leave blank to cancel)")
            s = input().lower()
            if s == "": return
            if s in self.stamp:
                print(s, "already exists, overwrite? ('y' to confirm)")
                if input().lower() != 'y':
                    continue
            self.stamp[s] = url
            self.saveStamps()
            break

    # get the MC "unskined" filename based on id
    async def get_mc_job_look(self : GBFTMR, skin, job) -> str:
        sjob = str((job//100) * 100 + 1)
        if sjob in self.classes:
            return "{}_{}_{}".format(sjob, self.classes[sjob], '_'.join(skin.split('_')[2:]))
        else:
            # search mainhand if not in cache
            for mh in ["sw", "kn", "sp", "ax", "wa", "gu", "me", "bw", "mc", "kr"]:
                try:
                    await self.getAsset("https://prd-game-a5-granbluefantasy.akamaized.net/assets_en/img/sp/assets/leader/s/{}_{}_0_01.jpg".format(job, mh))
                    self.class_modified = True
                    self.classes[sjob] = mh
                    return "{}_{}_{}".format(sjob, self.classes[sjob], '_'.join(skin.split('_')[2:])) 
                except:
                    pass
        return ""

    # to a character uncap suffix based on uncap level
    def get_uncap_id(self : GBFTMR, cs : int) -> str:
        return {2:'02', 3:'02', 4:'02', 5:'03', 6:'04'}.get(cs, '01')

    # return true if the given string contains only alphanumeric or underscore characters
    def valid_name(self : GBFTMR, s : str) -> bool:
        for c in s:
            if c not in "abcdefghijklmnopqrstuvwxyz0123456789_":
                return False
        return True

    # generate a background image for given ids
    async def generateBackground(self : GBFTMR, eid, bg, eico, fix : bool = None) -> Image|None:
        try:
            if "_" in eid: # if underscore in enemy id, get suffix (only used for old Hexachromatic spoiler animation and some event bosses)
                ext = "_"+eid.split("_")[1]
                eid = eid.split("_")[0]
            else:
                ext = ""
            # retrieve animation file
            cjs = (await self.getAsset("https://prd-game-a3-granbluefantasy.akamaized.net/assets_en/js/cjs/raid_appear_{}{}.js".format(eid, ext))).decode('utf-8')
            # make token string to be used in the file
            token = "raid_appear_"+eid+ext+"_"
            # start parsing for sub rectangles
            pos = 0
            elements = {}
            while True:
                a = cjs.find(token, pos) # sub rectables are always after their names
                if a == -1: break
                b = cjs.find("=", a) # so usually something like raid_appear_XXXXXXX_name=....Rectangle(
                if b == -1: break
                name = cjs[a+len(token):b] # retrieve the rect name
                if not self.valid_name(name) or name in elements: # check if valid (to avoid mistakes) else skip
                    pos = a + len(token)
                    continue
                c = cjs.find(".Rectangle(", b) # Now retrieve rectangle parameters...
                if c == -1: break
                d = cjs.find(")", c)
                if d == -1: break
                rect = cjs[c+len(".Rectangle("):d] # ... here
                pos = d
                elements[name] = []
                rect = rect.split(',') # split by , (format is X,Y,W,H)
                for r in rect: # and append to our list
                    if r.startswith('.'): # floating point correction
                        r = '0'+r
                    elements[name].append(float(r)) # convert from string to float
                # add origin to width/height (as pillow want the end point coordinates)
                elements[name][2] += elements[name][0]
                elements[name][3] += elements[name][1]
            # retrieve background
            if bg is not None:
                with BytesIO(await self.getAsset("https://game.granbluefantasy.jp/assets_en/img/sp/raid/bg/{}.jpg".format(bg))) as img_data:
                    img = Image.open(img_data)
                    # resize it to fit the thumbnail
                    mod = 1280/img.size[0]
                    tmp = img.resize((int(img.size[0]*mod), int(img.size[0]*mod)), Image.Resampling.LANCZOS)
                    img.close() # always close to make sure nothing leaks in memory
                    img = tmp
                    # calculate and apply a crop to show somehow the middle part
                    y = img.size[1]//2-360
                    tmp = img.crop((0, y, 1280, y+720))
                    img.close()
                    img = tmp
                    # add transparency
                    tmp = Image.new("L", img.size, "white")
                    img.putalpha(tmp)
                    tmp.close()
                    # set
                    background = img
            else:
                background = None
            
            # used for debugging, change to True to use
            if False:
                for k in elements:
                    print(k, elements[k]) # it shows each rectangle coordinates
            
            parts = []
            # we will select the rectangles to use and put their names in parts
            # it depends mostly on what rectangles are found, etc...
            name_y_off = 0 # will contain the vertical offset of the name part
            for p in ['boss', 'bg', 'vs', 'name_a', 'name_b']: # mostly fixes for diaspora, sieg etc...
                if p in elements:
                    parts.append(p)
            if 'opq_boss' in elements: # salmun golem fix
                found = False
                for i in range(len(parts)):
                    if parts[i] == 'boss':
                        parts[i] = 'opq_boss'
                        found = True
                        break
                if not found: parts.append('opq_boss')
            if 'vs_bg' in elements:
                parts[1] = 'vs_bg'
                parts.insert(0, 'bg')
            if 'opq_vs' in elements: # salmun golem fix
                found = False
                for i in range(len(parts)):
                    if parts[i] == 'vs':
                        parts[i] = 'opq_vs'
                        found = True
                        break
                if not found: parts.append('opq_vs')
            if 'name_a' in elements:
                name_y_off = int(max(135, elements['name_a'][3] - elements['name_a'][1])) - 135
            if 'opq_name_a' in elements: # salmun golem
                found = False
                for i in range(len(parts)):
                    if parts[i] == 'name_a':
                        parts[i] = 'opq_name_a'
                        found = True
                        break
                if not found:
                    parts.append('opq_name_a')
                name_y_off = int(max(135, elements['opq_name_a'][3] - elements['opq_name_a'][1])) - 135
            if 'name_b' in elements:
                name_y_off = int(max(135, elements['name_b'][3] - elements['name_b'][1])) - 135
            if 'boss_a' in elements:
                name_y_off = int(max(135, elements['boss_a'][3] - elements['boss_a'][1])) - 135
                parts[-1] = 'boss_a'
            if 'name_vs' in elements:
                parts.append('name_vs')
            if 'jp' in elements:
                parts.append('jp')
            if 'en' in elements:
                parts.append('en')

            # load spritsheet file (this type of animation usually only use one, so we don't bother checking. It could break in the future for more fancier bosses)
            with BytesIO(await self.getAsset("https://prd-game-a1-granbluefantasy.akamaized.net/assets_en/img/sp/cjs/raid_appear_{}{}.png".format(eid, ext))) as img_data:
                appear = Image.open(img_data)
                tmp = appear.convert('RGBA')
                appear.close()
                appear = tmp
                # make image (youtube wants 720p thumbnail usually)
                img = self.make_canvas((1280, 720))
                for k in parts: # iterate over parts
                    if fix and k == "name_b": # check name fix, skip name_b if enabled
                        continue
                    # load part coordinates, and extract rectangle from sheet
                    crop = appear.crop(tuple(elements[k]))
                    # different behavior based on part name:
                    match k:
                        case 'boss'|'opq_boss': # resize the boss to fit the image vertically, and put it on the left
                            mod = min(720/crop.size[0], 720/crop.size[1])
                            tmp = crop.resize((int(crop.size[0]*mod), int(crop.size[1]*mod)), Image.Resampling.LANCZOS)
                            crop.close()
                            crop = tmp
                            offset = (-20, 0)
                        case 'bg': # any special background is...
                            if k == parts[0]: # ... kept on the top left if encountered first
                                offset = (0, 0)
                            else: # ... or resized behind the name
                                offset = ((640 - crop.size[0]) // 2, 360-name_y_off)
                        # the following are only boss name related stuff
                        case 'vs'|'opq_vs':
                            offset = ((640 - crop.size[0]) // 2, 350-name_y_off)
                        case 'vs_bg':
                            offset = ((640 - crop.size[0]) // 2, 300-name_y_off)
                        case 'jp':
                            offset = ((640 - crop.size[0]) // 2, 480-name_y_off)
                        case 'en':
                            offset = ((640 - crop.size[0]) // 2, 540-name_y_off)
                        case 'name_a'|'opq_name_a':
                            offset = ((640 - crop.size[0]) // 2, 450-name_y_off)
                        case 'name_b':
                            offset = ((640 - crop.size[0]) // 2, 490-name_y_off)
                        case 'boss_a':
                            offset = ((640 - crop.size[0]) // 2, 440-name_y_off)
                        case 'name_vs':
                            offset = ((640 - crop.size[0]) // 2, 450-name_y_off)
                    # add rectangle to our image
                    layer = self.make_canvas((1280, 720))
                    layer.paste(crop, offset, crop)
                    mod = Image.alpha_composite(img, layer)
                    img.close()
                    layer.close()
                    crop.close()
                    img = mod
                    # add the gradient
                    if (k == 'bg' and k != parts[0]) or (parts[0] == 'bg' and k == 'vs_bg'): # gradient
                        grad = self.make_canvas((1280, 720))
                        tmp = Image.composite(img, grad, self.mask)
                        img.close()
                        grad.close()
                        img = tmp
                # if a background if selected, add it behind
                if background is not None:
                    tmp = Image.alpha_composite(background, img)
                    background.close()
                    img.close()
                    img = tmp
            try: # add the icon (if set)
                if eico is not None:
                    with BytesIO(await self.getAsset("https://prd-game-a-granbluefantasy.akamaized.net/assets_en/img/sp/assets/enemy/m/{}.png".format(eico))) as img_data:
                        mod = Image.open(img_data)
                        tmp = mod.convert("RGBA")
                        mod.close()
                        layer = self.make_canvas((1280, 720))
                        layer.paste(tmp, (15, 720-tmp.size[1]-15), tmp) # position, bottom left corner, off 15px
                        tmp.close()
                        tmp = Image.alpha_composite(img, layer)
                        img.close()
                        layer.close()
                        img = tmp
            except Exception as e:
                print(self.pexc(e))
            return img
        except Exception as me:
            print(self.pexc(me))
            return None

    # make a blank image to the specified size (usualy 1280x720)
    def make_canvas(self : GBFTMR, size) -> Image:
        i = Image.new('RGB', size, "black")
        im_a = Image.new("L", i.size, "black")
        i.putalpha(im_a)
        im_a.close()
        return i

    # generate a thumbnail via command line
    async def makeThumbnailManual(self : GBFTMR, gbfpib=None):
        print("Please select a template:")
        choices = []
        for k in self.template:
            print("[{}] {}".format(len(choices), k))
            choices.append(k)
        print("[Any] Cancel")
        s = input()
        try: k = choices[int(s)]
        except: return
        settings = {}
        # copy template
        template = copy.deepcopy(self.template[k])
        # iterate over actions to set their user settings
        for index in range(len(template)):
            e = template[index]
            match e["type"]:
                case "background": # background selection
                    while True:
                        print("Input the background you want to use (Leave blank to ignore)")
                        s = input().lower()
                        if s == "":
                            break
                        else:
                            data = self.bookmarkString(s)
                            if data[0] is not None:
                                settings['bg'] = data
                                while True:
                                    print("Input a boss name to save those settings (Leave blank to ignore)")
                                    s = input().lower()
                                    if s == "": break
                                    elif s in self.boss:
                                        print(s, "already exists, overwrite? ('y' to confirm)")
                                        if input().lower() != 'y':
                                            continue
                                    self.boss[s] = data
                                    self.saveBosses()
                                    break
                                break
                            else:
                                if s not in self.boss:
                                    print(s, "not found in the boss data")
                                    r = self.search_boss(s)
                                    if len(r) > 0:
                                        print("Did you mean...?")
                                        print("*", "\n* ".join(r))
                                else:
                                    settings['bg'] = self.boss[s]
                                    break
                case "boss": # boss selection
                    print("Input the ID of the boss you want to display (Leave blank to ignore)")
                    s = input().lower()
                    if s != "":
                        data = self.bookmarkString(s)
                        if data[0] is not None:
                            settings['boss'] = [data[0], data[2], data[3]]
                            while True:
                                print("Input a boss name to save those settings (Leave blank to ignore)")
                                s = input().lower()
                                if s == "": break
                                elif s in self.boss:
                                    print(s, "already exists, overwrite? ('y' to confirm)")
                                    if input().lower() != 'y':
                                        continue
                                self.boss[s] = data
                                self.saveBosses()
                                break
                        else:
                            if not s.isdigit() and s in self.boss:
                                settings['boss'] = [self.boss[s][0], self.boss[s][2], self.boss[s][3]]
                            else:
                                settings['boss'] = [s, None, False]
                            if settings['boss'][1] is None:
                                print("Input the ID of the boss whose icon you want to display, if different (Leave blank to ignore)")
                                s = input().lower()
                                if s != "":
                                    settings['boss'][1] = s
                                else:
                                    settings['boss'][1] = settings['boss'][0]
                case "stamp": # stamp selection
                    while True:
                        print("Input the stamp you want to use (Leave blank to ignore)")
                        s = input().lower()
                        if s == "":
                            break
                        else:
                            if s in self.stamp:
                                e["type"] = "asset"
                                e['asset'] = self.stamp[s]
                                break
                            else:
                                try:
                                    if not s.startswith("http"):
                                        raise Exception()
                                    await self.getAsset(s)
                                    url = s
                                    e["type"] = "asset"
                                    e['asset'] = url
                                    break
                                except:
                                    print("Not a valid URL or name")
                                    r = self.search_stamp(s)
                                    if len(r) > 0:
                                        print("Did you mean...?")
                                        print("*", "\n* ".join(r))
                                    continue
                                while True:
                                    print("Input a stamp name to save those settings (Leave blank to ignore)")
                                    s = input().lower()
                                    if s == "": break
                                    elif s in self.stamp:
                                        print(s, "already exists, overwrite? ('y' to confirm)")
                                        if input().lower() != 'y':
                                            continue
                                    self.stamp[s] = url
                                    self.saveStamps()
                                    break
                                break
                case "party": # party selection (using the clipboard)
                    if gbfpib is not None:
                        settings["gbfpib"] = gbfpib
                        if 'lang' not in settings["gbfpib"]:
                            return
                    else:
                        print("Checking clipboard for party data...")
                        while True:
                            try:
                                settings["gbfpib"] = json.loads(pyperclip.paste())
                                if 'lang' not in settings["gbfpib"]: raise Exception()
                                break
                            except:
                                print("No GBFPIB data found in the clipboard")
                                input("Export a party then press return here")
                case "autoinput": # FA selection
                    print("Select an Auto setting:")
                    print("[0] Auto")
                    print("[1] Full Auto")
                    print("[2] Full Auto Guard")
                    print("[Any] Manual")
                    match input():
                        case "0":
                            e["asset"] = "auto.png"
                        case "1":
                            e["asset"] = "fa.png"
                        case "2":
                            e["asset"] = "fa_guard.png"
                        case _:
                            e["asset"] = None
                    e["type"] = "asset"
                case "nminput": # NM selection
                    print("Select a GW NM or DB Foe:")
                    print("[0] GW NM90")
                    print("[1] GW NM95")
                    print("[2] GW NM100")
                    print("[3] GW NM150")
                    print("[4] GW NM200")
                    print("[5] GW NM250")
                    print("[6] DB 1*")
                    print("[7] DB 2*")
                    print("[8] DB 3*")
                    print("[9] DB 4*")
                    print("[10] DB 5*")
                    print("[11] DB UF95")
                    print("[12] DB UF135")
                    print("[13] DB UF175")
                    print("[14] DB UF215")
                    print("[15] DB Valiant")
                    print("[16] Record NM100")
                    print("[17] Record NM150")
                    print("[Any] Skip")
                    match input():
                        case "0": nm = 90
                        case "1": nm = 95
                        case "2": nm = 100
                        case "3": nm = 150
                        case "4": nm = 200
                        case "5": nm = 250
                        case "6": nm = 1
                        case "7": nm = 2
                        case "8": nm = 3
                        case "9": nm = 4
                        case "10": nm = 5
                        case "11": nm = 11
                        case "12": nm = 12
                        case "13": nm = 13
                        case "14": nm = 14
                        case "15": nm = 20
                        case "16": nm = -100
                        case "17": nm = -150
                        case _: nm = None
                    if nm is not None:
                        print("Input a GW / DB / Record ID:")
                        gwn = input()
                        if nm < 0: # record
                            e["asset"] = "https://prd-game-a1-granbluefantasy.akamaized.net/assets_en/img/sp/event/common/terra/top/assets/quest/terra{}_hell{}.png".format(gwn.zfill(3), -nm)
                        elif nm < 10:
                            e["asset"] = "https://prd-game-a1-granbluefantasy.akamaized.net/assets_en/img/sp/assets/summon/qm/teamforce{}_star{}.png".format(gwn.zfill(2), nm)
                        elif nm < 20:
                            e["asset"] = "https://prd-game-a1-granbluefantasy.akamaized.net/assets_en/img/sp/assets/summon/qm/teamforce{}_strong{}.png".format(gwn.zfill(2), nm-10)
                        elif nm == 20:
                            e["asset"] = "https://prd-game-a1-granbluefantasy.akamaized.net/assets_en/img/sp/assets/summon/qm/teamforce{}_sp.png".format(gwn.zfill(2))
                        else:
                            e["asset"] = "https://prd-game-a1-granbluefantasy.akamaized.net/assets_en/img/sp/event/teamraid{}/assets/thumb/teamraid{}_hell{}.png".format(gwn.zfill(3), gwn.zfill(3), nm)
                        e["type"] = "asset"
                case "prideinput": # pride selection
                    print("Select a Difficulty:")
                    print("[0] Proud")
                    print("[Any] Proud+")
                    match input():
                        case "0": p = ""
                        case _: p = "plus"
                    print("Input Pride Number:")
                    print("[1] Gilbert")
                    print("[2] Nalhe Great Wall")
                    print("[3] Violet Knight")
                    print("[4] Echidna")
                    print("[5] Golden Knight")
                    print("[6] White Knight")
                    print("[7] Cherub")
                    print("[8] Kikuri")
                    print("[9] Zwei")
                    print("[10] Maxwell")
                    print("[11] Otherworld Violet Knight")
                    print("[Any] Anything Else")
                    pn = input().zfill(3)
                    e["asset"] = "https://prd-game-a1-granbluefantasy.akamaized.net/assets_en/img/sp/quest/assets/free/conquest_{}_proud{}.png".format(str(pn).zfill(3), p)
                    e["type"] = "asset"
                case "textinput": # text input
                    print("Input the '{}'".format(e["ref"]))
                    settings[e["ref"]] = input()
        # generate thumbnail with given settings
        await self.makeThumbnail(settings, template)

    async def makeThumbnail(self : GBFTMR, settings : dict, template : list[dict]):
        if self.classes is None:
            self.loadClasses()
        print("[TMR] |--> Starting thumbnail generation...")
        img = self.make_canvas((1280, 720))
        for i, e in enumerate(template): # iterate over template action again
            print("[TMR] |--> Generating Element #{}: {}".format(i+1, e["type"]))
            match e["type"]:
                case "background":
                    img = await self.auto_background(img, settings, e)
                case "boss":
                    img = await self.auto_boss(img, settings, e)
                case "party":
                    img = await self.auto_party(img, settings, e)
                case "asset":
                    img = await self.auto_asset(img, settings, e)
                case "textinput":
                    img = self.auto_text(img, settings, e)
        print("[TMR] |--> Saving...") # save result as thumbnail.png
        img.save("thumbnail.png", "PNG")
        img.close()
        print("[TMR] |--> thumbnail.png has been generated with success")
        self.saveClasses()

    # generate and add background to image
    async def auto_background(self : GBFTMR, img, settings, element):
        if 'bg' not in settings: return img
        bg = await self.generateBackground(settings['bg'][0], settings['bg'][1], settings['bg'][2], settings['bg'][3])
        if bg is None:
            return img
        modified = Image.alpha_composite(img, bg)
        img.close()
        bg.close()
        return modified

    # generate and add a boss to the image
    async def auto_boss(self : GBFTMR, img, settings, element):
        if 'boss' not in settings: return img
        bg = await self.generateBackground(settings['boss'][0], None, settings['boss'][1], settings['boss'][2])
        if bg is None:
            return img
        modified = Image.alpha_composite(img, bg)
        img.close()
        bg.close()
        return modified

    # add a given asset to the image
    async def auto_asset(self : GBFTMR, img, settings, element): # auto asset parsing
        if element.get("asset", None) is None: return img
        pos = element.get('anchor', 'topleft')
        offset = element.get('position', (0,0))
        ratio = element.get('size', 1.0)
        img = await self.make_img_from_element(img, [element["asset"]], pos, offset, ratio)
        return img

    # add a text to the image
    def auto_text(self : GBFTMR, img, settings, element): # auto text parsing
        text = settings.get(element['ref'], '')
        if text == '':
            return img
        fc = tuple(element.get('fontcolor', (255, 255, 255)))
        oc = tuple(element.get('outlinecolor', (255, 0, 0)))
        os = element.get('outlinesize', 10)
        bold = element.get('bold', False)
        italic = element.get('italic', False)
        pos = element.get('anchor', 'middle')
        offset = element.get('position', (0, 0))
        fs = element.get('fontsize', 120)
        lj = element.get('ljust', 0)
        rj = element.get('rjust', 0)
        img = self.make_img_from_text(img, text, fc, oc, os, bold, italic, pos, offset, fs, lj, rj)
        return img

    # obtain character look without skin
    # also fix some characters resulting in some bugged results
    def fix_character_look(self : GBFTMR, export : dict, i : int) -> str:
        style = ("" if str(export['cst'][i]) == '1' else "_st{}".format(export['cst'][i])) # style
        if style != "":
            uncap = "01"
        else:
            uncap = self.get_uncap_id(export['cs'][i])
        cid = export['c'][i]
        # SKIN FIX START ##################
        if str(cid).startswith('371'):
            match cid:
                case 3710098000: # seox skin
                    if export['cl'][i] > 80: cid = 3040035000 # eternal seox
                    else: cid = 3040262000 # event seox
                case 3710122000: # seofon skin
                    cid = 3040036000 # eternal seofon
                case 3710143000: # vikala skin
                    if export['ce'][i] == 3: cid = 3040408000 # apply earth vikala
                    elif export['ce'][i] == 6:
                        if export['cl'][i] > 50: cid = 3040252000 # SSR dark vikala
                        else: cid = 3020073000 # R dark vikala
                case 3710154000: # clarisse skin
                    match export['ce'][i]:
                        case 2: cid = 3040413000 # water
                        case 3: cid = 3040067000 # earth
                        case 5: cid = 3040121000 # light
                        case 6: cid = 3040206000 # dark
                        case _: cid = 3040046000 # fire
                case 3710165000: # diantha skin
                    match export['ce'][i]:
                        case 2:
                            if export['cl'][i] > 70: cid = 3040129000 # water SSR
                            else: cid = 3030150000 # water SR
                        case 3: cid = 3040296000 # earth
                case 3710172000: # tsubasa skin
                    cid = 3040180000
                case 3710176000: # mimlemel skin
                    if export['ce'][i] == 1: cid = 3040292000 # apply fire mimlemel
                    elif export['ce'][i] == 3: cid = 3030220000 # apply earth halloween mimlemel
                    elif export['ce'][i] == 4:
                        if export['cn'][i] in ['Mimlemel', 'ミムルメモル']: cid = 3030043000 # first sr wind mimlemel
                        else: cid = 3030166000 # second sr wind mimlemel
                case 3710191000: # cidala skin 1
                    if export['ce'][i] == 3: cid = 3040377000 # apply earth cidala
                case 3710195000: # cidala skin 2
                    if export['ce'][i] == 3: cid = 3040377000 # apply earth cidala
        # SKIN FIX END ##################
        # Null character fix:
        if cid in self.NULLCHARACTER: 
            if export['ce'][i] == 99:
                return "{}_{}{}_0{}".format(cid, uncap, style, export['pce'])
            else:
                return "{}_{}{}_0{}".format(cid, uncap, style, export['ce'][i])
        else:
            return "{}_{}{}".format(cid, uncap, style)

    # add the party to the image
    async def auto_party(self : GBFTMR, img : Image, settings : dict, element : dict) -> Image:
        entries = []
        # flags
        noskin = element.get("noskin", False)
        mainsummon = element.get("mainsummon", False)
        # import using gbfpib bookmark
        try:
            export = settings['gbfpib']
            skip_zero = False
            if len(export['c']) > 8:
                mode = PartyMode.babyl
                nchara = 12
                skip_zero = True
            elif len(export['c']) > 5:
                mode = PartyMode.extended
                nchara = 8
            else:
                mode = PartyMode.normal
                nchara = 5
            # retrieve mc
            if not mainsummon:
                if noskin:
                    entries.append(await self.get_mc_job_look(export['pcjs'], export['p']))
                else:
                    entries.append(export['pcjs'])
            # iterate over entries and add their file to the list
            for x in range(0, nchara):
                if mainsummon:break
                if skip_zero and x == 0:
                    continue
                if x >= len(export['c']) or export['c'][x] is None:
                    entries.append("3999999999") # add 3999999999 if no character in the list
                    continue
                if noskin:
                    entries.append(self.fix_character_look(export, x))
                else:
                    entries.append(export['ci'][x])
            # retrieve summon
            if export['s'][0] is not None:
                entries.append(export['ss'][0])
            # retrieve weapon
            if not mainsummon:
                if export['w'][0] is not None and export['wl'][0] is not None:
                    entries.append(str(export['w'][0]))
                else:
                    entries.append("1999999999")
        except Exception as e:
            print("An error occured while importing a party:")
            print(self.pexc(e))
            raise Exception("Failed to import party data")
        # now, we add each element at the given position, on a different format depending on mode and babyl flag
        pos = element.get('anchor', 'topleft')
        offset = v2(*element.get('position', (0,0)))
        ratio = element.get('size', 1.0)
        if mainsummon:
            img = await self.make_img_from_element(img, entries, pos, offset, ratio, "partyicon")
        elif mode == PartyMode.babyl:
            img = await self.make_img_from_element(img, entries[:4], pos, offset, ratio, "squareicon", v2(100, 100))
            img = await self.make_img_from_element(img, entries[4:8], pos, offset + v2(0, 100) * ratio, ratio, "squareicon", v2(100, 100))
            img = await self.make_img_from_element(img, entries[8:12], pos, offset + v2(0, 200) * ratio, ratio, "squareicon", v2(100, 100))
            img = await self.make_img_from_element(img, entries[12:13], pos, offset + v2(0, 310) * ratio, ratio, "partyicon", v2(192, 108))
            img = await self.make_img_from_element(img, entries[13:14], pos, offset + v2(208, 310) * ratio, ratio, "partyicon", v2(192, 108))
        elif mode == PartyMode.extended:
            # Note: Elevated by 58 pixels so it fits on most normal party templates
            img = await self.make_img_from_element(img, entries[:4], pos, offset + v2(47, -58) * ratio, ratio, "squareicon", v2(95, 95))
            img = await self.make_img_from_element(img, entries[4:9], pos, offset + v2(0, -58+95+10) * ratio, ratio, "squareicon", v2(95, 95))
            img = await self.make_img_from_element(img, entries[9:10], pos, offset + v2(25, 142+10) * ratio, 0.75*ratio, "partyicon", v2(280, 160))
            img = await self.make_img_from_element(img, entries[10:11], pos, offset + v2(25+280*0.75+15, 142+10) * ratio, 0.75*ratio, "partyicon", v2(280, 160))
        else:
            img = await self.make_img_from_element(img, entries[:4], pos, offset, ratio, "partyicon", v2(78, 142))
            img = await self.make_img_from_element(img, entries[4:6], pos, offset + v2(78*4+15, 0) * ratio, ratio, "partyicon", v2(78, 142))
            img = await self.make_img_from_element(img, entries[6:7], pos, offset + v2(25, 142+10) * ratio, 0.75*ratio, "partyicon", v2(280, 160))
            img = await self.make_img_from_element(img, entries[7:8], pos, offset + v2(25+280*0.75+15, 142+10) * ratio, 0.75*ratio, "partyicon", v2(280, 160))
        return img

    # add element images to our canvas
    async def make_img_from_element(self : GBFTMR, img : Image, characters : list[str] = [], pos : str = "middle", offset : v2|tuple = (0, 0), ratio : float = 1.0, display : str = "squareicon", fixedsize : v2|None = None) -> Image:
        modified = img.copy()
        match pos.lower():
            case "topleft":
                cur_pos = v2(0, 0)
            case "top":
                cur_pos = v2(640, 0)
            case "topright":
                cur_pos = v2(1280, 0)
            case "right":
                cur_pos = v2(1280, 360)
            case "bottomright":
                cur_pos = v2(1280, 720)
            case "bottom":
                cur_pos = v2(640, 720)
            case "bottomleft":
                cur_pos = v2(0, 720)
            case "left":
                cur_pos = v2(0, 360)
            case "middle":
                cur_pos = v2(640, 360)
        cur_pos = cur_pos + offset
        for c in characters:
            size, path = await self.get_element_size(c, display)
            if size is None:
                continue
            if fixedsize is not None:
                size = fixedsize
            size = size * ratio
            match pos.lower():
                case "topright":
                    cur_pos = cur_pos + (-size[0], 0)
                case "right":
                    cur_pos = cur_pos + (-size[0], 0)
                case "bottomright":
                    cur_pos = cur_pos + (-size[0], -size[1])
                case "bottom":
                    cur_pos = cur_pos + (0, -size[1])
                case "bottomleft":
                    cur_pos = cur_pos + (0, -size[1])
            if path.startswith("http"):
                modified = await self.dlAndPasteImage(modified, path, cur_pos, resize=size)
            else:
                modified = self.pasteImage(modified, path, cur_pos, resize=size)
            cur_pos = cur_pos + (size[0], 0)
        img.close()
        return modified

    # add text on the canvas
    def make_img_from_text(self : GBFTMR, img : Image, text : str = "", fc : tuple[int, int, int] = (255, 255, 255), oc : tuple[int, int, int] = (0, 0, 0), os : int = 10, bold : bool = False, italic : bool = False, pos : str = "middle", offset : v2|tuple = (0, 0), fs : int = 24, lj : int = 0, rj : int = 0) -> Image: # to draw text into an image
        text = text.replace('\\n', '\n')
        modified = img.copy()
        d = ImageDraw.Draw(modified, 'RGBA')
        font_file = "font"
        if bold: font_file += "b"
        if italic: font_file += "i"
        font = ImageFont.truetype(self.path + "assets/" + font_file + ".ttf", fs, encoding="unic")
        nl = text.split('\n')
        size = [0, 0]
        for i in range(len(nl)):
            if lj > 0: nl[i] = nl[i].ljust(lj)
            if rj > 0: nl[i] = nl[i].rjust(rj)
            s = font.getbbox(nl[i], stroke_width=os)
            size[0] = max(size[0], s[2]-s[0])
            size[1] += s[3]-s[1] + 10
        text = '\n'.join(nl)
        size[1] = int(size[1] * 1.15)
        match pos.lower():
            case "topleft":
                text_pos = v2(0, 0)
            case "top":
                text_pos = v2(640-size[0]//2, 0)
            case "topright":
                text_pos = v2(1280-size[0], 0)
            case "right":
                text_pos = v2(1280-size[0], 360-size[1]//2)
            case "bottomright":
                text_pos = v2(1280-size[0], 720-size[1])
            case "bottom":
                text_pos = v2(640-size[0]//2, 720-size[1])
            case "bottomleft":
                text_pos = v2(0, 720-size[1])
            case "left":
                text_pos = v2(0, 360-size[1]//2)
            case "middle":
                text_pos = v2(640-size[0]//2, 360-size[1]//2)
        text_pos = text_pos + offset
        d.text(text_pos, text, fill=fc, font=font, stroke_width=os, stroke_fill=oc)
        img.close()
        return modified

    # get an image size and path
    async def get_element_size(self : GBFTMR, c : str, display : str) -> tuple[v2|None, str|None]: # retrive an element asset and return its size
        try:
            if not c.startswith("http"):
                if c == "1999999999":
                    t = 5
                elif c == "3999999999":
                    t = 6
                else:
                    try:
                        if len(c.replace('skin/', '').split('_')[0]) < 10:
                            raise Exception("MC?")
                        int(c.replace('skin/', '').split('_')[0])
                        t = int(c.replace('skin/', '')[0])
                    except Exception as e:
                        if str(e) == "MC?":
                            t = 0
                            if len(c.split("_")) != 4:
                                try:
                                    c = await self.get_mc_job_look(None, c)
                                except:
                                    t = 4
                        else:
                            t = 4
                try:
                    path = self.ASSET_TABLE[t][self.DISPLAY_TABLE.index(display.lower())].format(c)
                except:
                    path = self.ASSET_TABLE[t][self.DISPLAY_TABLE.index(display.lower())]
                if t == 4:
                    path = self.path + path
            else:
                path = c
            if path.startswith("http"):
                with BytesIO(await self.dlImage(path)) as file_jpgdata:
                    buf = Image.open(file_jpgdata)
                    size = v2(*(buf.size))
                    buf.close()
            else:
                buf = Image.open(path)
                size = v2(*(buf.size))
                buf.close()
            return size, path
        except:
            return None, None

    # download an image (check the cache first)
    async def dlImage(self : GBFTMR, url):
        if url not in self.cache:
            self.checkDiskCache()
            try: # get from disk cache if enabled
                with open(self.path + "cache/" + base64.b64encode(url.encode('utf-8')).decode('utf-8'), "rb") as f:
                    self.cache[url] = f.read()
            except: # else request it from gbf
                self.cache[url] = await self.getAsset(url)
                try:
                    with open(self.path + "cache/" + base64.b64encode(url.encode('utf-8')).decode('utf-8'), "wb") as f:
                        f.write(self.cache[url])
                except Exception as e:
                    print(url, ":", e)
                    pass
        return self.cache[url]

    # call dlImage() and pasteImage()
    async def dlAndPasteImage(self : GBFTMR, img, url, offset, resize=None, resizeType="default"):
        with BytesIO(await self.dlImage(url)) as file_jpgdata:
            return self.pasteImage(img, file_jpgdata, offset, resize, resizeType)

     # paste an image onto another
    def pasteImage(self : GBFTMR, img : Image, file : str, offset : v2, resize : v2|None = None, resizeType : str = "default") -> Image:
        buffers = [Image.open(file)]
        buffers.append(buffers[-1].convert('RGBA'))
        if resize is not None:
            match resizeType.lower():
                case "default":
                    buffers.append(buffers[-1].resize(resize.i, Image.Resampling.LANCZOS))
                case "fit":
                    size = buffers[-1].size
                    mod = min(resize[0]/size[0], resize[1]/size[1])
                    offset = offset + (int(resize[0]-size[0]*mod)//2, int(resize[1]-size[1]*mod)//2)
                    buffers.append(buffers[-1].resize((int(size[0]*mod), int(size[1]*mod)), Image.Resampling.LANCZOS))
                case "fill":
                    size = buffers[-1].size
                    mod = max(resize[0]/size[0], resize[1]/size[1])
                    offset = offset + (int(resize[0]-size[0]*mod)//2, int(resize[1]-size[1]*mod)//2)
                    buffers.append(buffers[-1].resize((int(size[0]*mod), int(size[1]*mod)), Image.Resampling.LANCZOS))
        size = buffers[-1].size
        if size[0] == img.size[0] and size[1] == img.size[1] and offset[0] == 0 and offset[1] == 0:
            modified = Image.alpha_composite(img, buffers[-1])
        else:
            layer = self.make_canvas((1280, 720))
            layer.paste(buffers[-1], offset.i, buffers[-1])
            modified = Image.alpha_composite(img, layer)
            layer.close()
        for buf in buffers: buf.close()
        del buffers
        return modified

    # search a boss in cache
    def search_boss(self : GBFTMR, search):
        return self._search(search, self.boss)

    # search a stamp in cache
    def search_stamp(self : GBFTMR, search):
        return self._search(search, self.stamp)

    # search function for stamps and bosses
    def _search(self : GBFTMR, search, target):
        s = search.lower().split(" ")
        r = []
        for k in target:
            for i in s:
                if i != "" and i in k:
                    r.append(k)
                    break
        return r

    # boss management menu
    async def manageBoss(self : GBFTMR):
        while True:
            print("")
            print("Boss Management Menu")
            print("[0] Search Boss by keyword")
            print("[1] Preview Boss")
            print("[2] Delete Boss")
            print("[3] Toggle Boss Name fix")
            print("[4] Tutorial")
            print("[Any] Back")
            s = input()
            match s:
                case '0':
                    print("Input keywords to search")
                    r = self.search_boss(input())
                    if len(r) > 0:
                        print("Listing bosses matching the keywords...")
                        print("*", "\n* ".join(r))
                    print(len(r), "positive result(s)")
                case '1':
                    print("Input the name of a Boss Fight to preview")
                    s = input().lower()
                    data = self.bookmarkString(s)
                    if data[0] is None and s not in self.boss:
                        print("No result found for", s)
                    else:
                        print("Generating preview...")
                        if data[0] is not None:
                            img = await self.generateBackground(*data)
                        else:
                            img = await self.generateBackground(*(self.boss[s]))
                        if img is None:
                            print("An error occured, aborting...")
                        else:
                            print("Opening preview...")
                            img.show()
                            img.close()
                            print("Done")
                case '2':
                    print("Input the name of a Boss Fight to delete")
                    s = input()
                    if s in self.boss:
                        self.boss.pop(s)
                        self.saveBosses()
                        print("Done")
                    else:
                        print("Not found")
                        r = self.search_boss(s)
                        if len(r) > 0:
                            print("Listing bosses matching the keywords...")
                            print("*", "\n* ".join(r))
                case '3':
                    print("Input the name of a Boss Fight to toggle the Name Fix")
                    s = input()
                    if s in self.boss:
                        self.boss[s][3] = not self.boss[s][3]
                        print("Fix is", ("enabled" if self.boss[s][3] else "disabled"), "for", s)
                        self.saveBosses()
                        print("Generating preview...")
                        img = await self.generateBackground(*(self.boss[s]))
                        if img is None:
                            print("An error occured, aborting...")
                        else:
                            print("Opening preview...")
                            img.show()
                            img.close()
                        print("Done")
                    else:
                        print("Not found")
                        r = self.search_boss(s)
                        if len(r) > 0:
                            print("Listing bosses matching the keywords...")
                            print("*", "\n* ".join(r))
                case '4':
                    print("# Explanation")
                    print("Bosses make up the background of your thumbnail.")
                    print("They are composed of three elements:")
                    print("- A background (usually the background used in the raid).")
                    print("- A boss ID. Said boss must have a \"raid_appear\" spritesheet.")
                    print("- A boss ID used for the bottom left corner icon. It can be different from the spritesheet one (some bosses do share asset).")
                    print("- Fixing a boss name is a workaround implemented for some bosses, where the boss name will be bugged.")
                    print("You can browser through https://mizagbf.github.io/GBFAL/ to look for a boss with a specific \"raid_appear\" spritesheet, or use the Chrome Dev Tools in-game.")
                case _:
                    break

    # stamp management menu
    async def manageStamp(self : GBFTMR):
        while True:
            print("")
            print("Stamp Management Menu")
            print("[0] Search Stamp by keyword")
            print("[1] Register Stamp")
            print("[2] Delete Stamp")
            print("[3] Tutorial")
            print("[Any] Back")
            s = input()
            match s:
                case '0':
                    print("Input keywords to search")
                    r = self.search_stamp(input())
                    if len(r) > 0:
                        print("Listing stamps matching the keywords...")
                        print("*", "\n* ".join(r))
                    print(len(r), "positive result(s)")
                case '1':
                    await self.addStamp()
                case '2':
                    print("Input the name of a Stamp to delete")
                    s = input()
                    if s in self.stamp:
                        self.stamp.pop(s)
                        self.saveStamps()
                        print("Done")
                    else:
                        print("Not found")
                        r = self.search_stamp(s)
                        if len(r) > 0:
                            print("Listing stamps matching the keywords...")
                            print("*", "\n* ".join(r))
                case '3':
                    print("# Explanation")
                    print("GBF Stamps or Stickers are added to thumbnail for flavor or comedy.")
                    print("This menu lets you register them in advance.")
                case _:
                    break

    # main menu CLI
    async def cli(self : GBFTMR):
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as self.client:
            while True:
                print("")
                print("Main Menu")
                print("[0] Generate Thumbnail")
                print("[1] Add Boss Fight")
                print("[2] Manage Boss Fights")
                print("[3] Manage Stamps")
                print("[4] Get Boss Bookmark")
                print("[Any] Quit")
                s = input()
                match s:
                    case '0':
                        await self.makeThumbnailManual()
                    case '1':
                        await self.addBoss()
                    case '2':
                        await self.manageBoss()
                    case '3':
                        await self.manageStamp()
                    case '4':
                        pyperclip.copy("javascript:(function () { let copyListener = event => { document.removeEventListener(\"copy\", copyListener, true); event.preventDefault(); let clipboardData = event.clipboardData; clipboardData.clearData(); clipboardData.setData(\"text/plain\", \"$$boss:\"+(stage.pJsnData.is_boss != null ? stage.pJsnData.is_boss.split(\"_\").slice(2).join(\"_\") : stage.pJsnData.boss.param[0].cjs.split(\"_\")[1])+\"|\"+stage.pJsnData.background.split(\"/\")[4].split(\".\")[0]+\"|\"+stage.pJsnData.boss.param[0].cjs.split(\"_\")[1]); }; document.addEventListener(\"copy\", copyListener, true); document.execCommand(\"copy\"); })();")
                        print("Bookmark copied!")
                        print("Make a new bookmark and paste the code in the url field")
                        print("Use it in battle to retrieve the boss and background data")
                        print("You can use it to set the boss thumbnail directly")
                    case _:
                        break

if __name__ == "__main__":
    asyncio.run(GBFTMR().cli())