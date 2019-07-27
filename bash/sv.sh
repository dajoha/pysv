
#-------------------- function sv()
function sv()
{
	local config_dir=~/.pysv

	local tmp=$(mktemp) || return 1

	local options=( --bs-dump --bs-include-cd )

	if [[ $PYSV_PARSE_CONF == 1 ]]; then
		local bs_conf=/usr/local/lib/pysv/default_config/sv.conf
		[[ -f $config_dir/sv.conf ]] && bs_conf=$config_dir/sv.conf
		options+=( --bs-conf $bs_conf )
	fi

	pysv "${options[@]}" "$@" >$tmp
	ret=$?

	case $ret in
		1) rm $tmp  >/dev/null 2>&1; return 1 ;;
		2) . $tmp ;;
		*) cat $tmp ;;
	esac

	rm $tmp  >/dev/null 2>&1
}


#-------------------- function sva()
function sva()
{
	if [[ $1 == -h ]]; then
		echo "Usage: sva <KEY> [PATH]"
		echo "Raccourci pour sv -a: ajoute le raccourci de projet <KEY> pour le répertoire"
		echo "courant, ou pour [PATH] si précisé."
		return
	fi

	sv -a "$@" || return
	sv # TODO: à améliorer (double exécution)
}


#--------------------     function _sv_completion()
function _sv_completion()
{
	COMPREPLY=()
	while read compl; do
		COMPREPLY+=( "$compl" )
	done < <(pysv --get-completions "${COMP_WORDS[COMP_CWORD]}")
}

complete -F _sv_completion  sv

