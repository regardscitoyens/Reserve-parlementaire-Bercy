#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, re, json

filepath = sys.argv[1]
with open(filepath, 'r') as xml_file:
    xml = xml_file.read()

drawMap = False
if len(sys.argv) > 2:
    drawMap = True

filterallpages = True
minl = 0
mint = 100
maxt = 1200
lastp = "all"
with open("cache/senateurs.json", 'r') as f:
    parls = [p["senateur"] for p in json.load(f)['senateurs']]
parls_dep = {}
for p in parls:
    dep = str(p["num_deptmt"]).upper()
    if dep not in parls_dep:
        parls_dep[dep] = []
    parls_dep[dep].append(p)

re_clean_bal = re.compile(r'<[^>]+>')
re_clean_spaces = re.compile(r'\s+')
clean = lambda x: re_clean_spaces.sub(' ', re_clean_bal.sub('', str(x))).strip()

re_clean_dep = re.compile(r"^\s*(\d+[AB]?) .*$")
clean_dep = lambda x: re_clean_dep.sub(r"\1", x.upper())
re_clean_euros = re.compile(r"\D")
clean_euros = lambda x: int(re_clean_euros.sub("", x))

regexps = [(re.compile(r), s) for r, s in [
    (u'[àÀ]', 'a'),
    (u'[éÉèÈêÊëË]', 'e'),
    (u'[îÎïÏ[]', 'i'),
    (u'[ôÔöÔ]', 'o'),
    (u'[ùÙûÛüÜ]', 'u'),
    (u'[çÇ]', 'c'),
    (u'\W', '')
]]
def clean_accents(t):
    if not isinstance(t, unicode):
        t = t.decode('utf-8')
    for r, s in regexps:
        t = r.sub(s, t)
    return t
checker = lambda x: clean(clean_accents(x)).lower().strip()

re_clean_part = re.compile(ur"^\s*([^A-Z]*) ([A-ZÉ].*)$")
clean_part = lambda x: re_clean_part.sub(r"\2 \1", x)

def find_parl(nom, dep):
    nom = clean_part(nom)
    nom = checker(nom)
    nom = nom.replace("josephfrancois", "joseph")
    if nom == "romaniroger":
        dep = 75
    elif nom == "valletandre":
        dep = 13
    dep = str(dep).upper()
    for parl in parls_dep[dep]:
        if checker("%s %s" % (parl['nom_de_famille'], parl['prenom'])) == nom:
            return parl
    sys.stderr.write("Could not find %s in %s\n" % (nom, dep))
    return None

page = 0
topvals = {}
leftvals = {}
maxtop = 0
maxleft = 0
results = []
headers = ['bénéficiaire', 'département', 'montant versé en 2013 (€)', 'nature de la subvention', 'programme budgétaire', 'attributeur', 'département attributeur', "année d'octroi de la subvention", 'prénom', 'nom', 'sexe', 'url_sénat', 'url_nossénateurs', 'url_nossénateurs_api']
record = ["", "", "", "", "", "", "", "", "", "", "", "", "", ""]
re_line = re.compile(r'<page number|text top="(\d+)" left="(\d+)"[^>]*font="(\d+)">(.*)</text>', re.I)
for line in (xml).split("\n"):
    #print "DEBUG %s" % line
    if line.startswith('<page'):
        page += 1
    if not line.startswith('<text'):
        continue
    attrs = re_line.search(line)
    if not attrs or not attrs.groups():
        raise Exception("WARNING : line detected with good font but wrong format %s" % line)
    font = int(attrs.group(3))
    top = int(attrs.group(1))
    if top > maxtop:
        maxtop = top
    if not font in topvals:
        topvals[font] = []
    topvals[font].append(top)
    left = int(attrs.group(2))
    if left > maxleft:
        maxleft = left
    if not font in leftvals:
        leftvals[font] = []
    leftvals[font].append(left)
    if drawMap:
        continue
    #print "DEBUG %s %s %s %s" % (font, left, top, text)
    if ((page == 1 or filterallpages) and top < mint) or ((lastp == "all" or page == lastp) and top > maxt):
        continue
    if left < minl:
        continue
    text = attrs.group(4).replace("&amp;", "&").replace("&quot;", '"')
    if left < 100:
        record[0] += clean(text)+ " "
    elif left < 200:
        record[1] += clean(text)+ " "
    elif left < 315:
        record[2] += clean(text)+ " "
    elif left < 350:
        record[3] += clean(text)+ " "
    elif left < 525:
        record[4] = int(clean(text))
    elif left < 550:
        record[5] += clean(text)+ " "
    elif left < 660:
        record[6] += clean(text)+ " "
    else:
        record[7] = int(clean(text))
    if record[7]:
        record[1] = clean_dep(record[1])
        record[2] = clean_euros(record[2])
        record[6] = clean_dep(record[6])
        parl = find_parl(record[5], record[6])
        if parl:
            record[8] = parl.get('prenom').encode('utf-8')
            record[9] = parl.get('nom_de_famille').encode('utf-8')
            record[10] = parl.get('sexe').encode('utf-8')
            record[11] = parl.get('url_institution').encode('utf-8')
            record[12] = "http://nossenateurs.fr/%s" % parl.get('slug').encode('utf-8')
            record[13] = "http://nossenateurs.fr/%s/xml" % parl.get('slug').encode('utf-8')
        results.append(record)
        record = ["", "", "", "", "", "", "", "", "", "", "", "", "", ""]

def format_csv(v):
    try:
        return str(int(v))
    except:
        return "\"%s\"" % v.replace('"', '""')

if not drawMap:
    print ",".join(['"%s"' % h for h in headers])
    for i in results:
        for j in range(len(i)):
            i[j] = clean(i[j])
        print ",".join([format_csv(i[a]) for a,_ in enumerate(i)])

else:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib import cm

    fig = plt.figure(figsize=(8.5, 12))
    ax = fig.add_subplot(111)
    ax.grid(True, fillstyle='left')
    nf = len(leftvals)
    for font in leftvals:
        color = cm.jet(1.5*font/nf)
        ax.plot(leftvals[font], topvals[font], 'ro', color=color, marker=".")
        plt.figtext((font+1.)/(nf+1), 0.95, "font %d" % font, color=color)
    plt.xticks(np.arange(0, maxleft + 50, 50))
    plt.yticks(np.arange(0, maxtop + 50, 50))
    plt.xlim(0, maxleft + 50)
    plt.ylim(0, maxtop + 50)
    plt.gca().invert_yaxis()
    mappath = filepath.replace(".xml", ".png").replace("pdfs/", "pdfmaps/")
    fig.savefig(mappath)
    fig.clf()
    plt.close(fig)

