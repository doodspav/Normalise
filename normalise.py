from skimage.measure import compare_ssim as SSIM
from PIL import Image, ImageFont, ImageDraw
from fontTools.ttLib import TTFont
from word2number import w2n
import numpy as np
import os

class Normalise:

    def __init__(self, font_dir=None, px_width=40):
        """
        ALL FONTS MUST BE MONOSPACE FONTS AND MUST SUPPORT U+0020 (space)
        Don't include any Emoji only fonts as these will never be used
        Right now, only TrueType fonts are supported
        """
        assert (px_width > 4), "Width cannot be less than 5px."
        assert (px_width <= 100), "Width cannot be greater than 100px."
        assert(type(px_width) == int), "Width must be an integer."
        self.width, self.height = px_width, 0 #in pixels
        allowed_font_types = (".ttf")
        if font_dir.endswith("/"):
            font_dir = font_dir[:-1]
        fonts = os.listdir(font_dirt)
        self.font_names = [f for f in fonts if f.endswith(allowed_font_types)]
        self.font_objects = {}
        self.font_points = {}
        for fn in self.font_names:
            path = font_dir+"/"+fn
            unicode_points, size = self.get_ttf_info(path)
            font_obj = ImageFont.truetype(path, size)
            self.font_objects[fn] = font_obj
            self.font_points[fn] = unicode_points
            w,h = font_obj.getsize(" ")
            if w != self.width:
                raise Exception("Width of chr(32) (%s) != self.width (%s)." % (w, self.width))
            if h > self.height:
                self.height = h
        print("Loaded %s font files." % len(self.font_names))

        #db stuff
        self.known_normalisations = {}
        self.known_removal = set([])
        self.load_db()
        #character ranges and ints from json
        self.generate_char_info()

    def get_ttf_info(self, font_path):
        f = TTFont(font_path)
        uni_decimals = list([cmap.cmap for cmap in f['cmap'].tables][0].keys())
        uni_decimals.sort()
        #could use (font.getBestCmap().keys()) instead?
        #slow method for size - i'll figure out fast method later
        size = 0
        i = 0
        try:
            while size == 0:
                f = ImageFont.truetype(font_path, i)
                w,h = f.getsize(" ")
                if w == self.width:
                    size == i
                i += 1
        except Exception as e:
            raise Exception("Font does not support space character (font path: %s)." % font_path)
        return uni_decimals, size

    def load_db(self):
        #do something later
        pass

    def generate_char_info(self):
        #ascii characters
        self.alphanumerical = set(list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"))
        self.punctuation = set(list("!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"))
        self.extra = {"ß": "ss", "æ": "ae", "Æ": "AE"}
        self.allowed_chars = self.alphanumerical | self.punctuation | set(self.extra.keys())

        #emoji characters - unicode v11.0
        emoji_ranges = [(8596, 8601), (8617, 8618), (8986, 8987), (9193, 9203), (9208, 9210), (9642, 9643), (9723, 9726), (9728, 9732), (9748, 9749), (9762, 9763), (9774, 9775), (9784, 9786), (9800, 9811), (9823, 9824), (9829, 9830), (9854, 9855), (9874, 9879), (9883, 9884), (9888, 9889), (9898, 9899), (9904, 9905), (9917, 9918), (9924, 9925), (9934, 9935), (9939, 9940), (9961, 9962), (9968, 9973), (9975, 9978), (9992, 9997), (10035, 10036), (10067, 10069), (10083, 10084), (10133, 10135), (10548, 10549), (11013, 11015), (11035, 11036), (127344, 127345), (127358, 127359), (127377, 127386), (127462, 127487), (127489, 127490), (127538, 127546), (127568, 127569), (127744, 127777), (127780, 127891), (127894, 127895), (127897, 127899), (127902, 127984), (127987, 127989), (127991, 127994), (127999, 128253), (128255, 128317), (128329, 128334), (128336, 128359), (128367, 128368), (128371, 128378), (128394, 128397), (128405, 128406), (128420, 128421), (128433, 128434), (128450, 128452), (128465, 128467), (128476, 128478), (128506, 128591), (128640, 128709), (128715, 128722), (128736, 128741), (128747, 128748), (128755, 128761), (129296, 129338), (129340, 129342), (129344, 129349), (129351, 129392), (129395, 129398), (129404, 129442), (129456, 129465), (129472, 129474), (129488, 129535), (917602, 917603), (917619, 917620)]
        emoji_ords = [169, 174, 8205, 8252, 8265, 8419, 8482, 8505, 9000, 9167, 9410, 9654, 9664, 9742, 9745, 9752, 9757, 9760, 9766, 9770, 9792, 9794, 9827, 9832, 9851, 9881, 9928, 9937, 9981, 9986, 9989, 9999, 10002, 10004, 10006, 10013, 10017, 10024, 10052, 10055, 10060, 10062, 10071, 10145, 10160, 10175, 11088, 11093, 12336, 12349, 12951, 12953, 65039, 126980, 127183, 127374, 127514, 127535, 128391, 128400, 128424, 128444, 128481, 128483, 128488, 128495, 128499, 128745, 128752, 129402, 917605, 917607, 917612, 917614, 917623, 917631]
        for er in emoji_ranges:
            emoji_ords += list(range(emr[0], emr[1]+1)) 
        self.emoji_ords = set(emoji_ords)
        self.allowed_emojis = {10134: '-', 127374: 'ab', 127377: 'cl', 127378: 'cool', 127379: 'free', 127380: 'id', 127381: 'new', 10006: 'x', 127383: 'ok', 127384: 'sos', 127385: 'up', 127386: 'vs', 128283: 'on', 128281: 'back', 128285: 'top', 128176: '$', 8482: 'tm', 127382: 'ng', 169: 'c', 174: 'r', 128175: '100', 12336: '~', 127921: '8', 128178: '$', 129353: '3', 8505: 'i', 128282: 'end', 8252: '!!', 128702: 'wc', 9410: 'm', 127920: '777', 129351: '1', 129352: '2', 8265: '!?', 10060: 'x', 10062: 'x', 10067: '?', 10068: '?', 10069: '!', 11093: 'o', 10071: '!', 127975: 'atm', 127344: 'a', 127345: 'b', 128284: 'soon', 127359: 'p', 127358: 'o', 10133: '+'}

        #combining characters
        combining_ranges = [(768, 879), (1155, 1161), (1425, 1469), (1473, 1474), (1476, 1477), (1552, 1562), (1611, 1631), (1750, 1756), (1759, 1764), (1767, 1768), (1770, 1773), (1840, 1866), (2027, 2035), (2070, 2073), (2075, 2083), (2085, 2087), (2089, 2093), (2137, 2139), (2260, 2273), (2275, 2304), (2362, 2364), (2380, 2383), (2385, 2389), (2402, 2403), (2503, 2504), (2507, 2509), (2631, 2632), (2635, 2637), (2672, 2673), (2763, 2765), (2786, 2787), (2878, 2879), (2887, 2888), (2891, 2893), (2902, 2903), (2914, 2915), (3006, 3008), (3018, 3019), (3139, 3140), (3148, 3149), (3157, 3158), (3170, 3171), (3270, 3271), (3276, 3277), (3387, 3388), (3398, 3399), (3404, 3406), (3535, 3536), (3570, 3571), (3640, 3642), (3656, 3659), (3768, 3769), (3784, 3787), (3864, 3865), (3953, 3954), (3962, 3965), (3970, 3972), (3974, 3975), (4150, 4151), (4153, 4155), (4157, 4158), (4184, 4185), (4236, 4237), (4957, 4959), (6068, 6069), (6277, 6278), (6457, 6459), (6679, 6680), (6773, 6780), (6832, 6845), (7019, 7027), (7082, 7083), (7154, 7155), (7376, 7378), (7380, 7392), (7394, 7400), (7411, 7412), (7416, 7417), (7616, 7673), (7675, 7679), (8400, 8412), (8421, 8432), (11503, 11505), (11744, 11775), (12330, 12335), (12441, 12442), (42612, 42621), (42654, 42655), (42736, 42737), (43232, 43249), (43307, 43309), (43443, 43444), (43698, 43700), (43703, 43704), (43710, 43711), (44004, 44005), (44012, 44013), (65056, 65071), (66422, 66426), (68152, 68154), (68325, 68326), (69817, 69818), (69888, 69890), (69939, 69940), (70197, 70198), (70377, 70378), (70502, 70508), (70512, 70516), (70850, 70851), (71103, 71104), (71350, 71351), (73028, 73029), (92912, 92916), (92976, 92982), (119141, 119145), (119149, 119154), (119163, 119170), (119173, 119179), (119210, 119213), (119362, 119364), (122880, 122886), (122888, 122904), (122907, 122913), (122915, 122916), (122918, 122922), (125136, 125142), (125252, 125258)]
        combining_chars = [1471, 1479, 1648, 1809, 2307, 2366, 2391, 2433, 2435, 2492, 2494, 2500, 2519, 2530, 2561, 2563, 2620, 2622, 2626, 2641, 2677, 2689, 2691, 2748, 2750, 2757, 2759, 2761, 2817, 2819, 2876, 2881, 2884, 2946, 3010, 3021, 3031, 3072, 3075, 3135, 3137, 3142, 3144, 3146, 3201, 3203, 3260, 3265, 3268, 3274, 3285, 3329, 3331, 3390, 3392, 3396, 3402, 3415, 3458, 3530, 3538, 3540, 3542, 3544, 3551, 3893, 3895, 3897, 3956, 3968, 4038, 4141, 4190, 4192, 4195, 4209, 4212, 4226, 4228, 4230, 4234, 4252, 5908, 5940, 6098, 6109, 6155, 6157, 6313, 6752, 6783, 6964, 6980, 7142, 7223, 7405, 8417, 9676, 11647, 42607, 43014, 43204, 43347, 43392, 43394, 43447, 43450, 43452, 43456, 43493, 43644, 43696, 43713, 43766, 44007, 44010, 64286, 65024, 65026, 65028, 65039, 66045, 66272, 68109, 68111, 68159, 69702, 69759, 70003, 70080, 70090, 70460, 70477, 70722, 70726, 71231, 71467, 72244, 72263, 72345, 72767, 73026, 113822]
        for cr in combining_ranges:
            combining_chars += list(range(emr[0], emr[1]+1))
        self.combining_chars = set(combining_chars)

        #variation selectors
        vs_ranges = [(65024, 65039), (917760, 917999)]
        variation_selectors = []
        for vs in vs_ranges:
            variation_selectors += list(range(vs[0], vs[1]+1))
        self.variation_selectors = set(variation_selectors)

        #whitespace characters (includes seperators)
        ws_ranges = [(9, 13), (8192, 8202), (8232, 8233)]
        self.whitespace = [133, 160, 5760, 8239, 8287, 12288] #keep as list
        for ws in ws_ranges:
            self.whitespace += list(range(ws[0], ws[1]+1))
        self.whitespace_extra = set([6158, 8203, 8204, 8205, 8288, 65279])

        #control characters (plus specials, seperators...)
        self.allowed_control_chars = {}
        self.control_chars = self.build_control_chars() #set

        #make arrays of images of allowed chars
        self.char_arrays = {65533: '?'}
        self.gen_arrays()
        print("Generated template arrays.")

    def build_control_chars(self, keep_whitespace=True, keep_whitespace_extra=True):
        control_0 = list(range(32)) #not including 32 (space)
        control_1 = list(range(127, 160))
        language_tags = list(rane(917505, 917631))
        bidirectional_text = [1564, 8206, 8207, 8234, 8235, 8236, 8237, 8238, 8294, 8295, 8296, 8297]
        specials = list(range(65520, 65536)) #includes interlinear notation
        total = control_0+control_1+language_tags+bidirectional_text+specials
        #whitespace stuff
        if keep_whitespace:
            for w in self.whitespace:
                if w in total:
                    total.remove(w)
        if keep_whitespace_extra:
            for w in self.whitespace_extra:
                if w in total:
                    total.remove(w)
        #allowed control chars
        for acc in self.allowed_control_chars.keys():
            if acc in total:
                total.remove(acc)
        total = set(total)
        return total

    def gen_arrays(self):
        #draw chars and conver to numpy arrays
        for i in range(len(self.allowed_chars)):
            char = self.allowed_chars[i]
            img = self.draw_string(char)
            arr = np.array(img)
            self.char_arrays[char] = arr

    def draw_string(self, string, unknown_char=" "):
        #unknown_char is what is drawn if none of the fonts support the character
        ords_set = set([ord(s) for s in string])
        to_use = []
        fonts = [(f, self.font_points[f]) for f in self.font_names]
        #split characters in strings between fonts
        while len(ords_set) != 0:
            fonts.sort(key=self.sort_key(ords_set))
            font = fonts[0]
            shared_chars = ords_set.intersection(font[1])
            if len(shared_chars) == 0:
                fonts.sort(key=self.sort_key(set([unknown_char])))
                font = fonts[0]
                shared_chars = ords_set.intersection(font[1])
                if len(shared_chars) == 0 or (len(unknown_char.split()) == 0 and len(unknown_char) != 0): #eg whitespace
                    ords_set.clear()
                    break
                else:
                    ords_set.clear()
                    temp_str = "".join([unknown_char if ord(s) in shared_chars else " " for s in string])
                    to_use.append((font[0], temp_str))
            else:
                shared_chars = ords_set.intersection(font[1])
                ords_set -= shared_chars
                temp_str = "".join([s if ord(s) in shared_chars else " " for s in string])
                to_use.append((font[0], temp_str))
        #create canvas
        str_width = self.width * len(string)
        str_blank = Image.new("L", (str_width, self.height), color=255)
        str_draw = ImageDraw.Draw(str_blank)
        #draw on canvas
        for tu in to_use:
            draw.text((0,0), tu[1], 0, font=self.font_objects[tu[0]])
        return str_blank

    def sort_key(self, ord_set):
        def key(tup):
            return (len(ord_set.intersection(tup[1])), len(tup[1]))
        return key

    def compare_char_array(self, array):
        """
        Arrays MUST HAVE THE SAME DIMENSIONS or this will not work
        """
        results = []
        for c in self.char_arrays.keys():
            c_arr = self.char_arrays[c]
            s = SSIM(array, c_arr)
            results.append((c, s))
        results.sort(key=lambda x: x[1])
        return results[0][0]

    def remove_control_chars(self, text, remove_vs=0):
        """
        remove_vs == 0: only remove control chars
        remove_vs == 1: remove control chars + vs
        remove_vs == 2: only remove vs
        """
        assert (remove_vs in [0,1,2]), "Remove_vs kwarg must be 0, 1, or 2."
        for acc in self.allowed_control_chars.keys():
            text = text.replace(chr(acc), self.allowed_control_chars[acc])
        to_remove = []
        #choose set to remove
        if remove_vs == 0:
            chars_to_remove = self.control_chars
        elif remove_vs == 1:
            chars_to_remove = self.control_chars | self.variation_selectors
        elif remove_vs == 2:
            chars_to_remove = self.variation_selectors
        #remove characters
        for i in range(len(text)):
            if ord(text[i]) in chars_to_remove:
                to_remove.append(i)
        to_remove.reverse()
        for tr in to_remove:
            text = text[:tr] + text[tr+1:]
        return text

    def remove_combining_chars(self, text):
        i = 0
        lentext = len(text)
        while i < lentext:
            ss = text[i] #substring
            if ss in self.combining_chars:
                text = text[:i] + text[i+1:]
            else:
                nfkd_list = list(unicodedata.normalize("NFKD",ss)) #compatibility
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
                i += len(new_ss)
            lentext = len(text)
        return text

    def normalise_extra(self, text):
        i = 0
        lentext = len(text)
        while i < lentext:
            if text[i] in self.extra.keys():
                text = text[:i] + self.extra[text[i]] + text[i+1]
                i += len(self.extra[text[i]])-1
            lentext = len(text)
            i += 1
        return text

    def normalise_LINE_emojis(self, text, replacement=" "):
        #turn LINE emojis into normal characters, or replace with replacement string
        assert (len(replacement) != 0), "Replacement cannot be empty."
        i = 0
        lentext = len(text)
        while i < lentext:
            if ord(text[i]) > 1000000: #private use unicode points
                e = text.find(chr(1114111), i)
                if e == -1:
                    text = text[:i] + text[i+1:]
                else:
                    start, mid, end = text[:i], text[i:e+1], text[e+1:]
                    emoji_ids = [m for m in mid if ord(m) > 1000000]
                    mid = [m for m in mid if ord(m) < 1000000]
                    mid = "".join(mid)
                    if mid == "..":
                        mid = "..."
                        text = start + mid + end
                    elif len(mid) > 2:
                        try:
                            mid = w2n.word_to_num(mid)
                        except:
                            if emoji_ids[0] == 1050625 and emoji_ids[1] in range(1048833, 1048948):
                                text = start + mid + end
                            elif emoji_ids[0] == 1056769 and emoji_ids[1] in range(1048966, 1049040):
                                if emoji_ids[1] == 1049036:
                                    mid = "13"
                                text = start + mid + end
                            elif mid in ["oz.","ml."]:
                                text = start + mid + end
                            else:
                                text = start + replacement + end
                    else:
                        text = start + replacement + end
                lentext = len(text)
            i += 1
        return text

    def normalise_emojis(self, text, replacement=" ", remove=True):
        assert (len(replacement) != 0), "Replacement cannot be empty."
        i = 0
        lentext = len(text)
        while i < lentext:
            o = ord(text[i])
            if o in self.emoji_ords:
                if o in self.allowed_emojis.keys():
                    text = text[:i] + self.allowed_emojis[o] + text[i+1:]
                    i += len(self.allowed_emojis[o])
                elif remove == True:
                    text = text[:i] + replacement + text[i+1:]
                    i += len(replacement)
                lentext = len(text)
            else:
                i += 1
        return text

    def normalise_whitespace(self, text):
        to_remove = []
        for i in range(len(text)):
            if ord(text[i]) in self.whitespace_extra:
                to_remove.append(i)
        to_remove.reverse()
        for tr in to_remove:
            text = text[:i] + text[i+1]
        for w in self.whitespace:
            text = text.replace(w, " ")
        return text

    def normalise_known(self, text):
        to_remove = []
        for i in range(len(text)):
            if ord(text[i]) in self.known_normalisations.keys():
                text = text[:i] + self.known_normalisations[ord(text[i])] + text[i+1:]
            elif ord(text[i]) in self.known_removal:
                to_remove.append(i)
        to_remove.reverse()
        for tr in to_remove:
            text = text[:i] + text[i+1:]
        return text

    def update_known(self, known_dict, known_set):
        self.known_removal |= known_set
        self.known_normalisations.update(known_dict)
        #maybe add some stuff to save it to database too

    def normalise(self, text):
        #removes variation selectors and 0 width whitespace characters cuz im lazy
        #normalises as much as possible without using imaging methods
        text = self.remove_control_chars(text, remove_vs=1)
        text = self.remove_combining_chars(text)
        text = self.normalise_extra(text)
        text = self.normalise_LINE_emojis(text)
        text = self.normalise_emojis(text)
        text = self.normalise_whitespace(text)
        text = self.normalise_known(text)
        #normalises using imaging methods
        unknown_chars = {} # uc[ord] = index
        for i in range(len(text)):
            if ord(text[i]) not in self.allowed_chars:
                unknown_chars[ord(text[i])] = i
        if unknown_chars != {}:
            text_image = self.draw_string(text)
            unknown_char_arrays = {}
            for uc_ord in unknown_chars.keys():
                uc_i = unknown_chars[uc_ord]
                coordinates = (uc_i*self.width, 0, (uc_i+1)*self.width, self.height) #LURD
                sub_img = text_image.crop(box=coordinates)
                sub_arr = np.array(sub_img)
                unknown_char_arrays[uc_ord] = sub_arr
            known_removal = []
            for uc_ord in unknown_char_arrays.keys():
                char = self.compare_char_array(unknown_char_arrays[uc_ord])
                if char == "":
                    known_removal.append(uc_ord)
                    del unknown_char_arrays[uc_ord]
                else:
                    unknown_char_arrays[uc_ord] = char
            self.update_known(unknown_char_arrays, set(known_removal))
            text = self.normalise_known(text)
        return text
