#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, re, json

filepath = sys.argv[1]
with open(filepath, 'r') as xml_file:
    xml = xml_file.read()

drawMap = False
if len(sys.argv) > 2:
    drawMap = True

lastp = "all"
filterallpages = True
minl = 0
mint = 100
maxt = 1200
limits = [
  (100, 0, str),
  (200, 1, str),
  (315, 2, str),
  (360, 3, str),
  (535, 4, int),
  (600, 5, str),
  (700, 6, str),
  (1200, 8, int)
]
checkidx = 8
if "-autre" in filepath:
    limits = [
      (100, 0, str),
      (315, 2, str),
      (500, 3, str),
      (565, 4, int),
      (650, 5, str),
      (1000, 6, str),
    ]
    checkidx = 6

with open("cache/senateurs.json", 'r') as f:
    sens = [p["senateur"] for p in json.load(f)['senateurs']]
with open("cache/deputes.json", 'r') as f:
    deps = [p["depute"] for p in json.load(f)['deputes']]
with open("cache/deputes-2007.json", 'r') as f:
    deps += [p["depute"] for p in json.load(f)['deputes']]
with open("cache/deputes-2002.json", 'r') as f:
    oldparls = {u.encode("utf-8"): 1 for u in json.load(f)}
if "-AN-" in filepath:
    typeparl = "Assemblée nationale"
    parls = deps + sens
elif "-Sénat-" in filepath:
    typeparl = "Sénat"
    parls = sens + deps

parls_dep = {}
for p in parls:
    dep = str(p["num_deptmt"]).upper()
    if dep not in parls_dep:
        parls_dep[dep] = []
    parls_dep[dep].append(p)
errors = {}

re_clean_bal = re.compile(r'<[^>]+>')
re_clean_spaces = re.compile(r'\s+')
clean = lambda x: re_clean_spaces.sub(' ', re_clean_bal.sub('', str(x))).strip()

re_clean_dep = re.compile(r"^\s*(\d+[AB]?) .*$")
clean_dep = lambda x: re_clean_dep.sub(r"\1", x.upper())
re_clean_euros = re.compile(r"\D")
clean_euros = lambda x: int(re_clean_euros.sub("", x))

regexps = [(re.compile(r), s) for r, s in [
    (u'[àâ]', 'a'),
    (u'[ÀÂ]', 'A'),
    (u'[éèêë]', 'e'),
    (u'[ÉÈÊË]', 'E'),
    (u'[îï]', 'i'),
    (u'[ÎÏ]', 'I'),
    (u'[ôö]', 'o'),
    (u'[ÔÔ]', 'O'),
    (u'[ùûü]', 'u'),
    (u'[ÙÛÜ]', 'U'),
    (u'ç', 'c'),
    (u'Ç', 'C'),
]]
def clean_accents(t):
    if not isinstance(t, unicode):
        t = t.decode('utf-8')
    for r, s in regexps:
        t = r.sub(s, t)
    return t
cleaner = re.compile(r'\W')
checker = lambda x: cleaner.sub('', clean(clean_accents(x))).lower().strip()

re_particule = re.compile(u"^\s*(d(?:(?:'|e l')|(?:[eu]|es|e la) ))(.*)$", re.I)
re_clean_nom = re.compile(u"^\s*((?:[A-Z\-'duela]+ )+)([A-Z\-][^A-Z\-'].*)$")
reorder_nom = lambda x: re_clean_nom.sub(r"\2 \1", re_particule.sub(r"\2 \1", x))

def find_parl(nom, dep):
    orig = nom
    nom = clean_accents(nom.strip())
    if nom in oldparls:
        return "old"
    nom = reorder_nom(nom)
    nom = checker(nom)
    nom = nom.replace("hevainqueurchristophe", "helenevainqueurchristophe")
    nom = nom.replace("rogergerschwartzenberg", "rogergerardschwartzenberg")
    nom = nom.replace("francoisdescampscrosnier", "francoisedescampscrosnier")
    nom = nom.replace("berangerepoletti", "berengerepoletti")
    nom = nom.replace("pozzodiborgoyves", "yvespozzodiborgo")
    nom = nom.replace("josephfrancois", "joseph")
    nom = nom.replace("martinecarilloncouvreur", "martinecarrilloncouvreur")
    nom = nom.replace("richardariihautuheiava", "richardtuheiava")
    nom = nom.replace("christophefrassa", "christopheandrefrassa")
    nom = nom.replace("daphpoznanskibenhamou", "daphnapoznanskibenhamou")
    nom = nom.replace("pavymorancais", "pavy")
    if nom == "rogerromani":
        dep = 75
    elif nom == "andrevallet":
        dep = 13
    elif nom == "jeanchristophelagarde":
        dep = "93"
    elif nom == "francoisebriand":
        dep = "91"
    elif nom == "nicolasalfonsi":
        dep = "2A"
    elif dep.startswith('SAINT-PIERRE'):
        dep = 975
    elif dep.startswith('SAINT-BARTH'):
        dep = 977
    elif 'WALLIS' in dep:
        dep = 986
    elif dep.startswith('POLYN'):
        dep = 987
    elif dep.startswith('NOUVELLE'):
        dep = 988
    elif dep.startswith('FRAN'):
        dep = 999
    dep = str(dep).upper()
    for parl in parls_dep[dep]:
        if checker(parl['nom']) == nom:
            return parl
    if nom not in errors:
        sys.stderr.write("Could not find %s %s in %s (%s)\n" % (typeparl, orig, dep, nom))
    errors[nom] = 1
    return None

re_fused = re.compile(r"^(\D+)(\d+[AB]? - .*)$")

page = 0
topvals = {}
leftvals = {}
maxtop = 0
maxleft = 0
results = []
headers = ['bénéficiaire', 'département', 'montant versé en 2013 (€)', 'nature de la subvention', 'programme budgétaire', 'attributeur', 'département attributeur', 'mandat attributeur', "année d'octroi de la subvention", 'prénom', 'nom', 'sexe', "groupe", 'url_institution', 'url_nosparlementaires', 'url_nosparlementaires_api']
record = ["", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""]
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
    text = attrs.group(4).replace("&amp;", "&").replace("&quot;", '"')
    #print >> sys.stderr, "DEBUG %s %s %s %s" % (font, left, top, text)
    if ((page == 1 or filterallpages) and top < mint) or ((lastp == "all" or page == lastp) and top > maxt):
        continue
    if left < minl:
        continue
    for limit, idx, typ in limits:
        if left < limit:
            if typ == int:
                record[idx] = int(clean(text))
            else:
                record[idx] += clean(text)+ " "
            break

    if not record[6] and re_fused.match(record[5]):
        res = re_fused.search(record[5])
        record[5] = res.group(1)
        record[6] = res.group(2)
    if record[checkidx] and record[0]:
        record[7] = typeparl
        record[1] = clean_dep(record[1])
        record[2] = clean_euros(record[2])
        record[6] = clean_dep(record[6])
        #print >> sys.stderr, record
        parl = find_parl(record[5], record[6])
        if parl == "old":
            record[7] = "Député"
            record[12] = "11ème législature (2002-2007)"
        elif parl:
            if parl.get("url_an", ""):
                record[7] = "Député"
            else:
                record[7] = "Sénateur"
            typ = record[7].replace("é", "e").lower()
            record[6] = clean_dep(parl.get('num_deptmt'))
            record[9] = parl.get('prenom').encode('utf-8')
            record[10] = parl.get('nom_de_famille').encode('utf-8')
            record[11] = parl.get('sexe').encode('utf-8')
            record[12] = parl.get('groupe_sigle', "")
            record[13] = parl.get('url_institution', parl.get('url_an')).encode('utf-8')
            record[14] = parl.get('url_nos%ss' % typ).encode('utf-8')
            record[15] = parl.get('url_nos%ss_api' % typ).encode('utf-8').replace("/json", "/xml")
        else:
            record[5] = record[5].strip("_ ")
            record[5] = record[5].replace("Présidence de l'Assemblée national", "Présidence de l'Assemblée nationale")
        results.append(record)
    if record[checkidx]:
        record = ["", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""]

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

