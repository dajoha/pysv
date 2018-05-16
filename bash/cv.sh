

#-------------------- function __pysv_get_global_svinfo()
function __pysv_get_global_svinfo()
{
	echo "${PYSV_GLOBAL_SVINFO-~/.svinfo.global}"
}


#-------------------- function __pysv_cv_completion()
function __pysv_cv_completion()
{
	local svinfo=$(__pysv_get_global_svinfo)

	COMPREPLY=()
	while read compl; do
		COMPREPLY+=( "$compl" )
	done < <(pysv -L $svinfo --get-completions "${COMP_WORDS[COMP_CWORD]}")
}


#-------------------- function cv()
function cv()
{
	local config_dir=~/.pysv

	local svinfo=$(__pysv_get_global_svinfo)

	local options=( -L "$svinfo" )

	if [[ $PYSV_PARSE_CONF == 1 ]]; then
		local bs_conf=/usr/local/lib/pysv/default_config/cv.conf
		[[ -f $config_dir/cv.conf ]] && bs_conf=$config_dir/cv.conf
		options+=( --bs-conf $bs_conf )
	fi

	sv "${options[@]}" "$@"
}


alias cva="cv -A"

complete -F __pysv_cv_completion  cv

