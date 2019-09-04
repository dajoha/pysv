
#-------------------- function cv()
function cv()
{
	local config_dir=~/.pysv
	local options=( --global )

	if [[ $PYSV_PARSE_CONF == 1 ]]; then
		local bs_conf=/usr/local/lib/pysv/default_config/cv.conf
		[[ -f $config_dir/cv.conf ]] && bs_conf=$config_dir/cv.conf
		options+=( --bs-conf $bs_conf )
	fi

	sv "${options[@]}" "$@"
}


#-------------------- function cva()
function cva()
{
	if [[ $1 == -h ]]; then
		echo "Usage: cva <KEY> [PATH]"
		echo "Raccourci pour cv -A: ajoute le raccourci global <KEY> pour le répertoire"
		echo "courant, ou pour [PATH] si précisé."
		return
	fi

	cv -A "$@" || return
	cv # TODO: à améliorer (double exécution)
}


# COMPLETION:

#-------------------- function __pysv_cv_completion()
function __pysv_cv_completion()
{
	COMPREPLY=()
	while read compl; do
		COMPREPLY+=( "$compl" )
	done < <(pysv --global --get-completions "${COMP_WORDS[COMP_CWORD]}")
}

complete -F __pysv_cv_completion  cv

