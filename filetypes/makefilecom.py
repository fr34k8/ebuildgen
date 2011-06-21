from ply import lex
from ply import yacc

def expand(lst,variables):
    newlst = []
    for item in lst:
        if isinstance(item, list):
            strlst = com_interp(item[0],variables)
            newlst += expand(strlst,variables)
        else:
            newlst.append(item)

    return newlst

def com_interp(string,variables):
    tokens = (
            "COMMAND",
            "COMMA",
            "COL",
            "EQ",
            "TEXT",
            "PERCENT",
            "BEGINCOM",
            "ENDCOM",
            "SPACE",
            )
    states = (
            ("ccode", "exclusive"), #command code
            ("eval", "exclusive"), #code to evaluate
            )

    # Match the first $(. Enter ccode state.
    def t_eval_ccode(t):
        r'\$(\{|\()'
        t.lexer.code_start = t.lexer.lexpos        # Record the starting position
        t.lexer.level = 1                          # Initial level
        t.lexer.push_state('ccode')                # Enter 'ccode' state

    # Rules for the ccode state
    def t_ccode_newcom(t):
        r'\$(\{|\()'
        t.lexer.level +=1

    def t_ccode_endcom(t):
        r'(\}|\))'
        t.lexer.level -=1

        # If closing command, return the code fragment
        if t.lexer.level == 0:
             t.value = t.lexer.lexdata[t.lexer.code_start-1:t.lexer.lexpos]
             t.type = "COMMAND"
             t.lexer.pop_state()
             return t

    def t_ccode_text(t):
        r"[^\$\(\{\)\}]"

    def t_BEGINCOM(t):
        r"(\(|\{)"
        t.lexer.begin("eval")
        return t

    def t_eval_ENDCOM(t):
        r"(\)|\})"
        t.lexer.begin("INITIAL")
        return t

    def t_eval_PERCENT(t):
        r"\%"
        return t

    def t_eval_EQ(t):
        r"="
        return t

    def t_eval_COMMA(t):
        r","
        return t

    def t_eval_COL(t):
        r":"
        return t

    def t_eval_TEXT(t):
        r"[^ \n\t:=\)\}\(\}\\\$,]+"
        return t

    def t_TEXT(t):
        r"[^ \\t$\(\{]"
        return t

    def t_eval_SPACE(t):
        r"[ \t]"
        return t

    def t_ANY_error(t):
        print("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)

    lexer = lex.lex()

    #lexer.input(string)
    #for tok in lexer:
    #    print(tok)


    #YACC stuff begins here

    def p_comp(p):
        """
        complst : BEGINCOM newstr ENDCOM
                | func
        """
        if len(p) == 4:
            p[0] = p[2]
        else:
            p[0] = p[1]

    def p_complst(p):
        """
        complst : complst BEGINCOM textstr ENDCOM
                | BEGINCOM textstr ENDCOM
                | complst textstr
                | textstr
        """
        if len(p) == 4:
            p[0] = expand(variables[p[2]],variables)
        elif len(p) == 5:
            p[0] = [p[1][0] + expand(variables[p[3]],variables)[0]]
        elif len(p) == 3:
            p[0] = [p[1][0] + p[2]]
        else:
            p[0] = [p[1]]

    def p_tonewstr(p):
        """
        newstr  : getstr EQ textstr PERCENT textstr
                | getstr EQ PERCENT textstr
                | getstr EQ textstr PERCENT
                | getstr EQ PERCENT
                | getstr EQ textstr
        """
        newtextlist = []
        if p[1] == []:
            p[0] = p[1]
        elif len(p) == 6:
            for text in p[1]:
                newtextlist.append(p[3] + text + p[5])
            p[0] = newtextlist

        elif len(p) == 5:
            if p[3] == "%":
                for text in p[1]:
                    newtextlist.append(text + p[4])
                p[0] = newtextlist
            else:
                for text in p[1]:
                    newtextlist.append(p[3] + text)
                p[0] = newtextlist

        elif p[3] == "%":
            p[0] = p[1]
        else:
            for text in p[1]:
                newtextlist.append(text + p[3])
            p[0] = newtextlist


    def p_getstr(p):
        """
        getstr : textstr COL textstr PERCENT textstr
               | textstr COL PERCENT textstr
               | textstr COL textstr PERCENT
               | textstr COL PERCENT
               | textstr COL textstr
        """
        if not p[1] in variables:
            p[0] = []
        else:
            textlst = expand(variables[p[1]],variables) #make sure it's expanded
            newtextlst = []

            if len(p) == 6:
                l1 = len(p[3]) #length of str1
                l2 = len(p[5])
                for text in textlst:
                    if p[3] == text[0:l1] and p[5] == text[-l2:]:
                        newtextlst.append(text[l1:-l2])

                p[0] = newtextlst

            elif len(p) == 5:
                if p[3] == "%":
                    l1 = len(p[4])
                    for text in textlst:
                        if p[4] == text[-l1:]:
                            newtextlst.append(text[:-l1])

                    p[0] = newtextlst
                else:
                    l1 = len(p[3])
                    for text in textlst:
                        if p[3] == text[0:l1]:
                            newtextlst.append(text[l1:])

                    p[0] = newtextlst
            elif p[3] == "%":
                p[0] = textlst
            else:
                l1 = len(p[3])
                for text in textlst:
                    if p[3] == text[-l1:]:
                        newtextlst.append(text[:-l1])

                p[0] = newtextlst

    def p_func(p):
        """
        func : BEGINCOM textstr SPACE funcinput
        """
        result = ["This calls a function"]
        #result = funcexe(p[2],p[4])
        p[0] = result

    def p_funcinput(p):
        """
        funcinput : funcinput inputstr COMMA
                  | funcinput inputstr ENDCOM
                  | inputstr COMMA
                  | inputstr ENDCOM
        """
        if len(p) == 4:
            p[0] = p[1].append(p[2])
        else:
            p[0] = [p[1]]

    def p_inputstr(p):
        """
        inputstr : inputstr spacestr
                 | inputstr textstr
                 | spacestr
                 | textstr
        """
        if len(p) == 3:
            p[0] = p[1] + p[2]
        else:
            p[0] = p[1]

    def p_command(p):
        """
        textstr : textstr COMMAND
                | COMMAND
        """
        if len(p) == 3:
            p[0] = p[1] + com_interp(p[2],variables)[0]
        else:
            p[0] = com_interp(p[1],variables)[0]

    def p_textstr(p):
        """
        textstr : textstr TEXT
                | TEXT
        """
        if len(p) == 3:
            p[0] = p[1] + p[2]
        else:
            p[0] = p[1]

    def p_spacestr(p):
        """
        spacestr : spacestr SPACE
                 | SPACE
        """
        if len(p) == 3:
            p[0] = p[1] + p[2]
        else:
            p[0] = p[1]

    def p_error(p):
        print("syntax error at '%s'" % p.type,p.lexpos)
        pass

    yacc.yacc()

    retlst = yacc.parse(string)

    #print(retlst)

    return retlst

#print(com_interp("(SRC:.c=.o)",{"x":["y"], "y":["z"], "z":["u"],'SRC': [['(wildcard src/*.c)']]}))
