#!/usr/bin/python3
# coding: utf-8

import sys
import os
from pathlib import Path
import argparse
import re
import shlex


# Nom du fichier à vérifier à chaque niveau de répertoire:
SvinfoFilename = Path('.svinfo')

# Noms de variables interdits lors de la génération des scripts bash:
Forbidden_VarNames = [
    '_'   , 'DISPLAY', 'HOME' , 'LANG', 'LOGNAME', 'MAIL'  , 'OLDPWD',
    'PATH', 'PWD'    , 'SHELL', 'TERM', 'USER'   , 'VISUAL',
]


#-------------------- class PysvError(Exception)
class PysvError(Exception):
    pass



#-------------------- def filterByPrefix(arr, prefix)
def filterByPrefix(arr, prefix):
    return [ s for s in arr if s[:len(prefix)] == prefix ]


#-------------------- def isYes(s)
def isYes(s):
    return s in ['y', 'yes']




#-------------------- class NameTransformer
class NameTransformer:
    #-------------------- def upperFirstLetter(self, word)
    def upperFirstLetter(self, word):
        return word.capitalize()


    #-------------------- def upperAll(self, word)
    def upperAll(self, word):
        return word.upper()


    #-------------------- def noTransform(self, word)
    def noTransform(self, word):
        return word


    #-------------------- def __init__(self, template)
    def __init__(self, template):
        try:

            open_paren = template.index('(')
            close_paren = template.index(')')

            if open_paren > close_paren:
                raise(PysvError("parenthèses mal placées"))

            self.prefix = template[:open_paren]
            self.templ_name = template[open_paren+1:close_paren]
            self.suffix = template[close_paren+1:]

            if not re.fullmatch('[A-Za-z_]{2,}', self.templ_name):
                raise(PysvError("nom de patron entre parenthèses '{}'".format(self.templ_name)))

            if self.templ_name.isupper():
                self.case_tranform = self.upperAll
            elif self.templ_name[0].isupper():
                self.case_tranform = self.upperFirstLetter
            else:
                self.case_tranform = self.noTransform

        except Exception as e:
            pysv_msg = isinstance(e, PysvError) and " ({})".format(e) or ''
            raise(PysvError(
                'Patron de nom de variable/alias bash invalide{}: "{}"'
                .format(pysv_msg, template)
            ))


    #-------------------- def transform(self, name)
    def transform(self, name):
        return self.prefix + self.case_tranform(name) + self.suffix




#-------------------- class BSOptions
class BSOptions:
    #-------------------- def __init__(self, args)
    def __init__(self, args):
        self.include_vars = self.include_aliases = False

        # Templates par défaut, si on n'a ni option --bs-*-templ, ni fichier de config
        # --bs-conf:
        self.vars_templ    = '(name)'
        self.aliases_templ = ',(name)'
        self.root_name = None

        if args.bs_conf:
            self.parseConf(args.bs_conf)

        if args.bs_include_vars:    self.include_vars    = isYes(args.bs_include_vars)
        if args.bs_include_aliases: self.include_aliases = isYes(args.bs_include_aliases)
        if args.bs_vars_templ:      self.vars_templ      = args.bs_vars_templ
        if args.bs_aliases_templ:   self.aliases_templ   = args.bs_aliases_templ
        if args.bs_vars_root_name:  self.root_name       = args.bs_vars_root_name

        self.include_cd = args.bs_include_cd

        if self.include_vars:
            self.transform_var = NameTransformer(self.vars_templ).transform
        if self.include_aliases:
            self.transform_alias = NameTransformer(self.aliases_templ).transform


    #-------------------- def parseConf(self, conf_file)
    def parseConf(self, conf_file):
        try:
            with open(conf_file, 'r') as infile:
                pattern = re.compile('(\w+)\s*=\s*(\S+)')
                for line in infile:
                    match = pattern.match(line)
                    if not match:
                        continue

                    varname, value = match.group(1, 2)

                    if   varname == 'BashVarsEnable':      self.include_vars = isYes(value)
                    elif varname == 'BashVarsTemplate':    self.vars_templ = value
                    elif varname == 'BashVarsRootName':    self.root_name = value
                    elif varname == 'BashAliasesEnable':   self.include_aliases = isYes(value)
                    elif varname == 'BashAliasesTemplate': self.aliases_templ = value

        except FileNotFoundError as e:
            raise PysvError(
                "Impossible d'ouvrir le fichier de configuration '{}'"
                .format(conf_file)
            )




#-------------------- class SviPath
class SviPath:
    #-------------------- def __init__(self, svinfo, path)
    def __init__(self, svinfo, path):
        self.svinfo = svinfo
        self.setPath(path)


    #-------------------- def setPath(self, path)
    def setPath(self, path):
        self.path = path
        slash_split = self.path.split('/')
        self.key = slash_split[0]
        self.subpath = None
        if len(slash_split) > 1:
            self.subpath = '/'.join(slash_split[1:])


    #-------------------- def getKeyPath(self, absolute=False)
    def getKeyPath(self, absolute=False):
        return self.svinfo.getKey(self.key, absolute)


    #-------------------- def getPath(self, absolute=False)
    def getPath(self, absolute=False):
        path = self.getKeyPath(absolute)
        if self.subpath != None:
            path = path / self.subpath
        return path


    #-------------------- def hasSubpath(self)
    def hasSubpath(self):
        return self.subpath != None


    #-------------------- def getSubpath(self)
    def getSubpath(self):
        return self.subpath == None and None or Path(self.subpath)


    #-------------------- def isDir(self)
    def isDir(self):
        return self.getPath(True).is_dir()


    #-------------------- def exists(self)
    def exists(self):
        return self.getPath(True).exists()


    #-------------------- def listDir(self)
    def listDir(self):
        return os.listdir(self.getPath(True))


    #-------------------- def getCompletions(self)
    def getCompletions(self):
        svinfo = self.svinfo
        completions = []

        try:
            if not self.hasSubpath():
                completions = filterByPrefix(svinfo.getKeys(), self.path)
            else:
                path_parts = self.path.split('/')
                last_part = path_parts[-1]
                base_path = '/'.join(path_parts[:-1])
                svi_base_path = SviPath(svinfo, base_path)
                files = filterByPrefix(svi_base_path.listDir(), last_part)
                completions = [ "{}/{}".format(base_path, f) for f in files ]

            completions = [ comp + (SviPath(svinfo, comp).isDir() and '/' or '') for comp in completions ]

            if len(completions) == 1:
                svi_path = SviPath(svinfo, completions[0])
                if svi_path.isDir():
                    files = svi_path.listDir()
                    files = [ svi_path.path + f for f in files ]
                    completions.extend(files)
        except Exception as e:
            pass

        return completions




#-------------------- class Svinfo
class Svinfo:

    #-------------------- def __init__(self, from_path, create_file_if_possible=False)
    def __init__(self, from_path, create_file_if_possible=False):
        self.svinfo_file = self.findSvinfo(from_path)
        self.exists = self.svinfo_file and self.svinfo_file.is_file()
        self.error = None

        if self.svinfo_file:
            if not self.exists and create_file_if_possible:
                self.svinfo_file.touch()
                self.exists = True
            self.project_dir = self.svinfo_file.parent

        if self.exists:
            try:
                self.parseSvinfo()
            except PysvError as e:
                self.error = e


    #-------------------- def findSvinfo(from_path=None)
    @staticmethod
    def findSvinfo(from_path=None):
        if from_path == None:
            folder = Path.cwd()
            while True:
                svinfo_file = folder / SvinfoFilename
                if svinfo_file.is_file(): break
                if folder.parent == folder: return None
                folder = folder.parent

        else:
            path = Path(from_path).expanduser()

            if path.is_file() or (not path.exists() and path.parent.is_dir()):
                svinfo_file = path
            elif path.is_dir():
                svinfo_file = path / SvinfoFilename
            else:
                raise(PysvError("Le chemin {} n'existe pas.".format(path)))

        name = svinfo_file.name
        return svinfo_file.parent.resolve() / name


    #-------------------- def parseSvinfo(self)
    def parseSvinfo(self):
        blank_line = re.compile('^\s*$')
        line_pattern = re.compile('^([a-zA-Zéèàêùïà_,][a-zA-Zéèàêùïà0-9_,]*)\s+(?:(\?)\s+)?(.+)$')
        self.defs = {}
        with open(str(self.svinfo_file), 'r') as infile:
            for line_nr, line in enumerate(infile, 1):
                if blank_line.match(line) != None:
                    continue
                match = line_pattern.match(line)
                if match == None:
                    raise PysvError("Erreur de parse du fichier '{}', ligne {}".format(self.svinfo_file, line_nr))

                groups = match.groups()

                keys = groups[0].split(',')
                for key in keys:
                    self.defs[key] = groups[2]


    #-------------------- def getKeys(self, filter_paths=None)
    def getKeys(self, filter_paths=None):
        if not filter_paths:
            return self.defs.keys()
        else:
            return [ k for k in self.defs if str(self.defs[k]) in filter_paths ]


    #-------------------- def getFullPaths(self)
    def getFullPaths(self):
        keys = self.getKeys()
        paths = [ self.getKey(k) for k in keys ]
        return paths


    #-------------------- def check(self, format='svinfo')
    def check(self, format='svinfo'):
        paths = self.getFullPaths()
        inexistent_paths = []
        for path in paths:
            if not path.exists():
                inexistent_paths.append(str(path))

        if format == 'svinfo':
            nb_shortcuts = len(inexistent_paths)
            if nb_shortcuts == 0:
                print("Aucun raccourci cassé n'a été trouvé dans le fichier '{}'.".format(self.svinfo_file))
            else:
                s = nb_shortcuts > 1 and 's' or ''
                print("Trouvé {} raccourci{s} cassé{s} dans le fichier '{}':".format(nb_shortcuts, self.svinfo_file, s=s))
                print(self.getDump(filter_paths=inexistent_paths, prefix='  '))
        elif format == 'get_keys':
            for k in self.getKeys(filter_paths=inexistent_paths):
                print(k)


    #-------------------- def getShortcutPath(self, keyword_path)
    def getShortcutPath(self, keyword_path):
        if keyword_path == '/' : return self.project_dir
        if keyword_path == ''  : raise PysvError("Mot-clé attendu.")

        svi_path = SviPath(self,  keyword_path)
        return svi_path.getPath(True)


    #-------------------- def relPathTo(self, path)
    def relPathTo(self, path):
        return os.path.relpath(path, self.project_dir)


    #-------------------- def getShortcutsByPath(self, filter_paths=None)
    def getShortcutsByPath(self, filter_paths=None):
        paths = {}
        for key, path in self.defs.items():
            if filter_paths and path not in filter_paths:
                continue
            if path not in paths:
                paths[path] = []
            paths[path].append(key)
        return paths


    #-------------------- def getKey(self, key, absolute=False)
    def getKey(self, key, absolute=False):
        if key == '':
            path = '.'
        elif key not in self.defs:
            raise PysvError("Le mot-clé '{}' n'existe pas.".format(key))
        else:
            path = self.defs[key]

        if absolute:
            return Path(self.project_dir) / path
        else:
            return Path(path)


    #-------------------- def searchForPath(self, path)
    def searchForPath(self, path):
        path = Path(path).resolve()
        shorcuts_by_path = self.getShortcutsByPath()

        for def_path, shortcuts in shorcuts_by_path.items():
            def_path = self.project_dir / def_path
            if path == def_path:
                return shortcuts

        return []


    #-------------------- def add(self, keyword, path, absolute=False)
    def add(self, keyword, path, absolute=False):
        self.defs[keyword] = absolute and path.resolve() or self.relPathTo(path)
        return keyword, self.defs[keyword]


    #-------------------- def do_add(self, add_args, absolute=False, force=False)
    def do_add(self, add_args, absolute=False, force=False):
        key = add_args[0]

        if key in self.defs and not force:
            raise PysvError("Le mot-clé '{}' existe déjà ({}). Utilisez -f pour forcer."
                    .format(key, self.defs[key]))

        if len(add_args) > 1:
            path = Path(add_args[1])
        else:
            path = Path.cwd()

        return self.add(key, path, absolute)


    #-------------------- def remove(self, keyword)
    def remove(self, keyword):
        has_keyword = keyword in self.defs
        if has_keyword:
            del self.defs[keyword]
        return has_keyword


    #-------------------- def getCompletions(self, arg)
    def getCompletions(self, arg):
        p = SviPath(self, arg)
        return p.getCompletions()


    #-------------------- def getBashScriptDump(self, args)
    def getBashScriptDump(self, args):
        # Détermine les options pour le dump, en prenant en compte les arguments fournis
        # en ligne de commande, et éventuellement par un fichier de configuration:
        opts = BSOptions(args)

        dump = ''
        for key, shortcut_path in self.defs.items():
            # Si shortcut_path est absolu, alors self.project_dir sera ignoré, ce qui
            # permet l'utilisation des raccourcis globaux dans les fichiers .svinfo:
            path = self.project_dir / shortcut_path
            quoted_path = shlex.quote(str(path))

            if opts.include_aliases and path.is_dir():
                quoted_alias=shlex.quote('cd {}'.format(quoted_path))
                dump += "alias {}={}\n".format(opts.transform_alias(key), quoted_alias)

            if opts.include_vars:
                var_name = opts.transform_var(key)
                if not var_name in Forbidden_VarNames:
                    dump += "{}={}\n".format(var_name, quoted_path)

        if opts.include_aliases:
            root_alias = opts.transform_alias('')
            if len(root_alias) != 0:
                # TODO: ci-dessous:   self.project_dir ==> shlex.quote(self.project_dir)  ?
                dump += "alias {}='cd {}'\n".format(root_alias, self.project_dir)

        if opts.include_vars:
            quoted_path = shlex.quote(str(self.project_dir))
            if opts.root_name != None:
                dump += "{}={}\n".format(opts.root_name, quoted_path)

        if opts.include_cd and args.keyword:
            path = shlex.quote(str(self.getShortcutPath(args.keyword)))
            dump += "cd {}".format(path)

        return dump


    #-------------------- def getJsonDump(self, filter_paths=None)
    def getJsonDump(self, filter_paths=None):
        # TODO: filter_paths

        import json

        data = { item[0] : str(self.project_dir / item[1]) for item in self.defs.items() }
        data['root'] = str(self.project_dir)

        return json.dumps(data);


    #-------------------- def getDump(self, absolute=False, json=False, ....)
    def getDump(self, absolute=False, json=False, filter_paths=None, prefix=''):
        # TODO: gérer absolute
        if json:
            return self.getJsonDump(filter_paths=filter_paths)

        shorcuts_by_path = self.getShortcutsByPath(filter_paths=filter_paths)

        dump = ''

        margin = 2  # Marge minimum pour l'alignement de la 1ère colonne

        # Pour l'alignement:
        max_col1_width = 0
        for shortcuts in shorcuts_by_path.values():
            shortcuts_strlen = len(','.join(shortcuts))
            if max_col1_width < shortcuts_strlen:
                max_col1_width = shortcuts_strlen

        for path, shortcuts in shorcuts_by_path.items():
            if len(dump) != 0:
                dump += '\n'
            dump += prefix
            shortcuts_str = ','.join(shortcuts)
            dump += shortcuts_str
            # Pour l'alignement:
            nb_spaces = max_col1_width - len(shortcuts_str) + margin
            dump += nb_spaces * ' '
            dump += str(path)

        return dump


    #-------------------- def save(self)
    def save(self):
        with open(str(self.svinfo_file),'w') as f:
            f.write(self.getDump() + '\n')




#-------------------- def create_parser(short_help=false)
def create_parser(short_help=False):
    parser = argparse.ArgumentParser(
        prog = 'pysv',
        description = "Gère les fichiers '.svinfo' .",
        add_help = False,
    )

    parser.add_argument('keyword', metavar='KEY', nargs='?', default='',
        help="Raccourci désignant un chemin soit local à un un projet, soit dépendant de l'option -L")

    parser.add_argument('-i', '--get-svinfo-file', action='store_true',
        help="Affiche le chemin vers le fichier .svinfo trouvé (ou précisé, cf option -L)")
    parser.add_argument('-C', '--directory', metavar='PATH',
        help="Exécute pysv comme si PATH était le répertoire courant")
    parser.add_argument('-L', '--svinfo-path', metavar='PATH',
        help="Choisit un fichier svinfo particulier au lieu de chercher dans l'arborescence courante")
    parser.add_argument('-l', '--list', nargs='*', metavar='KEY',
        help="Affiche les raccourcis actuels (contenu du fichier .svinfo trouvé). "+
             "Avec l'option '-u', affiche les chemins complets vers ces raccourcis.")
    parser.add_argument('--get-keys', action='store_true',
        help="Affiche la liste de tous les noms de raccourci existants")
    parser.add_argument('--check', action='store_true',
        help="Vérifie l'existence des chemins de chaque raccourci et affiche les problèmes trouvés")
    parser.add_argument('-p', '--get-project-dir', action='store_true',
        help="Affiche le chemin racine où se trouve le fichier .svinfo trouvé (ou précisé, cf option -L)")
    parser.add_argument('-s', '--search', nargs='?', metavar='PATH', const='.',
        help="Cherche le répertoire courant (ou le répertoire indiqué PATH) dans les raccourcis")

    parser.add_argument('-a', '--add', nargs='+', metavar='KEY',
        help="Ajoute un mot-clé pour le répertoire courant")
    parser.add_argument('-A', '--add-absolute', nargs='+', metavar='KEY',
        help="Ajoute un mot-clé pour le répertoire courant, avec un chemin absolu (équivalent de -ua)")
    parser.add_argument('-r', '--remove', nargs='+', metavar='KEY',
        help="Supprime des raccourcis")
    parser.add_argument('-I', '--init', nargs='?', metavar='PATH', const='.',
        help="Initialise un fichier .svinfo dans le répertoire courant (ou le répertoire "+
             "PATH donné). Équivalent de la commande linux 'touch .svinfo'.")

    parser.add_argument('-f', '--force', action='store_true',
        help="Forcer l'écrasement des raccourcis existants avec -a ou -A")
    parser.add_argument('-u', '--absolute', action='store_true',
        help="Pour l'option --add et --list: utilise des chemins absolus")
    parser.add_argument('-j', '--json', action='store_true',
            help="Pour les options -l, --get-keys: affiche les informations au format json")

    if not short_help:

        parser.add_argument('--get-completions', metavar='WORD',
            help="Affiche la liste des complétions possibles pour le début de mot indiqué")

        parser.add_argument('--bs-dump', action="store_true",
            help="Affiche des commandes bash de génération d'aliases et de variables (argument interne)")
        parser.add_argument('--bs-conf', metavar='CONFFILE',
            help="Utilise un fichier de config pour remplacer --bs-vars-templ, --bs-aliases-templs, "+
                 "ainsi que l'argument fourni à --get-bash-script")

        parser.add_argument('--bs-vars-templ', metavar='TEMPLATE',
            help="Définit le patron pour générer les noms de variable bash")
        parser.add_argument('--bs-include-vars', metavar='VAL',
            help="Indique s'il faut inclure les variable bash")
        parser.add_argument('--bs-vars-root-name', metavar='VARNAME', default=None,
            help="Spécifie un nom de variable à définir pour le chemin racine du projet")

        parser.add_argument('--bs-aliases-templ', metavar='TEMPLATE',
            help="Définit le patron pour générer les noms d'alias bash")
        parser.add_argument('--bs-include-aliases', metavar='VAL',
            help="Indique s'il faut inclure les alias bash")
        parser.add_argument('--bs-include-cd', action='store_true',
            help="Ajoute au script bash une commande 'cd' pour l'alias donné")

    parser.add_argument('-h', '--help', action='store_true',
        help="Affiche l'aide")
    parser.add_argument('-H', '--more-help', action='store_true',
        help="Affiche l'aide complète")

    return parser




#TODO:
def extra_help():
    print('''
''')



#-------------------- if __name__ == '__main__'
if __name__ == '__main__':

    try:
        parser = create_parser()
        args = parser.parse_args(sys.argv[1:])


        if args.help:
            shorthelp_parser = create_parser(True)
            shorthelp_parser.print_help()
            sys.exit()
        if args.more_help:
            parser.print_help()
            extra_help()
            sys.exit()


        if args.directory:
            os.chdir(args.directory)


        if args.init:
            init_path = args.init

            svinfo_file = Path(init_path) / '.svinfo'

            if svinfo_file.exists():
                if not args.force:
                    raise(PysvError(
                        "Impossible d'initialiser: le fichier existe; utilisez "+
                        "l'option -f pour forcer la suppression de l'ancien fichier."
                    ))

                svinfo_file.unlink()

            else:
                found_svinfo = Svinfo.findSvinfo(init_path)
                if found_svinfo != None and found_svinfo.exists() and not args.force:
                    raise(PysvError(
                        "Un fichier .svinfo a été trouvé en amont: {}\n".format(found_svinfo) +
                        "Utilisez l'option -f pour forcer une création imbriquée."
                        ))

            svinfo_file.touch()

            path = init_path == '.' and 'courant' or init_path
            print("Fichier .svinfo initialisé dans le dossier {}.".format(path))

            sys.exit()


        if args.add_absolute:
            args.absolute = True
            args.add = args.add_absolute
        possibly_create_file = bool(args.add)


        svinfo = Svinfo(args.svinfo_path, possibly_create_file)


        if not svinfo.exists:
            raise(PysvError("Aucun projet trouvé"))


        if   args.get_project_dir : print(svinfo.project_dir)
        elif args.get_svinfo_file : print(svinfo.svinfo_file)
        elif args.check:
            format = 'svinfo'
            if args.get_keys:
                format = 'get_keys'
            svinfo.check(format=format)
        else:
            if svinfo.error: raise svinfo.error

            if args.list != None:
                if args.list == []: print(svinfo.getDump(args.absolute, args.json))
                else:
                    if args.json:
                        import json
                        paths = [ str(svinfo.getKey(key, args.absolute)) for key in args.list ]
                        print(json.dumps(paths))
                    else:
                        for key in args.list:
                            print(svinfo.getKey(key, args.absolute))

            elif args.get_completions != None:
                print("\n".join(svinfo.getCompletions(args.get_completions)))

            elif args.add :
                key, path = svinfo.do_add(args.add, args.absolute, args.force)
                svinfo.save()
                print("Raccourci '{} => {}' ajouté.".format(key, path))

            elif args.remove :
                for key in args.remove:
                    path = svinfo.getShortcutPath(key)
                    if svinfo.remove(key):
                        svinfo.save()
                        print("Raccourci '{} => {}' retiré.".format(key, path))

            elif args.search:
                keys = svinfo.searchForPath(args.search)
                if not keys:
                    raise(PysvError("Aucun raccourci trouvé pour ce dossier"))
                else:
                    print(','.join(keys))

            elif args.get_keys:
                if args.json:
                    import json
                    print(json.dumps(list(svinfo.getKeys())))
                else:
                    print('  '.join(svinfo.getKeys()))
            elif args.bs_dump:
                print(svinfo.getBashScriptDump(args))
                sys.exit(2)
            else:
                print(svinfo.getShortcutPath(args.keyword))

    except PysvError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

