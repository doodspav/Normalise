from PIL import Image, ImageFont, ImageDraw
from word2number import w2n
from unidecode import unidecode
import time, datetime, unicodedata

class Normalise:
    """
    Prerequisites:
    - self.cur (from MySQLdb)
    """
    def __init__(self):
        self.normalisation = {}
        #self.cur.execute("SELECT * FROM `normalisation`")
        #for row in self.cur.fetchall():
        #   self.normalisation[row[0]] = row[1]
        self.alphanumerical = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
        self.punctuation = list("!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~")
        self.extra = {"ß": "ss", "æ": "ae", "Æ": "AE"}
        self.allowed_chars = self.alphanumerical + self.punctuation + self.extra.keys()
        #emoji stuff - unicode v11.0
        emoji_ranges = [(8596, 8601), (8617, 8618), (8986, 8987), (9193, 9203), (9208, 9210), (9642, 9643), (9723, 9726), (9728, 9732), (9748, 9749), (9762, 9763), (9774, 9775), (9784, 9786), (9800, 9811), (9823, 9824), (9829, 9830), (9854, 9855), (9874, 9879), (9883, 9884), (9888, 9889), (9898, 9899), (9904, 9905), (9917, 9918), (9924, 9925), (9934, 9935), (9939, 9940), (9961, 9962), (9968, 9973), (9975, 9978), (9992, 9997), (10035, 10036), (10067, 10069), (10083, 10084), (10133, 10135), (10548, 10549), (11013, 11015), (11035, 11036), (127344, 127345), (127358, 127359), (127377, 127386), (127462, 127487), (127489, 127490), (127538, 127546), (127568, 127569), (127744, 127777), (127780, 127891), (127894, 127895), (127897, 127899), (127902, 127984), (127987, 127989), (127991, 127994), (127999, 128253), (128255, 128317), (128329, 128334), (128336, 128359), (128367, 128368), (128371, 128378), (128394, 128397), (128405, 128406), (128420, 128421), (128433, 128434), (128450, 128452), (128465, 128467), (128476, 128478), (128506, 128591), (128640, 128709), (128715, 128722), (128736, 128741), (128747, 128748), (128755, 128761), (129296, 129338), (129340, 129342), (129344, 129349), (129351, 129392), (129395, 129398), (129404, 129442), (129456, 129465), (129472, 129474), (129488, 129535), (917602, 917603), (917619, 917620)]
        emoji_ints = [169, 174, 8205, 8252, 8265, 8419, 8482, 8505, 9000, 9167, 9410, 9654, 9664, 9742, 9745, 9752, 9757, 9760, 9766, 9770, 9792, 9794, 9827, 9832, 9851, 9881, 9928, 9937, 9981, 9986, 9989, 9999, 10002, 10004, 10006, 10013, 10017, 10024, 10052, 10055, 10060, 10062, 10071, 10145, 10160, 10175, 11088, 11093, 12336, 12349, 12951, 12953, 65039, 126980, 127183, 127374, 127514, 127535, 128391, 128400, 128424, 128444, 128481, 128483, 128488, 128495, 128499, 128745, 128752, 129402, 917605, 917607, 917612, 917614, 917623, 917631]
        self.emoji_ords = emoji_ints
        for emr in emoji_ranges:
            self.emoji_ords += list(range(emr[0],emr[1]+1))
        self.allowed_emojis = {10134: '-', 127374: 'ab', 127377: 'cl', 127378: 'cool', 127379: 'free', 127380: 'id', 127381: 'new', 10006: 'x', 127383: 'ok', 127384: 'sos', 127385: 'up', 127386: 'vs', 128283: 'on', 128281: 'back', 128285: 'top', 128176: '$', 8482: 'tm', 127382: 'ng', 169: 'c', 174: 'r', 128175: '100', 12336: '~', 127921: '8', 128178: '$', 129353: '3', 8505: 'i', 128282: 'end', 8252: '!!', 128702: 'wc', 9410: 'm', 127920: '777', 129351: '1', 129352: '2', 8265: '!?', 10060: 'x', 10062: 'x', 10067: '?', 10068: '?', 10069: '!', 11093: 'o', 10071: '!', 127975: 'atm', 127344: 'a', 127345: 'b', 128284: 'soon', 127359: 'p', 127358: 'o', 10133: '+'}
        self.combining_chars = list(range(768, 880)), list(range(8192,8447))
        self.variation_selectors = [(65024, 65039), (917760, 917999)]
        for vs in variation_selector_ranges:
            self.variation_selectors += list(range(vs[0],vs[1]+1))


    def updateNormal(self, char_in, char_out, type_, vs):
        """
        Arguments:
        - char_in is the input char
        - char_out is the ouput char
        - type is the glyph form: isolate, inital, medial, or final - none means it doesnt matter
        - vs is whether the glyph requires a variation selector
        """
        #put in self.normalisation
        #update normalisation table
        pass

    def removeControlChars(self, text, remove_vs=False):
        language_tags = list(range(917505, 917760))
        interlinear_notation = [65529, 65530, 65531]
        bidirectional_text = [1564, 8206, 8207, 8234, 8235, 8236, 8237, 8238]
        seperators = [8232, 8233]
        specials = list(range(65520, 65536))
        control_0 = list(range(32))
        control_1 = list(range(128, 160))
        iso_extra = [8961, 9083, 9086, 9087, 9254]
        plane_endings
        total = language_tags + interlinear_notation + bidirectional_text + seperators + specials + control_0 + control_1 + iso_extra
        if remove_vs:
            total += self.variation_selectors
        #actually doing stuff
        to_remove = []
        for i in range(len(text)):
            if ord(i) in total:
                to_remove.append(i)
        to_remove.reverse()
        for tr in to_remove:
            text = text[:tr] + text[tr+1:]
        return text

    def removeCombiningChars(self, text):
        i = 0
        lentext = len(text)
        while i < lentext:
            ss = text[i] #substring
            if ss in self.combining_chars:
                text = text[:i] + text[i+1:]
            else:
                nfkd_list = list(unicodedata.normalize("NFKD",ss)) #compatibility
                nfd_list = [list(unicodedata.normalize("NFD",n)) for n in nfkd_list] #canonical equivalence
                ss_list = []
                for n in nfkd_list:
                    nfd = list(unicodedata.normalize("NFD",n)) #canonical equivalence
                    if n not in self.punctuation:
                        for nfd_char in nfd:
                            if nfd_char in self.punctuation:
                                nfd.remove(nfd_char)
                    ss_list += nfd
                for s in ss_list:
                    if s in self.combining_chars:
                        ss_list.remove(s)
                new_ss = "".join(ss_list)
                text = text[:i] + new_ss + text[i+1:]
            lentext = len(text)
            i += 1
        return text

    def normaliseLINEEmojis(self, text, blanks):
        #turn LINE emojis into either normal characters or replace with blanks
        i = 0
        lentext = len(text)
        while i < lentext:
            if ord(text[i]) > 1000000:
                e = text.find(chr(1114111), i)
                if e == -1:
                    text = text[:i] + text[i+1:]
                else:
                    start, mid, end = text[:i], text[i:e+1], text[e+1:]
                    emoji_id = [m for m in mid if ord(m) > 1000000]
                    mid = [m for m in mid if ord(m) < 1000000]
                    mid = "".join(mid)
                    if len(mid) in [1,2]:
                        if mid == "..":
                            mid = "..."
                        text = start + mid + end
                    elif len(mid) > 2:
                        try:
                            mid = w2n.word_to_num(mid)
                        except:
                            if emoji_id[0] == 1050625 and emoji_id[1] in range(1048833, 1048948):
                                text = start + mid + end
                            elif emoji_id[0] == 1056769 and emoji_id[1] in range(1048966, 1049040):
                                if emoji_id[1] == 1049036:
                                    mid = "13"
                                text = start + mid + end
                            elif mid in ["oz.","ml."]:
                                text = start + mid + end
                            else:
                                text = start + " " + end
                                blanks.append(i)
                    else:
                        text = start + " " + end
                        blanks.append(i)
                lentext = len(text)
            i += 1
        return text, blanks

    def normaliseEmojis(self, text, blanks, remove=True):
        #turn emojis into alphanumerical characters or punctuation, or replace with blanks
        i = 0
        lentext = len(text)
        while i < lentext:
            o = ord(text[i])
            if o in self.emoji_ords:
                if o in self.allowed_emojis.keys():
                    text = text[:i] + self.allowed_emojis[o] + text[i+1:]
                elif remove == True:
                    text = text[:i] + " " + text[i+1:]
                    blanks.append(i)
                lentext = len(text)
            i += 1
        return text, blanks

    def normaliseWithUnidecode(self, text):
        for i in range(len(text)):
            if text[i] not in self.allowed_chars:
                u = unidecode(text[i])
                if len(u) == 1:
                    text = text[:i] + u + text[i+1:]
        return text

    def normaliseExtra(self, text):
        i = 0
        lentext = len(text)
        while i < lentext:
            if text[i] in self.extra.keys():
                text = text[:i] + self.extra[text[i]] + text[i+1:]
                lentext = len(text)
            i += 1

    def adjustForVariationSelectors(self, text, blanks):
        pass

    def removeVariationSelectors(self, text):
        to_remove = []
        for i in range(len(text)):
            if ord(textL[i]) in self.variation_selectors:
                to_remove.append(i)
        to_remove.reverse()
        for tr in to_remove:
            text = text[:i] + text[i+1:]
        return text

    def normaliseText(self, text):
        blanks = []
        text = self.removeControlChars(text)
        text = self.removeCombiningChars(text)
        text = self.normaliseWithUnidecode(text)
        text = self.normaliseExtra(text)
        text, blanks = self.normaliseLINEEmojis(text, blanks)
        text, blanks = self.normaliseEmojis(text, blanks)
        vs, blanks = self.adjustForVariationSelectors(text, blanks)
        text = self.removeVariationSelectors(text)
        #remove blanks
        blanks = blanks[::-1]
        for b in blanks:
            text = text[:b] + text[b+1:]
        texts = text.split()
        if len(texts[0]) == 0:
            texts = texts[1:]
        text = " ".join(texts)
        text = text.rstrip()
        return text
