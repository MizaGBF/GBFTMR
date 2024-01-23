import json
import re
import httpx
from PIL import Image, ImageFont, ImageDraw
from io import BytesIO
import pyperclip
import os
import base64
import copy

class GBFTMR():
    def __init__(self, path=""):
        self.version = [1, 25]
        print("GBF Thumbnail Maker Remake v{}.{}".format(self.version[0], self.version[1]))
        self.path = path
        self.client = httpx.Client(http2=False, limits=httpx.Limits(max_keepalive_connections=50, max_connections=50, keepalive_expiry=10))
        self.cache = {}
        self.classes = { # class prefix (gotta add them manually, sadly)
            10: 'sw',
            11: 'sw',
            12: 'wa',
            13: 'wa',
            14: 'kn',
            15: 'sw',
            16: 'me',
            17: 'bw',
            18: 'mc',
            19: 'sp',
            30: 'sw',
            41: 'ax',
            42: 'sp',
            43: 'me',
            44: 'bw',
            45: 'sw',
            20: 'kn',
            21: 'kt',
            22: 'kt',
            23: 'sw',
            24: 'gu',
            25: 'wa',
            26: 'kn',
            27: 'mc',
            28: 'kn',
            29: 'gu'
        }
        self.nullchar = [3030182000, 3020072000]
        self.regex = [
            re.compile('(30[0-9]{8})_01\\.'),
            re.compile('(20[0-9]{8})_03\\.'),
            re.compile('(20[0-9]{8})_02\\.'),
            re.compile('(20[0-9]{8})\\.'),
            re.compile('(10[0-9]{8})\\.')
        ]
        self.asset_urls = [
            [
                "https://prd-game-a1-granbluefantasy.akamaized.net/assets_en/img/sp/assets/leader/s/{}.jpg",
                "https://prd-game-a1-granbluefantasy.akamaized.net/assets_en/img/sp/assets/leader/quest/{}.jpg",
                "ttp://prd-game-a1-granbluefantasy.akamaized.net/assets_en/img/sp/assets/leader/my/{}.png",
                "https://prd-game-a1-granbluefantasy.akamaized.net/assets_en/img/sp/assets/leader/job_change/{}.png",
                "https://prd-game-a1-granbluefantasy.akamaized.net/assets_en/img/sp/assets/leader/job_change/{}.png"
            ],
            [
                "https://prd-game-a-granbluefantasy.akamaized.net/assets_en/img/sp/assets/weapon/s/{}.jpg",
                "https://prd-game-a-granbluefantasy.akamaized.net/assets_en/img/sp/assets/weapon/m/{}.jpg",
                "https://prd-game-a-granbluefantasy.akamaized.net/assets_en/img/sp/assets/weapon/b/{}.png",
                "https://prd-game-a-granbluefantasy.akamaized.net/assets_en/img/sp/assets/weapon/b/{}.png",
                "https://prd-game-a-granbluefantasy.akamaized.net/assets_en/img/sp/assets/weapon/b/{}.png"
            ],
            [
                "https://prd-game-a-granbluefantasy.akamaized.net/assets_en/img/sp/assets/summon/s/{}.jpg",
                "https://prd-game-a1-granbluefantasy.akamaized.net/assets_en/img/sp/assets/summon/m/{}.jpg",
                "https://prd-game-a1-granbluefantasy.akamaized.net/assets_en/img/sp/assets/summon/my/{}.png",
                "https://prd-game-a-granbluefantasy.akamaized.net/assets_en/img/sp/assets/summon/b/{}.png",
                "https://prd-game-a-granbluefantasy.akamaized.net/assets_en/img/sp/assets/summon/b/{}.png"
            ],
            [
                "https://prd-game-a1-granbluefantasy.akamaized.net/assets_en/img/sp/assets/npc/s/{}.jpg",
                "https://prd-game-a1-granbluefantasy.akamaized.net/assets_en/img/sp/assets/npc/quest/{}.jpg",
                "https://prd-game-a1-granbluefantasy.akamaized.net/assets_en/img/sp/assets/npc/my/{}.png",
                "https://prd-game-a-granbluefantasy.akamaized.net/assets_en/img_low/sp/assets/npc/b/{}.png",
                "https://media.skycompass.io/assets/customizes/characters/1138x1138/{}.png"
            ],
            [
                "assets/{}",
                "assets/{}",
                "assets/{}",
                "assets/{}",
                "assets/{}"
            ],
            [
                "https://prd-game-a-granbluefantasy.akamaized.net/assets_en/img/sp/assets/weapon/s/{}.jpg",
                "https://prd-game-a1-granbluefantasy.akamaized.net/assets_en/img/sp/deckcombination/base_empty_weapon_sub.png",
                "",
                "",
                ""
            ],
            [
                "https://prd-game-a1-granbluefantasy.akamaized.net/assets_en/img/sp/assets/npc/s/{}.jpg",
                "https://prd-game-a1-granbluefantasy.akamaized.net/assets_en/img/sp/deckcombination/base_empty_npc.jpg",
                "",
                "",
                ""
            ]
        ]
        self.possible_pos = ["topleft", "left", "bottomleft", "bottom", "bottomright", "right", "topright", "top", "middle"]
        self.possible_display = ["squareicon", "partyicon", "fullart", "homeart", "skycompass"]
        self.boss = {}
        self.stamp = {}
        self.loadBosses()
        self.loadStamps()
        self.template = {}
        self.loadTemplates()
        tmp = Image.open(self.path+"assets/mask.png")
        self.mask = tmp.convert('L')
        tmp.close()

    def loadTemplates(self):
        try:
            with open(self.path+"template.json", mode="r", encoding="utf-8") as f:
                self.template = json.load(f)
        except Exception as e:
            print(e)

    def loadBosses(self):
        try:
            with open(self.path+"boss.json", mode="r", encoding="utf-8") as f:
                self.boss = json.load(f)
        except:
            pass

    def saveBosses(self):
        try:
            with open(self.path+"boss.json", mode="w", encoding="utf-8") as f:
                json.dump(self.boss, f, ensure_ascii=False)
            print("'boss.json' updated")
        except:
            pass

    def loadStamps(self):
        try:
            with open(self.path+"stamp.json", mode="r", encoding="utf-8") as f:
                self.stamp = json.load(f)
        except:
            pass

    def saveStamps(self):
        try:
            with open(self.path+"stamp.json", mode="w", encoding="utf-8") as f:
                json.dump(self.stamp, f, ensure_ascii=False)
            print("'stamp.json' updated")
        except:
            pass

    def checkDiskCache(self): # check if cache folder exists (and create it if needed)
        if not os.path.isdir(self.path + 'cache'):
            os.mkdir(self.path + 'cache')

    def getAsset(self, url):
        response = self.client.get(url, headers={'connection':'keep-alive'})
        if response.status_code != 200: raise Exception()
        return response.content

    def bookmarkString(self, s):
        if s.startswith("$$boss:"):
            return tuple(s.replace("$$boss:", "").split('|'))
        else:
            return None, None, None

    def addBoss(self):
        print("Input an Enemy ID with a valid Appear animation (Leave blank to cancel)")
        s = input()
        if s == "": return
        if s.lower() == "cc":
            try:
                s = pyperclip.paste()
            except:
                s = "cc"
        eid, bg, eico = self.bookmarkString(s)
        if eid is None:
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
                if s != "None":
                    if s.lower() == "cc":
                        try:
                            s = pyperclip.paste()
                        except:
                            s = "cc"
                    eico = s
            else:
                eico = eid
        print("Generating a preview...")
        img = self.generateBackground(eid, bg, eico)
        if img is None:
            print("An error occured, check if the ID you provided are correct")
            return
        else:
            img.show()
            img.close()
        while True:
            print("Input a boss name to save those settings (Leave blank to cancel)")
            s = input().lower()
            if s == "": return
            if s in self.boss:
                print(s, "already exists, overwrite? ('y' to confirm)")
                if input().lower() != 'y':
                    continue
            self.boss[s] = [eid, bg, eico]
            self.saveBosses()
            break

    def addStamp(self):
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
                self.getAsset(s)
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

    def get_mc_job_look(self, skin, job): # get the MC unskined filename based on id
        jid = job // 10000
        if jid not in self.classes: return skin
        return "{}_{}_{}".format(job, self.classes[jid], '_'.join(skin.split('_')[2:]))

    def check_id(self, id, recur=True): # check an element id and return it if valid (None if error)
        if id is None or not isinstance(id, str): return None
        try:
            if len(id.replace('skin/', '').split('_')[0]) != 10: raise Exception("MC?")
            int(id.replace('skin/', '').split('_')[0])
            t = int(id.replace('skin/', '')[0])
        except Exception as e:
            if str(e) == "MC?":
                t = 0
                if len(id.split("_")) != 4:
                    try:
                        id = self.get_mc_job_look(None, id)
                    except:
                        if recur: return self.check_id(self.search_id_on_wiki(id), recur=False) # wiki check
                        else: return None
            else:
                if recur: return self.check_id(self.search_id_on_wiki(id), recur=False) # wiki check
                else: return None
        if id is None:
            return None
        if t > 1 and '_' not in id:
            id += '_' + input("Input uncap/modifier string:")
        return id

    def get_uncap_id(self, cs): # to get character portraits based on uncap levels
        return {2:'02', 3:'02', 4:'02', 5:'03', 6:'04'}.get(cs, '01')

    def valid_name(self, s):
        for c in s:
            if c not in "abcdefghijklmnopqrstuvwxyz0123456789_":
                return False
        return True

    def generateBackground(self, eid, bg, eico):
        try:
            if "_" in eid:
                ext = "_"+eid.split("_")[1]
                eid = eid.split("_")[0]
            else:
                ext = ""
            cjs = self.getAsset("https://prd-game-a3-granbluefantasy.akamaized.net/assets_en/js/cjs/raid_appear_{}{}.js".format(eid, ext)).decode('utf-8')
            token = "raid_appear_"+eid+ext+"_"
            pos = 0
            elements = {}
            while True:
                a = cjs.find(token, pos)
                if a == -1: break
                b = cjs.find("=", a)
                if b == -1: break
                name = cjs[a+len(token):b]
                if not self.valid_name(name) or name in elements:
                    pos = a + len(token)
                    continue
                c = cjs.find(".Rectangle(", b)
                if c == -1: break
                d = cjs.find(")", c)
                if d == -1: break
                rect = cjs[c+len(".Rectangle("):d]
                pos = d
                elements[name] = []
                rect = rect.split(',')
                for r in rect:
                    if r.startswith('.'): r = '0'+r
                    elements[name].append(float(r))
                elements[name][2] += elements[name][0]
                elements[name][3] += elements[name][1]
            if bg is not None:
                with BytesIO(self.getAsset("https://game.granbluefantasy.jp/assets_en/img/sp/raid/bg/{}.jpg".format(bg))) as img_data:
                    img = Image.open(img_data)
                    mod = 1280/img.size[0]
                    tmp = img.resize((int(img.size[0]*mod), int(img.size[0]*mod)), Image.Resampling.LANCZOS)
                    img.close()
                    img = tmp
                    y = img.size[1]//2-360
                    tmp = img.crop((0, y, 1280, y+720))
                    img.close()
                    img = tmp
                    tmp = Image.new("L", img.size, "white")
                    img.putalpha(tmp)
                    tmp.close()
                    background = img
            else:
                background = None
            
            # debug
            if False:
                for k in elements:
                    print(k, elements[k])
            
            # mostly fixes for diaspora, sieg etc...
            parts = []
            for p in ['boss', 'bg', 'vs', 'name_a', 'name_b']:
                if p in elements:
                    parts.append(p)
            if 'opq_boss' in elements: # salmun golem
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
            if 'opq_vs' in elements: # salmun golem
                found = False
                for i in range(len(parts)):
                    if parts[i] == 'vs':
                        parts[i] = 'opq_vs'
                        found = True
                        break
                if not found: parts.append('opq_vs')
            name_y_off = 0
            if 'name_a' in elements:
                name_y_off = int(max(135, elements['name_a'][3] - elements['name_a'][1])) - 135
            if 'opq_name_a' in elements: # salmun golem
                found = False
                for i in range(len(parts)):
                    if parts[i] == 'name_a':
                        parts[i] = 'opq_name_a'
                        found = True
                        break
                if not found: parts.append('opq_name_a')
                name_y_off = int(max(135, elements['opq_name_a'][3] - elements['opq_name_a'][1])) - 135
            if 'name_b' in elements:
                name_y_off = int(max(135, elements['name_b'][3] - elements['name_b'][1])) - 135
            if 'boss_a' in elements:
                name_y_off = int(max(135, elements['boss_a'][3] - elements['boss_a'][1])) - 135
                parts[-1] = 'boss_a'
            if 'name_vs' in elements: parts.append('name_vs')
            if 'jp' in elements: parts.append('jp')
            if 'en' in elements: parts.append('en')

            with BytesIO(self.getAsset("https://prd-game-a1-granbluefantasy.akamaized.net/assets_en/img/sp/cjs/raid_appear_{}{}.png".format(eid, ext))) as img_data:
                appear = Image.open(img_data)
                tmp = appear.convert('RGBA')
                appear.close()
                appear = tmp
                img = self.make_canvas((1280, 720))
                for k in parts:
                    crop = appear.crop(tuple(elements[k]))
                    match k:
                        case 'boss'|'opq_boss':
                            mod = min(720/crop.size[0], 720/crop.size[1])
                            tmp = crop.resize((int(crop.size[0]*mod), int(crop.size[1]*mod)), Image.Resampling.LANCZOS)
                            crop.close()
                            crop = tmp
                            offset = (-20, 0)
                        case 'bg':
                            if k == parts[0]: offset = (0, 0)
                            else: offset = ((640 - crop.size[0]) // 2, 360-name_y_off)
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
                    layer = self.make_canvas((1280, 720))
                    layer.paste(crop, offset, crop)
                    mod = Image.alpha_composite(img, layer)
                    img.close()
                    layer.close()
                    crop.close()
                    img = mod
                    if (k == 'bg' and k != parts[0]) or (parts[0] == 'bg' and k == 'vs_bg'): # gradient
                        grad = self.make_canvas((1280, 720))
                        tmp = Image.composite(img, grad, self.mask)
                        img.close()
                        grad.close()
                        img = tmp
                if background is not None:
                    tmp = Image.alpha_composite(background, img)
                    background.close()
                    img.close()
                    img = tmp
            try:
                if eico is not None:
                    with BytesIO(self.getAsset("https://prd-game-a-granbluefantasy.akamaized.net/assets_en/img/sp/assets/enemy/m/{}.png".format(eico))) as img_data:
                        mod = Image.open(img_data)
                        tmp = mod.convert("RGBA")
                        mod.close()
                        layer = self.make_canvas((1280, 720))
                        layer.paste(tmp, (15, 720-tmp.size[1]-15), tmp)
                        tmp.close()
                        tmp = Image.alpha_composite(img, layer)
                        img.close()
                        layer.close()
                        img = tmp
            except Exception as e:
                print(e)
            return img
        except Exception as me:
            print(me)
            return None

    def make_canvas(self, size): # make a blank image to the specified size
        i = Image.new('RGB', size, "black")
        im_a = Image.new("L", i.size, "black")
        i.putalpha(im_a)
        im_a.close()
        return i

    def addTuple(self, A:tuple, B:tuple): # to add pairs together
        return (A[0]+B[0], A[1]+B[1])

    def mulTuple(self, A:tuple, f:float): # multiply a pair by a value
        return (int(A[0]*f), int(A[1]*f))

    # GBFPIB compatibility
    def getTemplateList(self):
        return list(self.template.keys())

    def getThumbnailOptions(self, k):
        if k not in self.template: return None
        options = {"template":copy.deepcopy(self.template[k]), "settings":{}, "choices":[]}
        for i, e in enumerate(options["template"]):
            match e["type"]:
                case "background":
                    options["choices"].append(["Background", ["None"]+list(self.boss.keys()), [None]+list(self.boss.keys()), "settings", self.autoSetBG])
                case "boss":
                    options["choices"].append(["Boss ID", None, None, "settings", self.autoSetBoss])
                    options["choices"].append(["Boss Icon", None, None, "settings", self.autoSetBossIcon])
                case "stamp":
                    options["choices"].append(["Stamp", ["None"]+list(self.stamp.keys()), [None]+list(self.stamp.keys()), "template-"+str(i), self.autoSetStamp])
                    e["type"] = "asset"
                case "autoinput":
                    options["choices"].append(["Auto Setting", ["Manual", "Auto", "Full Auto", "Full Auto Guard"], [None, "auto.png", "fa.png", "fa_guard.png"], "template-"+str(i), self.autoSetAsset])
                    e["type"] = "asset"
                case "nminput":
                    options["choices"].append(["GW or DB ID", None, None, "template-"+str(i), self.autoSetGW])
                    options["choices"].append(["NM Setting", ["None", "GW NM90", "GW NM95", "GW NM100", "GW NM150", "GW NM200", "DB 1*", "DB 2*", "DB 3*", "DB 4*", "DB 5*", "DB UF95", "DB UF135", "DB UF175", "DB Valiant"], [None, 90, 95, 100, 150, 200, 1, 2, 3, 4, 5, 11, 12, 13, 20], "template-"+str(i), self.autoSetNM])
                    e["type"] = "asset"
                case "prideinput":
                    options["choices"].append(["Pride ID", ["Gilbert", "Nalhe Great Wall", "Violet Knight", "Echidna", "Golden Knight", "White Knight", "Cherub", "Kikuri", "Zwei", "??? (10)", "??? (12)", "??? (12)"], [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], "template-"+str(i), self.autoSetPrideID])
                    options["choices"].append(["Pride Difficulty", ["Proud", "Proud+"], [False, True], "template-"+str(i), self.autoSetPrideDifficulty])
                    e["type"] = "asset"
                case "textinput":
                    options["choices"].append([e["ref"], None, None, "choices-"+str(len(options["choices"])), self.autoSetText])
        return options

    def getOptionTarget(self, options, target):
        match target:
            case "settings": return options["settings"]
            case _:
                if target.startswith('choices'):
                    el = target.split('-')
                    el[1] = int(el[1])
                    return options["choices"][el[1]]
                elif target.startswith('template'):
                    el = target.split('-')
                    el[1] = int(el[1])
                    return options["template"][el[1]]

    def autoSetText(self, options, target, value):
        t = self.getOptionTarget(options, target)
        options["settings"][t[0]] = value

    def autoSetBG(self, options, target, value):
        if value is None: return
        t = self.getOptionTarget(options, target)
        data = self.bookmarkString(value)
        if data[0]is not None:
            t["bg"] = data
        else:
            t["bg"] = self.boss[value]

    def autoSetStamp(self, options, target, value):
        if value is None: return
        t = self.getOptionTarget(options, target)
        if value in self.stamp:
            t["asset"] = self.stamp[value]

    def autoSetBoss(self, options, target, value):
        if value == "": return
        t = self.getOptionTarget(options, target)
        data = self.bookmarkString(value)
        if data[0]is not None:
            t["boss"] = [data[0], data[2]]
        elif not value.isdigit() and value in self.boss:
            t["boss"] = [self.boss[value][0], self.boss[value][2]]
        else:
            t["boss"] = [value, None]

    def autoSetBossIcon(self, options, target, value):
        t = self.getOptionTarget(options, target)
        if "boss" not in t: return
        if value == "":
            t["boss"][1] = t["boss"][0]
        else:
            t["boss"][1] = value

    def autoSetAsset(self, options, target, value):
        t = self.getOptionTarget(options, target)
        t["asset"] = value

    def autoSetGW(self, options, target, value):
        t = self.getOptionTarget(options, target)
        t["gwn"] = value

    def autoSetNM(self, options, target, value):
        t = self.getOptionTarget(options, target)
        if value is None:
            t["asset"] = value
        else:
            if value < 10:
                t["asset"] = "https://prd-game-a1-granbluefantasy.akamaized.net/assets_en/img_low/sp/assets/summon/qm/teamforce{}_star{}.png".format(t["gwn"].zfill(2), value)
            elif value < 20:
                t["asset"] = "https://prd-game-a1-granbluefantasy.akamaized.net/assets_en/img/sp/assets/summon/qm/teamforce{}_strong{}.png".format(t["gwn"].zfill(2), int(value)-10)
            elif value == 20:
                t["asset"] = "https://prd-game-a1-granbluefantasy.akamaized.net/assets_en/img/sp/assets/summon/qm/teamforce{}_sp.png".format(t["gwn"].zfill(2))
            else:
                t["asset"] = "https://prd-game-a1-granbluefantasy.akamaized.net/assets_en/img/sp/event/teamraid{}/assets/thumb/teamraid{}_hell{}.png".format(t["gwn"].zfill(3), t["gwn"].zfill(3), value)

    def autoSetPrideID(self, options, target, value):
        t = self.getOptionTarget(options, target)
        t["pridenum"] = str(value).zfill(3)

    def autoSetPrideDifficulty(self, options, target, value):
        t = self.getOptionTarget(options, target)
        if value is None:
            t["asset"] = value
        else:
            t["asset"] = "https://prd-game-a1-granbluefantasy.akamaized.net/assets_en/img/sp/quest/assets/free/conquest_{}_proud{}.png".format(t["pridenum"], "plus" if value else "")

    # end of GBFPIB compatibility

    def makeThumbnailManual(self, gbfpib=None):
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
        template = copy.deepcopy(self.template[k])
        for e in template:
            match e["type"]:
                case "background":
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
                case "boss":
                    print("Input the ID of the boss you want to display (Leave blank to ignore)")
                    s = input().lower()
                    if s != "":
                        data = self.bookmarkString(s)
                        if data[0] is not None:
                            settings['boss'] = [data[0], data[2]]
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
                                settings['boss'] = [self.boss[s][0], self.boss[s][2]]
                            else:
                                settings['boss'] = [s, None]
                            if settings['boss'][1] is None:
                                print("Input the ID of the boss whose icon you want to display, if different (Leave blank to ignore)")
                                s = input().lower()
                                if s != "":
                                    settings['boss'][1] = s
                                else:
                                    settings['boss'][1] = settings['boss'][0]
                case "stamp":
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
                                    self.getAsset(s)
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
                case "party":
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
                case "autoinput":
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
                case "nminput":
                    print("Select a GW NM or DB Foe:")
                    print("[0] GW NM90")
                    print("[1] GW NM95")
                    print("[2] GW NM100")
                    print("[3] GW NM150")
                    print("[4] GW NM200")
                    print("[5] DB 1*")
                    print("[6] DB 2*")
                    print("[7] DB 3*")
                    print("[8] DB 4*")
                    print("[9] DB 5*")
                    print("[10] DB UF95")
                    print("[11] DB UF135")
                    print("[12] DB UF175")
                    print("[13] DB Valiant")
                    print("[Any] Skip")
                    match input():
                        case "0": nm = 90
                        case "1": nm = 95
                        case "2": nm = 100
                        case "3": nm = 150
                        case "4": nm = 200
                        case "5": nm = 1
                        case "6": nm = 2
                        case "7": nm = 3
                        case "8": nm = 4
                        case "9": nm = 5
                        case "10": nm = 11
                        case "11": nm = 12
                        case "12": nm = 13
                        case "13": nm = 20
                        case _: nm = None
                    if nm is not None:
                        print("Input a GW or DB ID:")
                        gwn = input()
                        if nm < 10:
                            e["asset"] = "https://prd-game-a1-granbluefantasy.akamaized.net/assets_en/img/sp/assets/summon/qm/teamforce{}_star{}.png".format(gwn.zfill(2), nm)
                        elif nm < 20:
                            e["asset"] = "https://prd-game-a1-granbluefantasy.akamaized.net/assets_en/img/sp/assets/summon/qm/teamforce{}_strong{}.png".format(gwn.zfill(2), nm-10)
                        elif nm == 20:
                            e["asset"] = "https://prd-game-a1-granbluefantasy.akamaized.net/assets_en/img/sp/assets/summon/qm/teamforce{}_sp.png".format(gwn.zfill(2))
                        else:
                            e["asset"] = "https://prd-game-a1-granbluefantasy.akamaized.net/assets_en/img/sp/event/teamraid{}/assets/thumb/teamraid{}_hell{}.png".format(gwn.zfill(3), gwn.zfill(3), nm)
                        e["type"] = "asset"
                case "prideinput":
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
                    print("[Any] Anything Else")
                    pn = input().zfill(3)
                    e["asset"] = "https://prd-game-a1-granbluefantasy.akamaized.net/assets_en/img/sp/quest/assets/free/conquest_{}_proud{}.png".format(str(pn).zfill(3), p)
                    e["type"] = "asset"
                case "textinput":
                    print("Input the '{}'".format(e["ref"]))
                    settings[e["ref"]] = input()
        self.makeThumbnail(settings, template)

    def makeThumbnail(self, settings, template):
        print("[TMR] |--> Starting thumbnail generation...")
        img = self.make_canvas((1280, 720))
        for i, e in enumerate(template):
            print("[TMR] |--> Generating Element #{}: {}".format(i+1, e["type"]))
            match e["type"]:
                case "background":
                    img = self.auto_background(img, settings, e)
                case "boss":
                    img = self.auto_boss(img, settings, e)
                case "party":
                    img = self.auto_party(img, settings, e)
                case "asset":
                    img = self.auto_asset(img, settings, e)
                case "textinput":
                    img = self.auto_text(img, settings, e)
        print("[TMR] |--> Saving...")
        img.save("thumbnail.png", "PNG")
        img.close()
        print("[TMR] |--> thumbnail.png has been generated with success")

    def auto_background(self, img, settings, element):
        if 'bg' not in settings: return img
        bg = self.generateBackground(settings['bg'][0], settings['bg'][1], settings['bg'][2])
        if bg is None: return img
        modified = Image.alpha_composite(img, bg)
        img.close()
        bg.close()
        return modified

    def auto_boss(self, img, settings, element):
        if 'boss' not in settings: return img
        bg = self.generateBackground(settings['boss'][0], None, settings['boss'][1])
        if bg is None: return img
        modified = Image.alpha_composite(img, bg)
        img.close()
        bg.close()
        return modified

    def auto_asset(self, img, settings, element): # auto asset parsing
        if element.get("asset", None) is None: return img
        pos = element.get('anchor', 'topleft')
        offset = element.get('position', (0,0))
        ratio = element.get('size', 1.0)
        img = self.make_img_from_element(img, [element["asset"]], pos, offset, ratio)
        return img

    def auto_text(self, img, settings, element): # auto text parsing
        text = settings.get(element['ref'], '')
        if text == '': return img
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

    def fix_character_look(self, export, i):
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
        if cid in self.nullchar: 
            if export['ce'][i] == 99:
                return "{}_{}{}_0{}".format(cid, uncap, style, export['pce'])
            else:
                return "{}_{}{}_0{}".format(cid, uncap, style, export['ce'][i])
        else:
            return "{}_{}{}".format(cid, uncap, style)

    def auto_party(self, img, settings, element): # auto party drawing
        characters = []
        noskin = element.get("noskin", False)
        mainsummon = element.get("mainsummon", False)
        try:
            export = settings['gbfpib']
            babyl = (len(export['c']) > 5)
            if not mainsummon:
                if noskin:
                    characters.append(self.get_mc_job_look(export['pcjs'], export['p']))
                else:
                    characters.append(export['pcjs'])
            if babyl: nchara = 12
            else: nchara = 5
            for x in range(0, nchara):
                if mainsummon:break
                if babyl and x == 0:
                    continue
                if x >= len(export['c']) or export['c'][x] is None:
                    characters.append("3999999999")
                    continue
                if noskin:
                    characters.append(self.fix_character_look(export, x))
                else:
                    characters.append(export['ci'][x])
            if export['s'][0] is not None:
                characters.append(export['ss'][0])
            if not mainsummon:
                if export['w'][0] is not None and export['wl'][0] is not None:
                    characters.append(str(export['w'][0]))
                else:
                    characters.append("1999999999")
        except Exception as e:
            print("An error occured while importing a party:", e)
            raise Exception("Failed to import party data")
        pos = element.get('anchor', 'topleft')
        offset = element.get('position', (0,0))
        ratio = element.get('size', 1.0)
        if mainsummon:
            img = self.make_img_from_element(img, characters, pos, offset, ratio, "partyicon")
        elif babyl:
            img = self.make_img_from_element(img, characters[:4], pos, offset, ratio, "squareicon", (100, 100))
            img = self.make_img_from_element(img, characters[4:8], pos, self.addTuple(offset, self.mulTuple((0, 100), ratio)), ratio, "squareicon", (100, 100))
            img = self.make_img_from_element(img, characters[8:12], pos, self.addTuple(offset, self.mulTuple((0, 200), ratio)), ratio, "squareicon", (100, 100))
            img = self.make_img_from_element(img, characters[12:13], pos, self.addTuple(offset, self.mulTuple((0, 310), ratio)), ratio, "partyicon", (192, 108))
            img = self.make_img_from_element(img, characters[13:14], pos, self.addTuple(offset, self.mulTuple((208, 310), ratio)), ratio, "partyicon", (192, 108))
        else:
            img = self.make_img_from_element(img, characters[:4], pos, offset, ratio, "partyicon", (78, 142))
            img = self.make_img_from_element(img, characters[4:6], pos, self.addTuple(offset, self.mulTuple((78*4+15, 0), ratio)), ratio, "partyicon", (78, 142))
            img = self.make_img_from_element(img, characters[6:7], pos, self.addTuple(offset, self.mulTuple((25, 142+10), ratio)), 0.75*ratio, "partyicon", (280, 160))
            img = self.make_img_from_element(img, characters[7:8], pos, self.addTuple(offset, self.mulTuple((25+280*0.75+15, 142+10), ratio)), 0.75*ratio, "partyicon", (280, 160))
        return img

    def make_img_from_element(self, img, characters = [], pos = "middle", offset = (0, 0), ratio = 1.0, display = "squareicon", fixedsize=None): # draw elements onto an image
        modified = img.copy()
        match pos.lower():
            case "topleft":
                cur_pos = (0, 0)
            case "top":
                cur_pos = (640, 0)
            case "topright":
                cur_pos = (1280, 0)
            case "right":
                cur_pos = (1280, 360)
            case "bottomright":
                cur_pos = (1280, 720)
            case "bottom":
                cur_pos = (640, 720)
            case "bottomleft":
                cur_pos = (0, 720)
            case "left":
                cur_pos = (0, 360)
            case "middle":
                cur_pos = (640, 360)
        cur_pos = self.addTuple(cur_pos, offset)
        for c in characters:
            size, u = self.get_element_size(c, display)
            if size is None: continue
            if fixedsize is not None:
                size = fixedsize
            size = self.mulTuple(size, ratio)
            match pos.lower():
                case "topright":
                    cur_pos = self.addTuple(cur_pos, (-size[0], 0))
                case "right":
                    cur_pos = self.addTuple(cur_pos, (-size[0], 0))
                case "bottomright":
                    cur_pos = self.addTuple(cur_pos, (-size[0], -size[1]))
                case "bottom":
                    cur_pos = self.addTuple(cur_pos, (0, -size[1]))
                case "bottomleft":
                    cur_pos = self.addTuple(cur_pos, (0, -size[1]))
            if u.startswith("http"):
                modified = self.dlAndPasteImage(modified, u, cur_pos, resize=size)
            else:
                modified = self.pasteImage(modified, u, cur_pos, resize=size)
            cur_pos = self.addTuple(cur_pos, (size[0], 0))
        img.close()
        return modified

    def make_img_from_text(self, img, text = "", fc = (255, 255, 255), oc = (0, 0, 0), os = 10, bold = False, italic = False, pos = "middle", offset = (0, 0), fs = 24, lj = 0, rj = 0): # to draw text into an image
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
                text_pos = (0, 0)
            case "top":
                text_pos = (640-size[0]//2, 0)
            case "topright":
                text_pos = (1280-size[0], 0)
            case "right":
                text_pos = (1280-size[0], 360-size[1]//2)
            case "bottomright":
                text_pos = (1280-size[0], 720-size[1])
            case "bottom":
                text_pos = (640-size[0]//2, 720-size[1])
            case "bottomleft":
                text_pos = (0, 720-size[1])
            case "left":
                text_pos = (0, 360-size[1]//2)
            case "middle":
                text_pos = (640-size[0]//2, 360-size[1]//2)
        text_pos = self.addTuple(text_pos, offset)
        d.text(text_pos, text, fill=fc, font=font, stroke_width=os, stroke_fill=oc)
        img.close()
        return modified

    def get_element_size(self, c, display): # retrive an element asset and return its size
        try:
            if not c.startswith("http"):
                if c == "1999999999":
                    t = 5
                elif c == "3999999999":
                    t = 6
                else:
                    try:
                        if len(c.replace('skin/', '').split('_')[0]) < 10: raise Exception("MC?")
                        int(c.replace('skin/', '').split('_')[0])
                        t = int(c.replace('skin/', '')[0])
                    except Exception as e:
                        if str(e) == "MC?":
                            t = 0
                            if len(c.split("_")) != 4:
                                try:
                                    c = self.get_mc_job_look(None, c)
                                except:
                                    t = 4
                        else:
                            t = 4
                try: u = self.asset_urls[t][self.possible_display.index(display.lower())].format(c)
                except: u = self.asset_urls[t][self.possible_display.index(display.lower())]
                if t == 4: u = self.path + u
            else:
                u = c
            if u.startswith("http"):
                with BytesIO(self.dlImage(u)) as file_jpgdata:
                    buf = Image.open(file_jpgdata)
                    size = buf.size
                    buf.close()
            else:
                buf = Image.open(u)
                size = buf.size
                buf.close()
            return size, u
        except:
            return None, None

    def dlImage(self, url): # download an image (check the cache first)
        if url not in self.cache:
            self.checkDiskCache()
            try: # get from disk cache if enabled
                with open(self.path + "cache/" + base64.b64encode(url.encode('utf-8')).decode('utf-8'), "rb") as f:
                    self.cache[url] = f.read()
            except: # else request it from gbf
                self.cache[url] = self.getAsset(url)
                try:
                    with open(self.path + "cache/" + base64.b64encode(url.encode('utf-8')).decode('utf-8'), "wb") as f:
                        f.write(self.cache[url])
                except Exception as e:
                    print(url, ":", e)
                    pass
        return self.cache[url]

    def dlAndPasteImage(self, img, url, offset, resize=None, resizeType="default"): # call dlImage() and pasteImage()
        with BytesIO(self.dlImage(url)) as file_jpgdata:
            return self.pasteImage(img, file_jpgdata, offset, resize, resizeType)

    def pasteImage(self, img, file, offset, resize=None, resizeType="default"): # paste an image onto another
        buffers = [Image.open(file)]
        buffers.append(buffers[-1].convert('RGBA'))
        if resize is not None:
            match resizeType.lower():
                case "default":
                    buffers.append(buffers[-1].resize(resize, Image.Resampling.LANCZOS))
                case "fit":
                    size = buffers[-1].size
                    mod = min(resize[0]/size[0], resize[1]/size[1])
                    offset = self.addTuple(offset, (int(resize[0]-size[0]*mod)//2, int(resize[1]-size[1]*mod)//2))
                    buffers.append(buffers[-1].resize((int(size[0]*mod), int(size[1]*mod)), Image.Resampling.LANCZOS))
                case "fill":
                    size = buffers[-1].size
                    mod = max(resize[0]/size[0], resize[1]/size[1])
                    offset = self.addTuple(offset, (int(resize[0]-size[0]*mod)//2, int(resize[1]-size[1]*mod)//2))
                    buffers.append(buffers[-1].resize((int(size[0]*mod), int(size[1]*mod)), Image.Resampling.LANCZOS))
        size = buffers[-1].size
        if size[0] == img.size[0] and size[1] == img.size[1] and offset[0] == 0 and offset[1] == 0:
            modified = Image.alpha_composite(img, buffers[-1])
        else:
            layer = self.make_canvas((1280, 720))
            layer.paste(buffers[-1], offset, buffers[-1])
            modified = Image.alpha_composite(img, layer)
            layer.close()
        for buf in buffers: buf.close()
        del buffers
        return modified

    def search_boss(self, search):
        return self._search(search, self.boss)

    def search_stamp(self, search):
        return self._search(search, self.stamp)

    def _search(self, search, target):
        s = search.lower().split(" ")
        r = []
        for k in target:
            for i in s:
                if i != "" and i in k:
                    r.append(k)
                    break
        return r

    def manageBoss(self):
        while True:
            print("")
            print("Boss Management Menu")
            print("[0] Search Boss by keyword")
            print("[1] Preview Boss")
            print("[2] Delete Boss")
            print("[3] Tutorial")
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
                            img = self.generateBackground(*data)
                        else:
                            img = self.generateBackground(*(self.boss[s]))
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
                    print("# Explanation")
                    print("Bosses make up the background of your thumbnail.")
                    print("They are composed of three elements:")
                    print("- A background (usually the background used in the raid).")
                    print("- A boss ID. Said boss must have a \"raid_appear\" spritesheet.")
                    print("- A boss ID used for the bottom left corner icon. It can be different from the spritesheet one (some bosses do share asset).")
                    print("You can browser through https://mizagbf.github.io/GBFAL/ to look for a boss with a specific \"raid_appear\" spritesheet, or use the Chrome Dev Tools in-game.")
                case _:
                    break

    def manageStamp(self):
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
                    self.addStamp()
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

    def cmd(self):
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
                    self.makeThumbnailManual()
                case '1':
                    self.addBoss()
                case '2':
                    self.manageBoss()
                case '3':
                    self.manageStamp()
                case '4':
                    pyperclip.copy("javascript:(function () { let copyListener = event => { document.removeEventListener(\"copy\", copyListener, true); event.preventDefault(); let clipboardData = event.clipboardData; clipboardData.clearData(); clipboardData.setData(\"text/plain\", \"$$boss:\"+(stage.pJsnData.is_boss != null ? stage.pJsnData.is_boss.split(\"_\").slice(2).join(\"_\") : stage.pJsnData.boss.param[0].cjs.split(\"_\")[1])+\"|\"+stage.pJsnData.background.split(\"/\")[4].split(\".\")[0]+\"|\"+stage.pJsnData.boss.param[0].cjs.split(\"_\")[1]); }; document.addEventListener(\"copy\", copyListener, true); document.execCommand(\"copy\"); })();")
                    print("Bookmark copied!")
                    print("Make a new bookmark and paste the code in the url field")
                    print("Use it in battle to retrieve the boss and background data")
                    print("You can use it to set the boss thumbnail directly")
                case _:
                    break

if __name__ == "__main__":
    GBFTMR().cmd()