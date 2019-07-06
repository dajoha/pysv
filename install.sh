#!/bin/bash

#-------------------- help()
help()
{
	echo "Usage : ./install"
	echo "Installe pysv vers /usr/local/bin et /usr/local/lib"
}

[[ $1 == -h ]] && { help; exit; }


projname=pysv
prefix=/usr/local

bin=$prefix/bin
lib=$prefix/lib/$projname


mkdir -p $bin      || exit 1

echo "Copie des fichiers:"
for subdir in bash default_config; do
	mkdir -p $lib/$subdir
	for tool in sv cv; do
		cp -v ./$subdir/$tool.* $lib/$subdir  || exit 1
	done
done
cp -v ./pysv_load $lib                        || exit 1

mkdir -p $lib/src  || exit 1
cp -v ./src/pysv.py $lib/src/pysv.py          || exit 1

echo "Création d'un lien vers l'exécutable:"
ln -v -fs $lib/src/pysv.py $bin/$projname     || exit 1

echo -e "\n$projname installé avec succès.\n" >&2

