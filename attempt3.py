from skimage.measure import compare_ssim as SSIM
from PIL import Image, ImageFont, ImageDraw
from fontTools.ttLib import TTFont
from word2number import w2n
import numpy as np
import unicodedata, random, os, tempfile, shutil, MySQLdb

class Normalise:

    def __init__(self, font_dir=None, create=False, db="Font"):
        """
        ALLL FONTS MUST BE MONOSPACE FONTS AND MUST SUPPORT U+0020 (space)
        Don't include any Emoji only fonts as these will never be used
        Also right now, only TrueType fonts are supported
        """
        #load fonts
        allowed_font_types = (".ttf")
        self.width = 40 #in pixels
        self.height = 0
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
            w,h = font_obj.getsize(chr(unicode_points[0]))
            if w != self.width:
                raise Exception("Width of 'a' (%s) != self.width (%s)." % (w, self.width))
            if h > self.height:
                self.height = h
        print("Loaded %s font files." % len(self.font_names))

        #define white for all bands
        self.white = {"RGB":   (255,255,255),
                      "RGBA":  (255,255,255,255),
                      "CMYK":  (0,0,0,0),
                      "LAB":   (255,128,127),
                      "L":     (255),
                      "1":     (1)}

        #db stuff
        self.load_db(db, create)

        #ascii characters
        self.alphanumerical = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
        self.punctuation = list("!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~")
        self.extra = {"ß": "ss", "æ": "ae", "Æ": "AE"}
        self.allowed_chars = self.alphanumerical + self.punctuation + self.extra.keys()

        #emoji characters - unicode v11.0
        emoji_ranges = [(8596, 8601), (8617, 8618), (8986, 8987), (9193, 9203), (9208, 9210), (9642, 9643), (9723, 9726), (9728, 9732), (9748, 9749), (9762, 9763), (9774, 9775), (9784, 9786), (9800, 9811), (9823, 9824), (9829, 9830), (9854, 9855), (9874, 9879), (9883, 9884), (9888, 9889), (9898, 9899), (9904, 9905), (9917, 9918), (9924, 9925), (9934, 9935), (9939, 9940), (9961, 9962), (9968, 9973), (9975, 9978), (9992, 9997), (10035, 10036), (10067, 10069), (10083, 10084), (10133, 10135), (10548, 10549), (11013, 11015), (11035, 11036), (127344, 127345), (127358, 127359), (127377, 127386), (127462, 127487), (127489, 127490), (127538, 127546), (127568, 127569), (127744, 127777), (127780, 127891), (127894, 127895), (127897, 127899), (127902, 127984), (127987, 127989), (127991, 127994), (127999, 128253), (128255, 128317), (128329, 128334), (128336, 128359), (128367, 128368), (128371, 128378), (128394, 128397), (128405, 128406), (128420, 128421), (128433, 128434), (128450, 128452), (128465, 128467), (128476, 128478), (128506, 128591), (128640, 128709), (128715, 128722), (128736, 128741), (128747, 128748), (128755, 128761), (129296, 129338), (129340, 129342), (129344, 129349), (129351, 129392), (129395, 129398), (129404, 129442), (129456, 129465), (129472, 129474), (129488, 129535), (917602, 917603), (917619, 917620)]
        emoji_ints = [169, 174, 8205, 8252, 8265, 8419, 8482, 8505, 9000, 9167, 9410, 9654, 9664, 9742, 9745, 9752, 9757, 9760, 9766, 9770, 9792, 9794, 9827, 9832, 9851, 9881, 9928, 9937, 9981, 9986, 9989, 9999, 10002, 10004, 10006, 10013, 10017, 10024, 10052, 10055, 10060, 10062, 10071, 10145, 10160, 10175, 11088, 11093, 12336, 12349, 12951, 12953, 65039, 126980, 127183, 127374, 127514, 127535, 128391, 128400, 128424, 128444, 128481, 128483, 128488, 128495, 128499, 128745, 128752, 129402, 917605, 917607, 917612, 917614, 917623, 917631]
        self.emoji_ords = emoji_ints
        for emr in emoji_ranges:
            self.emoji_ords += list(range(emr[0], emr[1]+1))
        self.allowed_emojis = {10134: '-', 127374: 'ab', 127377: 'cl', 127378: 'cool', 127379: 'free', 127380: 'id', 127381: 'new', 10006: 'x', 127383: 'ok', 127384: 'sos', 127385: 'up', 127386: 'vs', 128283: 'on', 128281: 'back', 128285: 'top', 128176: '$', 8482: 'tm', 127382: 'ng', 169: 'c', 174: 'r', 128175: '100', 12336: '~', 127921: '8', 128178: '$', 129353: '3', 8505: 'i', 128282: 'end', 8252: '!!', 128702: 'wc', 9410: 'm', 127920: '777', 129351: '1', 129352: '2', 8265: '!?', 10060: 'x', 10062: 'x', 10067: '?', 10068: '?', 10069: '!', 11093: 'o', 10071: '!', 127975: 'atm', 127344: 'a', 127345: 'b', 128284: 'soon', 127359: 'p', 127358: 'o', 10133: '+'}

        #control characters (plus extra things like specials, seperators...)
        self.allowed_control_chars = {65533: '?'}
        self.control_chars = self.build_control_chars(keep_whitespace=True)

        #combining characters
        combining_ranges = [(768, 879), (1155, 1161), (1425, 1469), (1473, 1474), (1476, 1477), (1552, 1562), (1611, 1631), (1750, 1756), (1759, 1764), (1767, 1768), (1770, 1773), (1840, 1866), (2027, 2035), (2070, 2073), (2075, 2083), (2085, 2087), (2089, 2093), (2137, 2139), (2260, 2273), (2275, 2304), (2362, 2364), (2380, 2383), (2385, 2389), (2402, 2403), (2503, 2504), (2507, 2509), (2631, 2632), (2635, 2637), (2672, 2673), (2763, 2765), (2786, 2787), (2878, 2879), (2887, 2888), (2891, 2893), (2902, 2903), (2914, 2915), (3006, 3008), (3018, 3019), (3139, 3140), (3148, 3149), (3157, 3158), (3170, 3171), (3270, 3271), (3276, 3277), (3387, 3388), (3398, 3399), (3404, 3406), (3535, 3536), (3570, 3571), (3640, 3642), (3656, 3659), (3768, 3769), (3784, 3787), (3864, 3865), (3953, 3954), (3962, 3965), (3970, 3972), (3974, 3975), (4150, 4151), (4153, 4155), (4157, 4158), (4184, 4185), (4236, 4237), (4957, 4959), (6068, 6069), (6277, 6278), (6457, 6459), (6679, 6680), (6773, 6780), (6832, 6845), (7019, 7027), (7082, 7083), (7154, 7155), (7376, 7378), (7380, 7392), (7394, 7400), (7411, 7412), (7416, 7417), (7616, 7673), (7675, 7679), (8400, 8412), (8421, 8432), (11503, 11505), (11744, 11775), (12330, 12335), (12441, 12442), (42612, 42621), (42654, 42655), (42736, 42737), (43232, 43249), (43307, 43309), (43443, 43444), (43698, 43700), (43703, 43704), (43710, 43711), (44004, 44005), (44012, 44013), (65056, 65071), (66422, 66426), (68152, 68154), (68325, 68326), (69817, 69818), (69888, 69890), (69939, 69940), (70197, 70198), (70377, 70378), (70502, 70508), (70512, 70516), (70850, 70851), (71103, 71104), (71350, 71351), (73028, 73029), (92912, 92916), (92976, 92982), (119141, 119145), (119149, 119154), (119163, 119170), (119173, 119179), (119210, 119213), (119362, 119364), (122880, 122886), (122888, 122904), (122907, 122913), (122915, 122916), (122918, 122922), (125136, 125142), (125252, 125258)]
        combining_ints = [1471, 1479, 1648, 1809, 2307, 2366, 2391, 2433, 2435, 2492, 2494, 2500, 2519, 2530, 2561, 2563, 2620, 2622, 2626, 2641, 2677, 2689, 2691, 2748, 2750, 2757, 2759, 2761, 2817, 2819, 2876, 2881, 2884, 2946, 3010, 3021, 3031, 3072, 3075, 3135, 3137, 3142, 3144, 3146, 3201, 3203, 3260, 3265, 3268, 3274, 3285, 3329, 3331, 3390, 3392, 3396, 3402, 3415, 3458, 3530, 3538, 3540, 3542, 3544, 3551, 3893, 3895, 3897, 3956, 3968, 4038, 4141, 4190, 4192, 4195, 4209, 4212, 4226, 4228, 4230, 4234, 4252, 5908, 5940, 6098, 6109, 6155, 6157, 6313, 6752, 6783, 6964, 6980, 7142, 7223, 7405, 8417, 9676, 11647, 42607, 43014, 43204, 43347, 43392, 43394, 43447, 43450, 43452, 43456, 43493, 43644, 43696, 43713, 43766, 44007, 44010, 64286, 65024, 65026, 65028, 65039, 66045, 66272, 68109, 68111, 68159, 69702, 69759, 70003, 70080, 70090, 70460, 70477, 70722, 70726, 71231, 71467, 72244, 72263, 72345, 72767, 73026, 113822]
        self.combining_chars = combining_ints
        for cr in combining_ranges:
            self.combining_chars += list(range(cr[0], cr[1]+1))

        #variation selectors
        vs_ranges = [(65024, 65039), (917760, 917999)]
        self.variation_selectors = []
        for vs in vs_ranges:
            self.variation_selectors += list(range(vs[0], vs[1]+1))

        #whitespace (includes seperators)
        ws_ranges = [(9, 13), (8192, 8202), (8232, 8233)]
        self.whitespace = [133, 160, 5760, 8239, 8287, 12288]
        for ws in ws_ranges:
            self.whitespace += list(range(ws[0], ws[1]+1))
        self.whitespace_extra = [6158, 8203, 8204, 8205, 8288, 65279]

        #make arrays of images of allowed chars
        self.char_arrays = {}
        self.gen_arrays()
        print("Generated template arrays.")

    def build_control_chars(self, keep_whitespace=True):
        control_0 = list(range(32)) #not including 32 which is space
        control_1 = list(range(127, 160))
        language_tags = list(range(917505, 917631))
        bidirectional_text = [1564, 8206, 8207, 8234, 8235, 8236, 8237, 8238, 8294, 8295, 8296, 8297]
        specials = list(range(65520, 65536)) #includes interlinear notation
        total = control_0+control_1+language_tags+interlinear_notation+bidirectional_text+specials
        if keep_whitespace:
            ws = self.whitespace+self.whitespace_extra
            for w in ws:
                if w in total:
                    total.remove(w)
        return total

    def gen_arrays(self):
        #create a temp directory to store images
        temp_path = tempfile.mkdtemp()
        temp_path += "/"
        #draw characters and convert to numpy arrays
        for i in range(len(self.allowed_chars)):
            char = self.allowed_chars[i]
            img_path = self.draw_string(char, temp_path+str(i)+".png", save=True, mode="RGB")
            img = Image.open(img_path).convert("L") #converts to 8-bit grayscale single channel
            arr = np.array(img)
            self.char_arrays[char] = arr
        #delete directory
        temp_path = temp_path[:-1]
        shutil.rmtree(temp_path)

    def draw_string(self, string, path=None, save=False, unknown_char=" ", mode="RGB"):
        """
        - if save is false, an Image object is returned
        - if save is true, the Image object is saved to the path and the path is returned
        - unknown char is what is drawn if none of the available fonts support the character
        """
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
                    break
            else:
                shared_chars = ords_set.intersection(font[1])
                ords_set -= shared_chars
                temp_str = "".join([s if ord(s) in shared_chars else " " for s in string])
                to_use.append((font[0], temp_str))
        #create canvas
        str_width = self.width * len(string)
        str_blank = Image.new(mode, (str_width, self.height), color=self.white[mode])
        str_draw = ImageDraw.Draw(str_blank)
        #draw on canvas
        for tu in to_use:
            w,h = self.font_objects[tu[0]].getsize(tu[1])
            #assertion
            assert (w == str_width), "Expected width: %s (got %s)   String:\n[%s]" % (str_width, w, tu[1]) 
            draw.text((0,0), tu[1], (0,0,0), font=self.font_objects[tu[0]])
        #save if need
        if save:
            str_blank.save(path, "PNG")
            return path
        else:
            return str_blank

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

    def load_db(self, db, create):
        try:
            #connect
            self.font_db = MySQLdb.connect(host="localhost", user="root", passwd="", db=db, charset="utf8mb4")
            self.font_db.autocommit(True)
            self.font_cur = self.font_db.cursor()
            self.font_points = {}
            self.font_objects = {}
            #get font tables
            tables = []
            self.font_cur.execute("SHOW TABLES")
            for t in self.font_cur.fetchall():
                tables.append(t[0])
            tables.remove("Fonts")
            tables.remove("Normalisation")
            #load fonts
            for t in tables:
                range_ints = []
                self.font_cur.execute("SELECT * FROM `%s`" % t)
                for row in self.font_cur.fetchall():
                    ranges.append(row[0])
                range_tuples = [(range_ints[i], range_ints[i+1]) for i in range(len(range_ints)) if i%2 == 0]
                points = []
                for rt in range_tuples:
                    points += list(range(rt[0], rt[1]+1))
                points = list(set(points))
                points.sort()
                points = tuple(points)
                self.fonts[t] = points
            #load normalisation table
            self.normalisation = {}
            self.font_cur.execute("SELECT * FROM `Normalisation`")
            for row in self.font_cur.fetchall():
                self.normalisation[chr(row[0])] = chr(row[1])
        except Exception as e:
            try:
                if e.args[0] == 1049: #1049 is db doesnt exist or something
                    if create:
                        self.create_db(db)
                    else:
                        raise Exception("Database %s does not exist and create is set to False" % db)

                else:
                    raise e from None
            #not going to catch the second exception if it occurs

    def sort_key(self, ord_set):
        def key(tup):
            return (len(ord_set.intersection(tup[1])), len(tup[1]))
        return key

    def get_ttf_info(self, font_path):
        f = TTFont(font_path)
        uni_decimals = list([cmap.cmap for cmap in f['cmap'].tables][0].keys())
        uni_decimals.sort()
        # could use (font.getBestCmap().keys()) instead? not sure
        size = "getsize using self.width"
        return uni_decimals, size
