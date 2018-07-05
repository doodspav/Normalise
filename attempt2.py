from word2number import w2n
import unicodedata

class Normalise:
    def __init__(self):
        #standard characters + a few common non standard ones
        self.alphanumerical = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
        self.punctuation = list("!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~ ")
        self.extra_chars = {"ß": "ss", "æ": "ae", "Æ": "AE"}
        self.allowed_chars = self.alphanumerical + self.punctuation + list(self.extra_chars.keys())
        #emoji stuff - unicode v11.0
        #note: all the allowed emojis are a single codepoint
        emoji_ranges = [(8596, 8601), (8617, 8618), (8986, 8987), (9193, 9203), (9208, 9210), (9642, 9643), (9723, 9726), (9728, 9732), (9748, 9749), (9762, 9763), (9774, 9775), (9784, 9786), (9800, 9811), (9823, 9824), (9829, 9830), (9854, 9855), (9874, 9879), (9883, 9884), (9888, 9889), (9898, 9899), (9904, 9905), (9917, 9918), (9924, 9925), (9934, 9935), (9939, 9940), (9961, 9962), (9968, 9973), (9975, 9978), (9992, 9997), (10035, 10036), (10067, 10069), (10083, 10084), (10133, 10135), (10548, 10549), (11013, 11015), (11035, 11036), (127344, 127345), (127358, 127359), (127377, 127386), (127462, 127487), (127489, 127490), (127538, 127546), (127568, 127569), (127744, 127777), (127780, 127891), (127894, 127895), (127897, 127899), (127902, 127984), (127987, 127989), (127991, 127994), (127999, 128253), (128255, 128317), (128329, 128334), (128336, 128359), (128367, 128368), (128371, 128378), (128394, 128397), (128405, 128406), (128420, 128421), (128433, 128434), (128450, 128452), (128465, 128467), (128476, 128478), (128506, 128591), (128640, 128709), (128715, 128722), (128736, 128741), (128747, 128748), (128755, 128761), (129296, 129338), (129340, 129342), (129344, 129349), (129351, 129392), (129395, 129398), (129404, 129442), (129456, 129465), (129472, 129474), (129488, 129535), (917602, 917603), (917619, 917620)]
        emoji_ints = [169, 174, 8205, 8252, 8265, 8419, 8482, 8505, 9000, 9167, 9410, 9654, 9664, 9742, 9745, 9752, 9757, 9760, 9766, 9770, 9792, 9794, 9827, 9832, 9851, 9881, 9928, 9937, 9981, 9986, 9989, 9999, 10002, 10004, 10006, 10013, 10017, 10024, 10052, 10055, 10060, 10062, 10071, 10145, 10160, 10175, 11088, 11093, 12336, 12349, 12951, 12953, 65039, 126980, 127183, 127374, 127514, 127535, 128391, 128400, 128424, 128444, 128481, 128483, 128488, 128495, 128499, 128745, 128752, 129402, 917605, 917607, 917612, 917614, 917623, 917631]
        self.emoji_ords = emoji_ints
        for emr in emoji_ranges:
            self.emoji_ords += list(range(emr[0],emr[1]+1))
        self.allowed_emojis = {10134: '-', 127374: 'ab', 128292: 'abc', 127377: 'cl', 127378: 'cool', 127379: 'free', 127380: 'id', 127381: 'new', 10006: 'x', 127383: 'ok', 127384: 'sos', 127385: 'up', 127386: 'vs', 128283: 'on', 128281: 'back', 128285: 'top', 128176: '$', 8482: 'tm', 127382: 'ng', 169: 'c', 174: 'r', 128175: '100', 12336: '~', 127921: '8', 128178: '$', 129353: '3', 8505: 'i', 128282: 'end', 8252: '!!', 128702: 'wc', 9410: 'm', 127920: '777', 129351: '1', 129352: '2', 8265: '!?', 10060: 'x', 10062: 'x', 10067: '?', 10068: '?', 10069: '!', 11093: 'o', 10071: '!', 127975: 'atm', 127344: 'a', 127345: 'b', 128284: 'soon', 127359: 'p', 127358: 'o', 10133: '+', 9888: '!', 128164: 'zzz', 129288: 'ABCD', 128289: 'abcd', 128290: '1234'}
        self.__add_emoji_spaces()
        #variation selectors (only really used with CJK fonts, or mongolian fonts)
        variation_selector_ranges = [(65024, 65039), (917760, 917999)]
        self.variation_selectors = []
        for vs in variation_selector_ranges:
            self.variation_selectors += list(range(vs[0],vs[1]+1))
        #control characters (non text things such as U+0000)
        self.control_chars = self.__build_control_chars()

    def __add_emoji_spaces(self):
        for k in self.allowed_emojis.keys():
            v = self.allowed_emojis[k]
            is_punctuation = True
            for c in v:
                if c not in self.punctuation:
                    is_punctuation = False
                    break
            if is_punctuation:
                v += " "
            else:
                v = " " + v + " "
            self.allowed_emojis[k] = v

    def __build_control_chars(self):
        language_tags = list(range(917505, 917760)) #last one is 917631
        interlinear_notation = [65529, 65530, 65531]
        bidirectional_text = [1564, 8206, 8207, 8234, 8235, 8236, 8237, 8238]
        seperators = [8232, 8233]
        specials = list(range(65520, 65536))
        control_0 = list(range(32)) #not including 32 which is space
        control_1 = list(range(127, 160))
        iso_extra = [8961, 9083, 9086, 9087, 9254]
        total = language_tags + interlinear_notation + bidirectional_text + seperators + specials + control_0 + control_1 + iso_extra
        #total.remove(10) #\n
        return total

    def shift_blanks(self, start, amount, blanks):
        blanks = [b+amount if b > start else b for b in blanks]
        return blanks

    def remove_control_chars(self, text):
        to_remove = []
        for i in range(len(text)):
            if ord(text[i]) in self.control_chars:
                to_remove.append(i)
        to_remove.reverse()
        for tr in to_remove:
            text = text[:tr] + text[tr+1:]
        return text

    def normalise_with_forms(self, text):
        i = 0
        lentext = len(text)
        while i < lentext:
            ss = text[i] #substring
            nfkd_list = list(unicodedata.normalize("NFKD",ss)) #compatibility
            ss_list = []
            for n in nfkd_list:
                nfd = list(unicodedata.normalize("NFD",n)) #canonical equivalence
                if n not in self.punctuation:
                    [nfd.remove(nfd_char) for nfd_char in nfd if nfd_char in self.punctuation]
                ss_list += nfd
            new_ss = "".join(ss_list)
            text = text[:i] + new_ss + text[i+1:]
            lentext = len(text)
            i += 1
        return text

    def remove_combining_chars(self, text):
        to_remove = []
        for i in range(len(text)):
            if unicodedata.combining(text[i]) != 0:
                to_remove.append(i)
            elif ord(text[i]) in self.combining_chars:
                to_remove.append(i)
        to_remove.reverse()
        for tr in to_remove:
            text = text[:tr] + text[tr+1:]
        return text

    def remove_variation_selectors(self, text):
        to_remove = []
        for i in range(len(text)):
            if ord(text[i]) in self.variation_selectors:
                to_remove.append(i)
        to_remove.reverse()
        for tr in to_remove:
            text = text[:tr] + text[tr+1:]
        return text

    def normalise_extra_chars(self, text):
        i = 0
        lentext = len(text)
        while i < lentext:
            if text[i] in self.extra_chars.keys():
                text = text[:i] + self.extra_chars[text[i]] + text[i+1:]
                lentext = len(text)
            i += 1
        return text

    def normalise_LINE_emojis(self, text, blanks):
        i = 0
        lentext = len(text)
        while i < lentext:
            if ord(text[i]) > 1000000:
                e = text.find(chr(1114111), i)
                if e == -1 or e > i+15:
                    text = text[:i] + text[i+1]
                    blanks = self.shift_blanks(i, -1, blanks)
                    #DONT i += 1
                else:
                    start, mid, end = text[:i], text[i:e+1], text[e+1:]
                    emoji_len = len(mid)
                    emoji_id = [ord(m) for m in mid if ord(m) > 1000000]
                    mid = [m for m in mid if ord(m) < 1000000]
                    mid = "".join(mid)
                    if len(mid) in [1,2]:
                        if mid == "..":
                            mid = "..."
                    elif len(mid) > 2:
                        try:
                            mid = str(w2n.word_to_num(mid))
                        except:
                            if emoji_id[0] == 1050625 and emoji_id[1] in range(1048833, 1048948):
                                pass
                            elif emoji_id[0] == 1056769 and emoji_id[1] in range(1048966, 1049040):
                                if emoji_id[1] == 1049036:
                                    mid = "13"
                            elif mid in ["oz.","ml."]:
                                pass
                            else:
                                mid = " "
                                blanks.append(i)
                    else:
                        mid = " "
                        blanks.append(i)
                    is_punctuation = True
                    for m in mid:
                        if m not in self.punctuation:
                            is_punctuation = False
                            break
                    if is_punctuation:
                        mid += " "
                    else:
                        mid = " "+mid+" "
                    text = start + mid + end
                    if emoji_len != len(mid):
                        #shift blanks, change lentext, change i
                        d = emoji_len - len(mid)
                        blanks = self.shift_blanks(i, d, blanks)
                        if d < 0:
                            i += 1+d
                        lentext = len(text)
            else:
                i += 1
        return text, blanks

    def normalise_emojis(self, text, blanks):
        #all allowed emojis are a single codepoint
        i = 0
        lentext = len(text)
        while i < lentext:
            o = ord(text[i])
            if o in self.emoji_ords:
                if o in self.allowed_emojis.keys():
                    replace = self.allowed_emojis[o]
                elif text[i-1] != " ":
                    replace = " "
                    blanks.append(i)
                else:
                    replace = ""
                text = text[:i] + replace + text[i+1:]
                if len(replace) != 1:
                    #shift blanks, change lentext, change i
                    d = len(replace) - 1
                    blanks = self.shift_blanks(i, d, blanks)
                    if d < 0:
                        i += 1+d
                    lentext = len(text)
            else:
                i += 1
        return text, blanks

    def normalise_text(self, text):
        #blanks isnt sorted
        blanks = []
        text = "".join(text.split())
        text = text.strip()
        text = self.remove_control_chars(text)
        text= self.normalise_with_forms(text)
        text = self.remove_combining_chars(text)
        text = self.remove_variation_selectors(text)
        text = self.normalise_extra_chars(text)
        text, blanks = self.normalise_LINE_emojis(text, blanks)
        text, blanks = self.normalise_emojis(text, blanks)
        #make all ascii text lowercase
        text = text.lower()
        #remove blanks
        blanks = list(set(blanks))
        blanks.sort(reverse=True)
        for b in blanks:
            text = text[:b] + text[b+1:]
        #turn all whitespace in spaces
        texts = text.split()
        text = " ".join(texts)
        text = text.strip()
        return text
