#!/bin/bash

echo "parsing sentences ..."
# only parse sentences that mention the table
# remove the "The point is" part at the beginning of each sentence
if test "location_descriptions.csv" -nt "parses.csv"
then
cat location_descriptions.csv | perl -pe "s/The point is //" | python parse.py > parses.csv
fi


echo "performing surgery ..."
# extract the parse column (excluding header)
cat parses.csv | cut -d, -f4 | perl -ne "print unless $. == 1" > trees.txt
# perform tree surgery
java -mx100m -cp stanford-tregex/stanford-tregex.jar \
     edu.stanford.nlp.trees.tregex.tsurgeon.Tsurgeon \
     -s -treeFile trees.txt surgery/* > modtrees.txt


echo "writing results ..."
# merge everything into a csv file
echo modparse | cat - modtrees.txt | paste -d, parses.csv - > modparses.csv


echo "counting stuff ..."
# make sure the database exists
python models.py
# sample ten times for each example
python counter.py modparses.csv -i10
