import os
from lex import tokenize
from json import dumps
from xmltodict import unparse

def main(folder):
    for file in os.listdir(folder):
        parse(folder + "/" + file)


# Top-down recursive-descent parser (LL(1))
def parse(file):
    text = open(file, "r").read()
    text = removeWhitespace(text)

    print("INPUT " + file + ":")
    print(text + "\n")

    tokens = tokenize(text)

    print(dumps(tokens))

    parser = Parser(text)
    # parser.woodoomagic()

    # ast = parse()
    # outputXML(ast, file)

# Smart whitespace remove
# Ignore whitespace in strings and comments
def removeWhitespace(text):
    newText = ""

    inString = False
    inComment = False
    for c in text:
        if c == "\"":
            inString = not inString
        if c == "*":
            inComment = not inComment

        if inString or inComment or not str(c).isspace(): # TODO: Fix for ASCII > 32
            newText += c
    
    return newText

class Parser:

    def __init__(self, tokens):
        self.tokens = tokens
        self.index = 0
        self.ast = None
    
    def currentToken(self):
        return self.tokens[self.index]
    
    # Test for equality of current token
    def match(self, token):
        if self.index >= len(self.tokens):
            raise Exception("Syntax error: unexpected EOF")

        elif self.currToken() == token:
            self.index += 1

        else:
            raise Exception("Syntax error: unexpected " + self.currToken() + ", expected " + token)

    def tNode(self, token):
        return { "token": token }
    
    def nNode(self, name, children):
        return { name: children }

    #=============== GRAMMAR ===============#
    # Each of these returns a tree node

    def progr_(self):
        if self.currentToken() in ["h", "g", "c", "w", "i", "r", "o", "n", "b", "s"]:
            # ALGO PROCDEFS

            tree1 = algo_()
            tree2 = procdefs_()

            tree = { "PROGR": self.currentToken() }

    def procdefs_(self): pass
    def proc_(self): pass
    def digits_(self): pass
    def d_(self): pass
    def more_(self): pass
    def algo_(self): pass
    def seq_(self): pass
    def instr_(self): pass

    def call_(self):
        if self.currentToken() == "c":
            nodes = []

            self.match("c")
            nodes.append(self.tNode("c"))

            self.match("p")
            nodes.append(self.tNode("p"))

            nodes.append(self.digits_())

            return self.nNode("CALL", nodes)

        else:
            raise Exception("Syntax error: unexpected " + self.currentToken() + ", expected c")

    def assign_(self): pass
    def loop_(self): pass
    def branch_(self): pass
    def else_(self): pass
    def numvar_(self): pass
    def boolvar_(self): pass
    def stringv_(self): pass
    def numexpr_(self): pass
    def decnum_(self): pass
    def neg_(self): pass
    def pos_(self): pass
    def int_(self): pass
    def boolexpr_(self): pass
    def logic_(self): pass
    def cmpr_(self): pass
    def stri_(self): pass
    def c_(self): pass
    def comment_(self): pass
    def input_(self): pass
    def output_(self): pass
    def value_(self): pass

    def text_(self):
        if self.currentToken() ==


def outputXML(ast, file):
    outFile = file.replace("inputs", "outputs")
    outFile = outFile[:-4] + ".xml"

    xml = unparse(ast, pretty=True)
    open(outFile, "w").write(xml)

main("inputs")


# PROGR ::= ALGO PROCDEFS
# PROCDEFS ::= , PROC PROCDEFS
# PROCDEFS ::= ''
# PROC ::= p DIGITS { PROGR }
# DIGITS ::= D MORE
# D ::= 0
# D ::= 1
# D ::= 2
# D ::= 3
# D ::= 4
# D ::= 5
# D ::= 6
# D ::= 7
# D ::= 8
# D ::= 9
# MORE ::= DIGITS
# MORE ::= ''
# ALGO ::= INSTR COMMENT SEQ
# SEQ ::= ; ALGO
# SEQ ::= ''
# INSTR ::= INPUT
# INSTR ::= OUTPUT
# INSTR ::= ASSIGN
# INSTR ::= CALL
# INSTR ::= LOOP
# INSTR ::= BRANCH
# INSTR ::= h
# CALL ::= c p DIGITS
# ASSIGN ::= NUMVAR := NUMEXPR 
# ASSIGN ::= BOOLVAR := BOOLEXPR
# ASSIGN ::= STRINGV := STRI
# LOOP ::= w ( BOOLEXPR ) { ALGO } 
# BRANCH ::= i ( BOOLEXPR ) t { ALGO } ELSE
# ELSE ::= e { ALGO }
# ELSE ::= ''
# NUMVAR ::= n DIGITS
# BOOLVAR ::= b DIGITS
# STRINGV ::= s DIGITS
# NUMEXPR ::= a ( NUMEXPR , NUMEXPR )
# NUMEXPR ::= m ( NUMEXPR , NUMEXPR )
# NUMEXPR ::= d ( NUMEXPR , NUMEXPR )
# NUMEXPR ::= NUMVAR
# NUMEXPR ::= DECNUM
# DECNUM ::= 0.00
# DECNUM ::= NEG
# DECNUM ::= POS
# NEG ::= ‒ POS
# POS ::= INT . D D
# INT ::= 1 MORE
# INT ::= 2 MORE
# INT ::= 3 MORE
# INT ::= 4 MORE
# INT ::= 5 MORE
# INT ::= 6 MORE
# INT ::= 7 MORE
# INT ::= 8 MORE
# INT ::= 9 MORE
# BOOLEXPR ::= LOGIC
# BOOLEXPR ::= CMPR
# LOGIC ::= BOOLVAR
# LOGIC ::= T
# LOGIC ::= F
# LOGIC ::= ^ ( BOOLEXPR , BOOLEXPR )
# LOGIC ::= v ( BOOLEXPR , BOOLEXPR )
# LOGIC ::= ! ( BOOLEXPR )
# CMPR ::= E ( NUMEXPR , NUMEXPR )
# CMPR ::= < ( NUMEXPR , NUMEXPR )
# CMPR ::= > ( NUMEXPR , NUMEXPR )
# STRI ::= " C C C C C C C C C C C C C C C "
# C ::= as
# COMMENT ::= * C C C C C C C C C C C C C C C *
# COMMENT ::= ''
# INPUT ::= g NUMVAR
# OUTPUT ::= TEXT
# OUTPUT ::= VALUE
# VALUE ::= o NUMVAR
# TEXT ::= r STRINGV