# pylint: disable-all
import os
import sys
from lex import tokenize
from scop import scope
from prin import outputScopeTableHTML
from transl import translate
from json import dumps
from xmltodict import unparse
import re

def parseFolder(folder):
    print("\n\033[93m" + "_____ PARSING FOLDER [" + folder + "] " + "_"*(33-len(folder)) + "\033[0m")

    files = sorted(os.listdir(folder))
    for file in files:
        if file.endswith(".txt") or file.endswith(".spl"):
            # try:
                print("\n\n\033[94m" + "===== " + file + " " + "=" * (50-len(file)) + "\033[0m")
                parse(folder + os.sep + file)
            # except Exception as e:
                # print("\033[91m" + "PARSING ERROR\n> ", e, "\033[0m")

def parseFile(file):
    # try:
        print("=" * 25 + " \033[94m" + file + "\033[0m " + "=" * 25)
        parse(file)
        print("=" * (50 + len(file)))
    # except Exception as e:
        # print("\033[91m", "PARSING ERROR\n> ", e, "\033[0m")


# Top-down recursive-descent parser (LL(1))
def parse(file):
    text = open(file, "r").read()
    text = removeWhitespace(text)

    print("INPUT " + file + ":")
    print(text + "\n")

    tokens = tokenize(text)

    #===== PARSE =====#
    parser = Parser(tokens)
    ast = parser.woodooMagic()

    print("\033[92m", "PARSING SUCCESS", "\033[0m")
    prune(ast)

    outputJSON(ast, file)

    # xmlAST = convertASTForXML(ast)
    # outputXML({"PROGR": xmlAST}, file)

    #===== DEDUCE SCOPE TABLE =====#
    # tbl = scope(ast)
    # outputScopeTableHTML(tbl, file)

    # outputJSON(tbl, file)

    #===== TRANSLATE TO BASIC =====#
    basic = translate(ast)
    outputBasic(basic, file)


def prune(node):
    pruneDigitsDecnum(node)
    pruneProc(node)
    pruneVars(node)
    pruneCall(node)

def pruneDigitsDecnum(node):
    for child in node["children"]:
        if child["name"] in ["DIGITS", "DECNUM"]:
            val = pruneDigits(child)
            child["children"] = []
            child["value"] = val

        else:
            pruneDigitsDecnum(child)

def pruneProc(node):
    for child in node["children"]:
        if child["name"] == "PROC":
            # Extract proc name
            child["value"] = "p" + getNodePart(child, "DIGITS")["value"]
            # Remove proc name
            child["children"] = child["children"][2:]

        # Procs have subprocs
        pruneProc(child)

def pruneVars(node):
    for child in node["children"]:
        if child["name"] in ["NUMVAR", "BOOLVAR", "STRINGV"]:
            # Extract var name
            child["value"] = child["children"][0]["value"] + getNodePart(child, "DIGITS")["value"]
            # Remove var name tokens
            child["children"] = []

        # Procs have subprocs
        pruneVars(child)

def pruneCall(node):
    for child in node["children"]:
        if child["name"] == "CALL":
            # Extract proc name
            child["value"] = "p" + getNodePart(child, "DIGITS")["value"]
            child["children"] = []

        else:
            pruneCall(child)

def getNodePart(node, part):
    for child in node["children"]:
        if child["name"] == part:
            return child
    return None

def pruneDigits(node):
    res = node["value"]
    for child in node["children"]:
        res += pruneDigits(child)
    return res

# Smart whitespace remove
# Ignore whitespace in strings and comments
def removeWhitespace(text):
    newText = ""

    inString = False
    inComment = False
    for c in text:
        if c == "\"" and not inComment:
            inString = not inString
        if c == "*" and not inString:
            inComment = not inComment

        if inString or inComment or not str(c).isspace(): # TODO: Fix for ASCII > 32
            # print(c + " " + str(inString) + " " + str(inComment))
            newText += c
    
    return newText

class Parser:

    def __init__(self, tokens):
        self.tokens = tokens
        self.index = 0
        self.counter = 0
        self.ast = None

    def woodooMagic(self):
        self.ast = self.progr_()
        return self.ast
    
    def currentToken(self):
        return self.tokens[self.index]
    
    # Test for equality of current token
    def match(self, token):
        # print(">" + token)
        if self.index >= len(self.tokens):
            raise Exception("Syntax error: unexpected EOF")

        elif self.currentToken() == token:
            self.index += 1

        else:
            raise Exception("Syntax error: unexpected " + self.currentToken() + ", expected " + token)

    def tNode(self, token):
        id = str(self.counter)
        self.counter += 1
        return {"name": "term", "id": id, "children": [], "value": token}
    
    def nNode(self, name: str, children):
        id = str(self.counter)
        self.counter += 1
        res = {
            "name": name,
            "id": id,
            "children": children,
            "value": ""
        }
        return res

    # Used to check if the token is a string / comment
    def checkWrappedToken(self, token, wrapper, length=17):
        return token.startswith(wrapper) and self.currentToken().endswith(wrapper) and len(self.currentToken()) == length

    #=============== GRAMMAR ===============#
    # Each of these returns a tree node

    def progr_(self):
        if self.currentToken() in ["h", "g", "c", "w", "i", "r", "o", "n", "b", "s"]: # FIRST(PROGR)
            # PROGR -> ALGO PROCDEFS
            nodes = []

            nodes.append(self.algo_())

            nodes.append(self.procdefs_())

            return self.nNode("PROG", nodes)
        
        else:
            raise Exception("Syntax error: unexpected " + self.currentToken() + ", expected h, g, c, w, i, r, o, n, b or s")

    def procdefs_(self):
        if self.currentToken() == ",": # FIRST(PROCDEFS)
            # PROCDEFS -> , PROC PROCDEFS
            nodes = []

            self.match(",")
            nodes.append(self.tNode(","))

            nodes.append(self.proc_())

            nodes.append(self.procdefs_())

            return self.nNode("PROCDEFS", nodes)
        
        elif self.currentToken() in ["$", "}"]: # FOLLOW(PROCDEFS)
            # PROCDEFS -> epsilon

            # return None
            return self.nNode("PROCDEFS", [])
        
        else:
            raise Exception("Syntax error: unexpected " + self.currentToken() + ", expected p or $")

    def proc_(self):
        if self.currentToken() == "p": # FIRST(PROC)
            # PROC -> p DIGITS { PROGR }
            nodes = []

            self.match("p")
            nodes.append(self.tNode("p"))

            nodes.append(self.digits_())

            self.match("{")
            nodes.append(self.tNode("{"))

            nodes.append(self.progr_())

            self.match("}")
            nodes.append(self.tNode("}"))

            return self.nNode("PROC", nodes)
        
        else:
            raise Exception("Syntax error: unexpected " + self.currentToken() + ", expected p")

    def digits_(self):
        if self.currentToken() in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]: # FIRST(DIGITS)
            # DIGITS -> D MORE
            nodes = []

            nodes.append(self.d_())

            nodes.append(self.more_())

            return self.nNode("DIGITS", nodes)
        
        else:
            raise Exception("Syntax error: unexpected " + self.currentToken() + ", expected 0-9")

    def d_(self):
        if self.currentToken() in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]: # FIRST(D)
            # D -> 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9

            node = self.tNode(self.currentToken())
            self.match(self.currentToken())

            return node

            # self.match(self.currentToken())
            # nodes.append(self.tNode(self.currentToken()))

            # return self.nNode("D", nodes)

        
        else:
            raise Exception("Syntax error: unexpected " + self.currentToken() + ", expected 0-9")

    def more_(self):
        if self.currentToken() in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]: # FIRST(MORE)
            # MORE -> DIGITS
            nodes = []

            nodes.append(self.digits_())

            return self.nNode("MORE", nodes)
        
        elif self.currentToken() in ["{", ".", ",", ";", ":=", "}", "$", ")"] or self.checkWrappedToken(self.currentToken(), "*"): # FOLLOW(MORE)
            # MORE -> epsilon

            return self.nNode("MORE", [])
            # return None
        
        else:
            raise Exception("Syntax error: unexpected " + self.currentToken() + ", expected 0-9, {, ., ,, ;, *, :=, }, $ or )")

    def algo_(self):
        if self.currentToken() in ["h", "g", "c", "w", "i", "r", "o", "n", "b", "s"]: # FIRST(ALGO)
            # ALGO -> INSTR COMMENT SEQ
            nodes = []

            nodes.append(self.instr_())

            nodes.append(self.comment_())

            nodes.append(self.seq_())

            return self.nNode("ALGO", nodes)
        
        else:
            raise Exception("Syntax error: unexpected " + self.currentToken() + ", expected h, g, c, w, i, r, o, n, b or s")

    def seq_(self):
        if self.currentToken() in [";"]: # FIRST(SEQ)
            # SEQ -> ; ALGO
            nodes = []

            self.match(";")
            nodes.append(self.tNode(";"))

            nodes.append(self.algo_())

            return self.nNode("SEQ", nodes)
        
        elif self.currentToken() in [",", "}", "$"]: # FOLLOW(SEQ)
            # SEQ -> epsilon

            # return None
            return self.nNode("SEQ", [])
        
        else:
            raise Exception("Syntax error: unexpected " + self.currentToken() + ", expected ;, , or }")

    def instr_(self):
        if self.currentToken() in ["g"]: # FIRST(INSTR)
            # INSTR -> INPUT
            nodes = []

            nodes.append(self.input_())

            return self.nNode("INSTR", nodes)
        
        elif self.currentToken() in ["o", "r"]: # FIRST(INSTR)
            # INSTR -> OUTPUT
            nodes = []

            nodes.append(self.output_())

            return self.nNode("INSTR", nodes)
        
        elif self.currentToken() in ["n", "b", "s"]: # FIRST(INSTR)
            # INSTR -> ASSIGN
            nodes = []

            nodes.append(self.assign_())

            return self.nNode("INSTR", nodes)
        
        elif self.currentToken() in ["c"]: # FIRST(INSTR)
            # INSTR -> CALL
            nodes = []

            nodes.append(self.call_())

            return self.nNode("INSTR", nodes)
        
        elif self.currentToken() in ["w"]: # FIRST(INSTR)
            # INSTR -> LOOP
            nodes = []

            nodes.append(self.loop_())

            return self.nNode("INSTR", nodes)
        
        elif self.currentToken() in ["i"]: # FIRST(INSTR)
            # INSTR -> BRANCH
            nodes = []

            nodes.append(self.branch_())

            return self.nNode("INSTR", nodes)
        
        elif self.currentToken() in ["h"]: # FIRST(INSTR)
            # INSTR -> h
            nodes = []

            self.match("h")
            nodes.append(self.tNode("h"))

            return self.nNode("INSTR", nodes)
        
        else:
            raise Exception("Syntax error: unexpected " + self.currentToken() + ", expected g, o, r, n, b, s, c, w, i or h")

    def call_(self):
        if self.currentToken() == "c": # FIRST(CALL)
            # CALL -> c p DIGITS
            nodes = []

            self.match("c")
            nodes.append(self.tNode("c"))

            self.match("p")
            nodes.append(self.tNode("p"))

            nodes.append(self.digits_())

            return self.nNode("CALL", nodes)

        else:
            raise Exception("Syntax error: unexpected " + self.currentToken() + ", expected c")

    def assign_(self):
        if self.currentToken() in ["n"]: # FIRST(ASSIGN)
            # ASSIGN -> NUMVAR := NUMEXPR
            nodes = []

            nodes.append(self.numvar_())

            self.match(":=")
            nodes.append(self.tNode(":="))

            nodes.append(self.numexpr_())

            return self.nNode("ASSIGN", nodes)

        elif self.currentToken() in ["b"]: # FIRST(ASSIGN)
            # ASSIGN -> BOOLVAR := BOOLEXPR
            nodes = []

            nodes.append(self.boolvar_())

            self.match(":=")
            nodes.append(self.tNode(":="))

            nodes.append(self.boolexpr_())

            return self.nNode("ASSIGN", nodes)
        
        elif self.currentToken() in ["s"]: # FIRST(ASSIGN)
            # ASSIGN -> STRINGV := STRI
            nodes = []

            nodes.append(self.stringv_())

            self.match(":=")
            nodes.append(self.tNode(":="))

            nodes.append(self.stri_())

            return self.nNode("ASSIGN", nodes)
        
        else:
            raise Exception("Syntax error: unexpected " + self.currentToken() + ", expected n, b or s")

    def loop_(self):
        if self.currentToken() == "w": # FIRST(LOOP)
            # LOOP -> w ( BOOLEXPR ) { ALGO }
            nodes = []

            self.match("w")
            nodes.append(self.tNode("w"))

            self.match("(")
            nodes.append(self.tNode("("))

            nodes.append(self.boolexpr_())

            self.match(")")
            nodes.append(self.tNode(")"))

            self.match("{")
            nodes.append(self.tNode("{"))

            nodes.append(self.algo_())

            self.match("}")
            nodes.append(self.tNode("}"))

            return self.nNode("LOOP", nodes)
        
        else:
            raise Exception("Syntax error: unexpected " + self.currentToken() + ", expected w")

    def branch_(self):
        if self.currentToken() == "i": # FIRST(BRANCH)
            # BRANCH -> i ( BOOLEXPR ) t { ALGO } ELSE
            nodes = []

            self.match("i")
            nodes.append(self.tNode("i"))

            self.match("(")
            nodes.append(self.tNode("("))

            nodes.append(self.boolexpr_())

            self.match(")")
            nodes.append(self.tNode(")"))

            self.match("t")
            nodes.append(self.tNode("t"))

            self.match("{")
            nodes.append(self.tNode("{"))

            nodes.append(self.algo_())

            self.match("}")
            nodes.append(self.tNode("}"))

            nodes.append(self.else_())

            return self.nNode("BRANCH", nodes)
        
        else:
            raise Exception("Syntax error: unexpected " + self.currentToken() + ", expected i")

    def else_(self):
        if self.currentToken() == "e": # FIRST(ELSE)
            # ELSE -> e { ALGO }
            nodes = []

            self.match("e")
            nodes.append(self.tNode("e"))

            self.match("{")
            nodes.append(self.tNode("{"))

            nodes.append(self.algo_())

            self.match("}")
            nodes.append(self.tNode("}"))

            return self.nNode("ELSE", nodes)
    
        elif self.currentToken() in [",", ";", "}", "$"] or self.checkWrappedToken(self.currentToken(), "*"): # FOLLOW(ELSE)
            # ELSE -> epsilon

            # return None
            return self.nNode("ELSE", [])
        
        else:
            raise Exception("Syntax error: unexpected " + self.currentToken() + ", expected e, , or $")

    def numvar_(self):
        if self.currentToken() == "n": # FIRST(NUMVAR)
            # NUMVAR -> n DIGITS
            nodes = []

            self.match("n")
            nodes.append(self.tNode("n"))

            nodes.append(self.digits_())

            return self.nNode("NUMVAR", nodes)
        
        else:
            raise Exception("Syntax error: unexpected " + self.currentToken() + ", expected n")

    def boolvar_(self):
        if self.currentToken() == "b": # FIRST(BOOLVAR)
            # BOOLVAR -> b DIGITS
            nodes = []

            self.match("b")
            nodes.append(self.tNode("b"))

            nodes.append(self.digits_())

            return self.nNode("BOOLVAR", nodes)
        
        else:
            raise Exception("Syntax error: unexpected " + self.currentToken() + ", expected b")

    def stringv_(self):
        if self.currentToken() == "s": # FIRST(STRINGV)
            # STRINGV -> s DIGITS
            nodes = []

            self.match("s")
            nodes.append(self.tNode("s"))

            nodes.append(self.digits_())

            return self.nNode("STRINGV", nodes)
        
        else:
            raise Exception("Syntax error: unexpected " + self.currentToken() + ", expected s")

    def numexpr_(self):
        if self.currentToken() in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0.00", "-"]: # FIRST(NUMEXPR)
            # NUMEXPR -> DECNUM
            nodes = []

            nodes.append(self.decnum_())

            return self.nNode("NUMEXPR", nodes)

        elif self.currentToken() == "n": # FIRST(NUMEXPR)
            # NUMEXPR -> NUMVAR
            nodes = []

            nodes.append(self.numvar_())

            return self.nNode("NUMEXPR", nodes)

        elif self.currentToken() in ["a", "m", "d"]: # FIRST(NUMEXPR)
            # NUMEXPR -> a ( NUMEXPR , NUMEXPR )
            # NUMEXPR -> m ( NUMEXPR , NUMEXPR )
            # NUMEXPR -> d ( NUMEXPR , NUMEXPR )
            nodes = []

            tok = self.currentToken()

            self.match(tok)
            nodes.append(self.tNode(tok))

            self.match("(")
            nodes.append(self.tNode("("))

            nodes.append(self.numexpr_())

            self.match(",")
            nodes.append(self.tNode(","))

            nodes.append(self.numexpr_())

            self.match(")")
            nodes.append(self.tNode(")"))

            return self.nNode("NUMEXPR", nodes)

        else:
            raise Exception("Syntax error: unexpected " + self.currentToken() + ", expected 1, 2, 3, 4, 5, 6, 7, 8, 9, 0.00, -, n, a, m, or d")

    def decnum_(self):
        if self.currentToken() in ["1", "2", "3", "4", "5", "6", "7", "8", "9"]: # FIRST(DECNUM)
            # DECNUM -> POS
            nodes = []

            nodes.append(self.pos_())

            return self.nNode("DECNUM", nodes)

        elif self.currentToken() == "0.00": # FIRST(DECNUM)
            # DECNUM -> 0.00
            nodes = []

            self.match("0.00")
            nodes.append(self.tNode("0.00"))

            return self.nNode("DECNUM", nodes)

        elif self.currentToken() == "-": # FIRST(DECNUM)
            # DECNUM -> NEG
            nodes = []

            nodes.append(self.neg_())

            return self.nNode("DECNUM", nodes)
        
        else:
            raise Exception("Syntax error: unexpected " + self.currentToken() + ", expected 1, 2, 3, 4, 5, 6, 7, 8, 9, 0.00, or -")

    def neg_(self):
        if self.currentToken() == "-": # FIRST(NEG)
            # NEG -> - POS
            nodes = []

            self.match("-")
            nodes.append(self.tNode("-"))

            nodes.append(self.pos_())

            return self.nNode("NEG", nodes)
        
        else:
            raise Exception("Syntax error: unexpected " + self.currentToken() + ", expected -")

    def pos_(self):
        if self.currentToken() in ["1", "2", "3", "4", "5", "6", "7", "8", "9"]: # FIRST(POS)
            # POS -> INT . D D 
            nodes = []

            nodes.append(self.int_())

            self.match(".")
            nodes.append(self.tNode("."))

            nodes.append(self.d_())

            nodes.append(self.d_())

            return self.nNode("POS", nodes)

        else:
            raise Exception("Syntax error: unexpected " + self.currentToken() + ", expected 1, 2, 3, 4, 5, 6, 7, 8, or 9")

    def int_(self):
        if self.currentToken() in ["1", "2", "3", "4", "5", "6", "7", "8", "9"]: # FIRST(INT)
            # INT -> x MORE
            nodes = []

            v = self.currentToken()

            self.match(v)
            nodes.append(self.tNode(v))

            nodes.append(self.more_())

            return self.nNode("INT", nodes)

        else:
            raise Exception("Syntax error: unexpected " + self.currentToken() + ", expected 1, 2, 3, 4, 5, 6, 7, 8, or 9")

    def boolexpr_(self):
        if self.currentToken() in ["b", "T", "F", "^", "v", "!"]: # FIRST(BOOLEXPR)
            # BOOLEXPR -> LOGIC
            nodes = []

            nodes.append(self.logic_())

            return self.nNode("BOOLEXPR", nodes)
        
        elif self.currentToken() in ["E", "<", ">"]: # FIRST(BOOLEXPR)
            # BOOLEXPR -> CMPR
            nodes = []

            nodes.append(self.cmpr_())

            return self.nNode("BOOLEXPR", nodes)
        
        else:
            raise Exception("Syntax error: unexpected " + self.currentToken() + ", expected b, T, F, ^, v, !, E, <, or >")

    def logic_(self):
        if self.currentToken() == "b": # FIRST(LOGIC)
            # LOGIC -> BOOLVAR
            nodes = []

            nodes.append(self.boolvar_())

            return self.nNode("LOGIC", nodes)

        elif self.currentToken() in ["T", "F"]: # FIRST(LOGIC)
            # LOGIC -> T | F
            nodes = []

            v = self.currentToken()
            self.match(v)
            nodes.append(self.tNode(v))

            return self.nNode("LOGIC", nodes)
        
        elif self.currentToken() in ["^", "v"]: # FIRST(LOGIC)
            # LOGIC ::= ^ ( BOOLEXPR , BOOLEXPR )
            # LOGIC ::= v ( BOOLEXPR , BOOLEXPR )
            nodes = []

            f = self.currentToken()
            self.match(f)
            nodes.append(self.tNode(f))

            self.match("(")
            nodes.append(self.tNode("("))

            nodes.append(self.boolexpr_())

            self.match(",")
            nodes.append(self.tNode(","))

            nodes.append(self.boolexpr_())

            self.match(")")
            nodes.append(self.tNode(")"))

            return self.nNode("LOGIC", nodes)

        elif self.currentToken() == "!": # FIRST(LOGIC)
            # LOGIC ::= ! ( BOOLEXPR )
            nodes = []

            self.match("!")
            nodes.append(self.tNode("!"))

            self.match("(")
            nodes.append(self.tNode("("))

            nodes.append(self.boolexpr_())

            self.match(")")
            nodes.append(self.tNode(")"))

            return self.nNode("LOGIC", nodes)
        
        else:
            raise Exception("Syntax error: unexpected " + self.currentToken() + ", expected b, T, F, ^, v, !, E, <, or >")

    def cmpr_(self):
        if self.currentToken() in ["E", "<", ">"]: # FIRST(CMPR)
            # CMPR ::= E ( NUMEXPR , NUMEXPR )
            # CMPR ::= < ( NUMEXPR , NUMEXPR )
            # CMPR ::= > ( NUMEXPR , NUMEXPR )
            nodes = []

            r = self.currentToken()
            self.match(r)
            nodes.append(self.tNode(r))

            self.match("(")
            nodes.append(self.tNode("("))

            nodes.append(self.numexpr_())

            self.match(",")
            nodes.append(self.tNode(","))

            nodes.append(self.numexpr_())

            self.match(")")
            nodes.append(self.tNode(")"))

            return self.nNode("CMPR", nodes)

    def stri_(self):
        if self.checkWrappedToken(self.currentToken(), "\""): # FIRST(STRI)
            # STRI -> " C C C C C C C C C C C C C C C "
            nodes = []

            v = self.currentToken()

            for i, c in enumerate(v):
                if i != 0 and i != len(v)-1:

                    # Check valid ASCII character
                    if ord(c) < 32 or ord(c) >= 127 or c == "\"":
                        raise Exception("Syntax error: invalid ASCII character " + self.currentToken() + " in string")

            self.match(v)
            nodes.append(self.tNode(v))

            return self.nNode("STRI", nodes)

        else:
            raise Exception("Syntax error: unexpected " + self.currentToken() + ", expected \"")

    def c_(self):
        if len(self.currentToken()) == 1 and ord(self.currentToken()) >= 32 and ord(self.currentToken()) < 127: # FIRST(C)
            # C -> x
            nodes = []

            v = self.currentToken()

            self.match(v)
            nodes.append(self.tNode(v))

            return self.nNode("C", nodes)
        
        else:
            raise Exception("Syntax error: unexpected " + self.currentToken() + ", expected an ASCII character in range [32, 126]")

    def comment_(self):
        if self.checkWrappedToken(self.currentToken(), "*"): # FIRST(COMMENT)
            # COMMENT -> * C C C C C C C C C C C C C C C *
            nodes = []

            v = self.currentToken()

            for i, c in enumerate(v):
                if i != 0 and i != len(v)-1:

                    # Check valid ASCII character
                    if ord(c) < 32 or ord(c) >= 127 or c == "*":
                        raise Exception("Syntax error: invalid ASCII character " + self.currentToken() + " in comment")

            self.match(v)
            nodes.append(self.tNode(v))

            return self.nNode("COMMENT", nodes)

        elif self.currentToken() in ["$", ",", "}", ";"]: # FIRST(COMMENT)
            # COMMENT -> epsilon

            # return None
            return self.nNode("COMMENT", [])
        
        else:
            raise Exception("Syntax error: unexpected " + self.currentToken() + ", expected *, $, ,, }, or ;")

    def input_(self):
        if self.currentToken() == "g": # FIRST(INPUT)
            # INPUT -> g NUMVAR
            nodes = []

            self.match("g")
            nodes.append(self.tNode("g"))

            nodes.append(self.numvar_())

            return self.nNode("INPUT", nodes)
        
        else:
            raise Exception("Syntax error: unexpected " + self.currentToken() + ", expected g")


    def output_(self):
        if self.currentToken() == "o": # FIRST(OUTPUT)
            # OUTPUT -> VALUE
            nodes = []

            nodes.append(self.value_())

            return self.nNode("OUTPUT", nodes)
        
        elif self.currentToken() == "r": # FIRST(OUTPUT)
            # OUTPUT -> TEXT
            nodes = []

            nodes.append(self.text_())

            return self.nNode("OUTPUT", nodes)
        
        else:
            raise Exception("Syntax error: unexpected " + self.currentToken() + ", expected o or r")

    def value_(self):
        if self.currentToken() == "o": # FIRST(VALUE)
            # VALUE -> o NUMVAR
            nodes = []

            self.match("o")
            nodes.append(self.tNode("o"))

            nodes.append(self.numvar_())

            return self.nNode("VALUE", nodes)
        
        else:
            raise Exception("Syntax error: unexpected " + self.currentToken() + ", expected o")

    def text_(self):
        if self.currentToken() == "r": # FIRST(TEXT)
            # TEXT -> r STRINGV
            nodes = []

            self.match("r")
            nodes.append(self.tNode("r"))

            nodes.append(self.stringv_())

            return self.nNode("TEXT", nodes)
        
        else:
            raise Exception("Syntax error: unexpected " + self.currentToken() + ", expected r")


# Converts the parent-child AST to the correct AST format for XML output
def convertASTForXML(inputAST):
    def traverse(node):
        # if "name" not in node:
            # node["name"] = "root"
        name_tag = f"{node['name']}-{node['id']}"
        children_ids = ','.join(child['id'] for child in node['children'])

        output_node = {
            '@id': node['id'],
            '@children': children_ids,
            '#text': node['value'],
        }

        for child in node['children']:
            child_output = traverse(child)
            child_tag = f"{child['name']}-{child['id']}"
            output_node[child_tag] = child_output

        return output_node

    return traverse(inputAST)

def outputBasic(basic, file):
    if not os.path.exists("outputs"):
        os.makedirs("outputs")

    outFile = file

    if outFile.startswith("inputs" + os.sep):
        outFile = "outputs" + os.sep + outFile[7:]

    dotIndex = outFile.rfind(".")

    if dotIndex != -1:
        outFile = outFile[:dotIndex] + ".b"
    else:
        outFile += ".json"

    open(outFile, "w").write(basic)

def outputJSON(ast, file):
    if not os.path.exists("outputs"):
        os.makedirs("outputs")

    outFile = file

    if outFile.startswith("inputs" + os.sep):
        outFile = "outputs" + os.sep + outFile[7:]


    dotIndex = outFile.rfind(".")

    if dotIndex != -1:
        outFile = outFile[:dotIndex] + ".json"
    else:
        outFile += ".json"

    json = dumps(ast, indent=2)
    open(outFile, "w").write(json)

def outputXML(ast, file):
    if not os.path.exists("outputs"):
        os.makedirs("outputs")

    outFile = file

    # If file is in the inputs folder, move it to the outputs folder
    # All other output files will be left in place
    if outFile.startswith("inputs" + os.sep):
        outFile = "outputs" + os.sep + outFile[7:]

    dotIndex = outFile.rfind(".")

    if dotIndex != -1:
        outFile = outFile[:dotIndex] + ".xml"
    else:
        outFile += ".xml"

    xml = unparse(ast, pretty=True)

    # Remove ids in tagnames
    clean_xml = ""

    for line in xml.splitlines():
        matches = re.finditer(r"<\/?[a-zA-Z]+(-\d+)", line)
        for match in matches:
            cap = match.group(1)
            line = line.replace(cap, "")
        
        clean_xml += line + "\n"

    open(outFile, "w").write(clean_xml)
    print("> XML OUTPUT: \033[93m" + outFile + "\033[0m")

def printHelp():
    print("""
    Usage: python3 pars.py [OPTION] [FILE]

    OPTIONS:
        -h      Print this help message
        -f      Parse a single file
    
    If no option is specified, the program will try to parse all files in the "inputs" folder.
    Input from the inputs/ folder will have their outputs placed in the "outputs" folder.

    Explicitly specified output files will be placed in the same folder as the input file.
    """)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        match sys.argv[1]:
            case "-f":
                if len(sys.argv) > 2:
                    parseFile(sys.argv[2])
                else:
                    print("\033[91mNo file specified!\033[0m")
                    printHelp()

            case "-h":
                printHelp()
            
            case _:
                print("\033[91mInvalid command option!\033[0m")
                printHelp()

    else:
        parseFolder("inputs")