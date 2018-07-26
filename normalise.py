from skimage.measure import compare_ssim as SSIM #can also have mse, nrmse, and psnr
from PIL import Image, ImageFont, ImageDraw
from fontTools.ttLib import TTFont
from word2number import w2n
import numpy as np
import os, unicodedata, itertools, uuid

class Normalise:

    def __init__(self, font_dir=None, px_width=40, debug=False):
        """
        ALL FONTS MUST BE MONOSPACE UNICODE FONTS AND MUST SUPPORT U+0020 (space)
        I don't check to make sure fonts monospace
        Sans Serif fonts work a LOT better
        Don't include any Emoji only fonts as these will never be used
        Right now, only TrueType fonts are supported
        """
        assert (type(font_dir) == str), "font_dir must be a path string."
        assert (type(px_width) == int), "Width must be an integer."
        assert (px_width > 4), "Width cannot be less than 5px."
        assert (px_width <= 100), "Width cannot be greater than 100px."
        assert (type(debug) == bool), "Debug must be True or False."

        self.debug = debug
        self.width, self.height = px_width, 0 #in pixels
        allowed_font_types = (".ttf")
        if font_dir.endswith("/"):
            font_dir = font_dir[:-1]
        fonts = os.listdir(font_dir)
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
        total_font_points = set(itertools.chain.from_iterable(self.font_points.values()))
        print("%s unique unicode character points supported." % total_font_points)

        #db stuff
        self.known_normalisations = {} #IMPORTANT k:v --> ord:str NOT ord:ord (but it IS stored in db as ord:ord)
        self.known_removal = set([])
        self.load_db()
        
        #character ranges and ints from json
        self.generate_char_info()

    def get_ttf_info(self, font_path):
        f = TTFont(font_path)
        #check to make sure it's a unicode font
        cmap_tables = [cmap.cmap for cmap in f['cmap'].tables if cmap.isUnicode()]
        assert (len(cmap_tables) != 0), "%s is not a unicode font and cannot be used here." % font_path
        combined_cmap = {k:v for ct in cmap_tables for k,v in ct.items()}
        uni_decimals = list(combined_cmap.keys())
        #could use (font.getBestCmap().keys()) instead?
        #slow method for size - i'll figure out fast method later
        size = 0
        i = 0
        try:
            while size == 0:
                f = ImageFont.truetype(font_path, i)
                w,h = f.getsize(" ")
                if w == self.width:
                    size = i
                i += 1
        except Exception as e:
            raise Exception("Font does not support space character (font path: %s)." % font_path)
        print("Font %s contributed %s characters" % (font_path, len(uni_decimals)))
        return uni_decimals, size

    def load_db(self):
        #do something later
        pass

    def generate_char_info(self):
        #ascii characters
        alphanumerical = set(list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"))
        punctuation = set(list("!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"))
        punctuation.add(" ")
        extra = {"ß": "ss", "æ": "ae", "Æ": "AE"}
        self.allowed_chars = alphanumerical | punctuation | set(extra.keys())

        #known
        extra = {ord(k):v for k,v in extra.items()}
        self.known_normalisations.update(extra)

        #emoji characters - unicode v11.0
        emoji_ranges = [(8596, 8601), (8617, 8618), (8986, 8987), (9193, 9203), (9208, 9210), (9642, 9643), (9723, 9726), (9728, 9732), (9748, 9749), (9762, 9763), (9774, 9775), (9784, 9786), (9800, 9811), (9823, 9824), (9829, 9830), (9854, 9855), (9874, 9879), (9883, 9884), (9888, 9889), (9898, 9899), (9904, 9905), (9917, 9918), (9924, 9925), (9934, 9935), (9939, 9940), (9961, 9962), (9968, 9973), (9975, 9978), (9992, 9997), (10035, 10036), (10067, 10069), (10083, 10084), (10133, 10135), (10548, 10549), (11013, 11015), (11035, 11036), (127344, 127345), (127358, 127359), (127377, 127386), (127462, 127487), (127489, 127490), (127538, 127546), (127568, 127569), (127744, 127777), (127780, 127891), (127894, 127895), (127897, 127899), (127902, 127984), (127987, 127989), (127991, 127994), (127999, 128253), (128255, 128317), (128329, 128334), (128336, 128359), (128367, 128368), (128371, 128378), (128394, 128397), (128405, 128406), (128420, 128421), (128433, 128434), (128450, 128452), (128465, 128467), (128476, 128478), (128506, 128591), (128640, 128709), (128715, 128722), (128736, 128741), (128747, 128748), (128755, 128761), (129296, 129338), (129340, 129342), (129344, 129349), (129351, 129392), (129395, 129398), (129404, 129442), (129456, 129465), (129472, 129474), (129488, 129535), (917602, 917603), (917619, 917620)]
        emoji_ords = [169, 174, 8205, 8252, 8265, 8419, 8482, 8505, 9000, 9167, 9410, 9654, 9664, 9742, 9745, 9752, 9757, 9760, 9766, 9770, 9792, 9794, 9827, 9832, 9851, 9881, 9928, 9937, 9981, 9986, 9989, 9999, 10002, 10004, 10006, 10013, 10017, 10024, 10052, 10055, 10060, 10062, 10071, 10145, 10160, 10175, 11088, 11093, 12336, 12349, 12951, 12953, 65039, 126980, 127183, 127374, 127514, 127535, 128391, 128400, 128424, 128444, 128481, 128483, 128488, 128495, 128499, 128745, 128752, 129402, 917605, 917607, 917612, 917614, 917623, 917631]
        for er in emoji_ranges:
            emoji_ords += list(range(er[0], er[1]+1)) 
        self.emoji_ords = set(emoji_ords)
        self.allowed_emojis = {10134: '-', 127374: 'ab', 127377: 'cl', 127378: 'cool', 127379: 'free', 127380: 'id', 127381: 'new', 10006: 'x', 127383: 'ok', 127384: 'sos', 127385: 'up', 127386: 'vs', 128283: 'on', 128281: 'back', 128285: 'top', 128176: '$', 8482: 'tm', 127382: 'ng', 169: 'c', 174: 'r', 128175: '100', 12336: '~', 127921: '8', 128178: '$', 129353: '3', 8505: 'i', 128282: 'end', 8252: '!!', 128702: 'wc', 9410: 'm', 127920: '777', 129351: '1', 129352: '2', 8265: '!?', 10060: 'x', 10062: 'x', 10067: '?', 10068: '?', 10069: '!', 11093: 'o', 10071: '!', 127975: 'atm', 127344: 'a', 127345: 'b', 128284: 'soon', 127359: 'p', 127358: 'o', 10133: '+'}

        #other extra - unicode v11.0
        self.allowed_control_chars = {65532: '', 65533: '?'}
        self.whitespace_extra = set([6158, 8203, 8204, 8205, 8288, 65279])
        self.private_use_chars = set(range(57344, 63744))

        #make numpy arrrays of images of allowed_chars
        self.char_arrays = {}
        self.gen_arrays()
        print("Generated template arrays.")

    def gen_arrays(self):
        #draw chars and conver to numpy arrays
        for char in self.allowed_chars:
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
            str_draw.text((0,0), tu[1], 0, font=self.font_objects[tu[0]])
        #debug
        if self.debug:
            w,h = str_blank.size
            x_coords = [0]
            while x_coords[-1]+self.width < w:
                x_coords.append(x_coords[-1]+self.width)
            for x in x_coords:
                str_draw.line([(x,0), (x,h)])
            filename = str(uuid.uuid4())+".png"
            str_blank.save(filename, format="PNG")
            print("Text image saved as: %s" % filename)
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

    def remove_control_chars(self, text):
        """
        Removes control, format, and modifier characters
        Not including modifier letters or allowed control characters
        """
        set_text = set(text)
        #Im assuming acc.keys() will in general be shorter than set_text
        for acck in self.allowed_control_chars.keys():
            if acck in set_text:
                text = text.replace(acck, self.allowed_control_chars[acck])
        to_remove = []
        for i in range(len(text)):
            if unicodedata.category(text[i]) in ['Cc','Cf','Sk']:
                to_remove.append(i)
        to_remove.reverse()
        for tr in to_remove:
            text = text[:i] + text[i+1:]
        if self.debug:
            print("Control chars: %s" % text)
        return text

    def remove_illegal_chars(self, text):
        """
        Removes surrogate and unassigned characters
        I realise that this function can be combined with the function above
        I have left it like this for readability
        """
        to_remove = []
        for i in range(len(text)):
            if unicodedata.category(text[i]) in ['Cs','Cn'] or ord(text[i]) in self.private_use_chars:
                if ord(text[i]) not in [1114110, 1114111]: #used for LINE emojis
                    to_remove.append(i)
        to_remove.reverse()
        for tr in to_remove:
            text = text[:i] + text[i+1:]
        if self.debug:
            print("Illegal chars: %s" % text)
        return text

    def remove_combining_chars(self, text):
        """
        Removes marks
        Really should be named remove_marks, but this is what i originally named it
        """
        i = 0
        lentext = len(text)
        while i < lentext:
            ss = text[i] #substring
            if unicodedata.category(ss)[0] == 'M':
                text = text[:i] + text[i+1:]
            else:
                nfkd_list = list(unicodedata.normalize("NFKD",ss)) #compatibility
                ss_list = []
                for n in nfkd_list:
                    nfd = list(unicodedata.normalize("NFD",n)) #canonical equivalence
                    if unicodedata.category(n)[0] != 'P':
                        for nfd_char in nfd:
                            if unicodedata.category(nfd_char)[0] == 'P':
                                nfd.remove(nfd_char)
                    ss_list += nfd
                for s in ss_list:
                    if unicodedata.category(s) == 'M':
                        ss_list.remove(s)
                new_ss = "".join(ss_list)
                text = text[:i] + new_ss + text[i+1:]
                i += len(new_ss)
            lentext = len(text)
        if self.debug:
            print("Combining chars: %s" % text)
        return text

    def normalise_emojis(self, text, replacement=" ", remove=True):
        """
        Converts allowed emojis
        Removes all other emojis
        """
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
        if self.debug:
            print("Emojis: %s" % text)
        return text

    def normalise_LINE_emojis(self, text, replacement=" ", remove=1):
        """
        remove == 0:
            turns LINE emojis into normal characters
            or ignores them
        remove == 1:
            turns LINE emojis into normal characters
            or replaces them with replacement string
        remove == 2:
            replaces all LINE emojis with replacement string
        """
        i = 0
        lentext = len(text)
        while i < lentext:
            if ord(text[i]) > 983040: #supplementary private use unicode points
                e = text.find(chr(1114111), i)
                if e in [-1, i]:
                    text = text[:i] + text[i+1:]
                else:
                    start, mid, end = text[:i], text[i:e+1], text[e+1:]
                    emoji_ids = [m for m in mid if ord(m) >= 983040]
                    mid = [m for m in mid if ord(m) < 983040]
                    mid = "".join(mid)
                    if remove == 2:
                        text = start + replacement + end
                        i += len(replacement)
                    elif len(mid) > 2:
                        try:
                            mid = w2n.word_to_num(mid)
                            text = start + mid +end
                        except:
                            if emoji_ids[0] == 1050625 and emoji_ids[1] in range(1048833, 1048948):
                                text = start + mid + end
                            elif emoji_ids[0] == 1056769 and emoji_ids[1] in range(1048966, 1049040):
                                if emoji_ids[1] == 1049036:
                                    mid = "13"
                                text = start + mid + end
                            #not sure why i have this next elif but id just leave it
                            elif mid in ['oz.','ml.']:
                                text = start + mid + end
                            elif remove == 1:
                                mid = replacement
                                text = start + replacement + end
                            else:
                                mid += "".join(emoji_ids)
                        i += len(mid)
                    elif remove == 1:
                        text = start + replacement + end
                        i += len(replacement)
                lentext = len(text)
        if self.debug:
            print("LINE emojis: %s" % text)
        return text

    def normalise_whitespace(self, text):
        """
        Removes whitespace extra characters (not true whitespace)
        Converts all other whitespace characters into spaces (0x20)
        """
        to_remove = []
        for i in range(len(text)):
            if ord(text[i]) in self.whitespace_extra:
                to_remove.append(i)
        to_remove.reverse()
        for tr in to_remove:
            text = text[:i] + text[i+1:]
        for char in text:
            #Zl, Zp, and Zs categories (Cc whitespace chars get removed as control chars)
            if unicodedata.category(char)[0] == 'Z':
                text = text.replace(char, ' ') #space chr(32) 0x20
        if self.debug:
            print("Whitespace: %s" % text)
        return text

    def normalise_known(self, text):
        """
        Converts extra keys to extra values
        Should probably be merged with normalise_known at some point
        """
        set_text = set(text)
        to_remove = []
        #Im assuming kn.keys() will in general be longer than set_text
        for st in set_text:
            if ord(st) in self.known_normalisations.keys():
                text = text.replace(st, self.known_normalisations[ord(st)])
        #Im assuming self.kr will in general be longer than set_text
        for i in range(len(text)):
            if ord(text[i]) in self.known_removal:
                to_remove.append(i)
        to_remove.reverse()
        for tr in to_remove:
            text = text[:i] + text[i+1:]
        if self.debug:
            print("Known: %s" % text)
        return text

    def update_known(self, known_dict, known_set):
        self.known_normalisations.update(known_dict)
        self.known_removal |= known_set
        #maybe add some stuff to save it to database too

    def normalise(self, text):
        text = self.remove_illegal_chars(text)
        text = self.normalise_whitespace(text)
        #whitespace first because control removes some whitespace chars
        text = self.remove_combining_chars(text)
        text = self.remove_control_chars(text)
        text = self.normalise_LINE_emojis(text)
        text = self.normalise_emojis(text)
        text = self.normalise_known(text)

        #get rid of multiple spaces
        texts = text.split()
        text = " ".join(texts)

        #normalise using imaging methods
        unknown_chars = {} # uc[ord] = index
        for i in range(len(text)):
            if text[i] not in self.allowed_chars:
                unknown_chars[ord(text[i])] = i
        if unknown_chars != {}:
            #could just not draw whole text string, but not sure if i wanna split it in weird spots
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
        if self.debug:
            print("Imaging: %s" % text)

        #get rid of multiple spaces
        texts = text.split()
        text = " ".join(texts)
        return text
