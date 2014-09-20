#!/bin/bash

mkdir -p pdfs pdfmaps cache data

function download {
  if [ ! -s "$2" ]; then
    wget -q "$1" -O "$2"
  fi
}

download "http://www.nossenateurs.fr/senateurs/json" cache/senateurs.json
download "http://www.nosdeputes.fr/deputes/json" cache/deputes.json
download "http://2007-2012.nosdeputes.fr/deputes/json" cache/deputes-2007.json
download "http://www.performance-publique.budget.gouv.fr/sites/performance_publique/files/farandole/ressources/2013/rap/pdf/PLR2013_annexe_reserve_parlementaire_senat_P122.pdf" "pdfs/1409-Sénat-réserve-2013.pdf"
download "http://www.performance-publique.budget.gouv.fr/sites/performance_publique/files/farandole/ressources/2013/rap/pdf/PLR2013_annexe_reserve_parlementaire_senat_autre.pdf" "pdfs/1409-Sénat-réserve-2013-autre.pdf"
download "http://www.performance-publique.budget.gouv.fr/sites/performance_publique/files/farandole/ressources/2013/rap/pdf/PLR2013_annexe_reserve_parlementaire_AN_P122.pdf" "pdfs/1409-AN-réserve-2013.pdf"
download "http://www.performance-publique.budget.gouv.fr/sites/performance_publique/files/farandole/ressources/2013/rap/pdf/PLR2013_annexe_reserve_parlementaire_AN_autre.pdf" "pdfs/1409-AN-réserve-2013-autre.pdf"

for pdffile in pdfs/*.pdf; do
  pdftohtml -xml "$pdffile" > /dev/null
  xmlfile=$(echo $pdffile | sed 's/\.pdf$/.xml/')
  # draw maps
  ./bin/convert.py "$xmlfile" 1
  csvfile=$(echo $pdffile | sed 's/\.pdf$/.csv/' | sed 's#pdfs/#data/#')
  ./bin/convert.py "$xmlfile" > "$csvfile"
done

head -n 1 data/1409-Sénat-réserve-2013.csv > data/1409-réserve-parlementaire-2013-Bercy.csv
cat data/1409-Sénat-* data/1409-AN-* | grep -v '^"bénéficiaire"' >> data/1409-réserve-parlementaire-2013-Bercy.csv
