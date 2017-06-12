#!/bin/bash

# Simple script to try using GPIO

gpio mode 25 out

delay=".02"

GP[0]=22
GP[1]=23
GP[2]=24
GP[3]=25

COMMAND[0]="0000"
COMMAND[1]="1010"
COMMAND[2]="1001"
COMMAND[3]="0101"
COMMAND[4]="0110"
COMMAND[5]="0000"

# Default direction is left, it's ok, if first arg is right then change commands
steps=1

if [[ $1 == ?(-)+([0-9])  ]] ;
then
	steps=$1
	if (( $1 < 0 ));
	then
		steps=`expr -1 \* $1`
		read COMMAND[1] COMMAND[4] <<< "${COMMAND[4]} ${COMMAND[1]}"
		read COMMAND[2] COMMAND[3] <<< "${COMMAND[3]} ${COMMAND[2]}"
	fi
fi

for (( s=1; s<=$steps; s++ ));
do
	for (( c=0; c<${#COMMAND[*]}; c++ )); do
		cmd=${COMMAND[$c]}
		for (( i=0; i<${#cmd}; i++)); do
			gpio write "${GP[$i]}" "${cmd:$i:1}"
		done
		sleep $delay
	done
done
