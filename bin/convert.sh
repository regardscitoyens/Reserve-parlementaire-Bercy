#!/bin/bash

mkdir -p pdfs pdfmaps cache data

wget -q "http://www.nossenateurs.fr/senateurs/json" -O cache/senateurs.json
wget -q "http://www.performance-publique.budget.gouv.fr/sites/performance_publique/files/farandole/ressources/2013/rap/pdf/PLR2013_annexe_reserve_parlementaire_senat_P122.pdf" -O "pdfs/1409-Sénat-réserve-2013.pdf"

for pdffile in pdfs/*.pdf; do
  pdftohtml -xml "$pdffile" > /dev/null
  xmlfile=$(echo $pdffile | sed 's/\.pdf$/.xml/')
  # draw maps
  ./bin/convert.py "$xmlfile" 1
  csvfile=$(echo $pdffile | sed 's/\.pdf$/.csv/' | sed 's#pdfs/#data/#')
  ./bin/convert.py "$xmlfile" > "$csvfile"
done

