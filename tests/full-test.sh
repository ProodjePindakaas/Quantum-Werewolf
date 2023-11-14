#!/bin/bash

for i in {1..1000}
do
    out=$(python ../quantumwerewolf/cli.py < input.txt)
#     if [[ $out == *'Traceback'* ]]
#     then
#         echo $out
#     fi
done
