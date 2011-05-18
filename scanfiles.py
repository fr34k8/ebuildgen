import os
import glob
from ply import lex
from ply import yacc

def scandir(dir, filetypes):
    files = []
    dirs = [f for f in os.listdir(dir)
        if os.path.isdir(os.path.join(dir, f))]
    for dir_path in dirs:
        files += scandir(dir + "/" + dir_path, filetypes)
    for filetype in filetypes:
        files += glob.glob(dir + "/*" + filetype)
    return files

#print(scandir("/home/zed/Desktop/test/smw/", ".cpp"))

#lex stuff begins here

def scanincludes(string,global_hfiles,local_hfiles):
    tokens = (
            "INCLUDE",
            "GLOBH",
            "LOCALH",
            "BUNDLEINC"
            )

    t_ignore = " \t"

    def t_comment(t):
        r'(/\*(.|\n)*\*/)|(//.*)'
        pass

    def t_INCLUDE(t):
        r"\#[Ii][Nn][Cc][Ll][Uu][Dd][Ee]"
        return t

    def t_GLOBH(t):
        r"<.*\.h>"
        t.value = t.value[1:-1] #strip <>
        return t

    def t_LOCALH(t):
        r"\".*\.h\""
        t.value = t.value[1:-1] #strip ""
        return t

    def t_BUNDLEINC(t): #for <string> etc.
        r"<.*>"
        return t

    def t_error(t):
        #print("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)

    lexer = lex.lex()

    #lexer.input(input_string)
    #
    #for tok in lexer:
    #    print(tok)
    #
    #YACC stuff here

    def p_includes2(p):
        """
        includes : includes ginc
                 | includes linc
        """

    def p_includes(p):
        """
        includes : ginc
                 | linc
        """

    def p_ginclude(p):
        "ginc : INCLUDE GLOBH"
        global_hfiles.add(p[2])

    def p_linclide(p):
        "linc : INCLUDE LOCALH"
        local_hfiles.add(p[2])

    def p_error(p):
        #print("syntax error at '%s'" % p.value)
        pass

    yacc.yacc()

    yacc.parse(string)
    return(global_hfiles,local_hfiles)


def startscan(dir,filetypes):
    global_hfiles = set()
    local_hfiles = set()

    for file in scandir(dir, filetypes):
        #print(file)

        with open(file, encoding="utf-8", errors="replace") as inputfile:
            (global_hfiles,local_hfiles) = scanincludes(inputfile.read(),global_hfiles,local_hfiles)

    return(global_hfiles,local_hfiles)

