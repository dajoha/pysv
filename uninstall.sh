#!/bin/bash

#-------------------- help()
help()
{
	echo "Usage : ./uninstall.sh"
	echo "Désinstalle pysv"
}

[[ $1 == -h ]] && { help; exit; }


projname=pysv
prefix=/usr/local

bin=$prefix/bin
lib=$prefix/lib/$projname


# Prévention d'accidents regrettables:
[[ -z $projname ]] && exit 1


# Désinstallation:
if [[ -f $bin/$projname ]]; then
	rm -v "$bin/$projname" || exit 1
fi

if [[ -d $lib ]]; then
	rm -v -r "$lib" || exit 1
fi


echo -e "\n$projname désinstallé avec succès.\n" >&2

