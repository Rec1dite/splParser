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
        self.index = 0 # tok
        self.lookahead = None
    
    def nextToken(self):
        if self.lookahead is None:
            return self.tokens[self.index]

        self.index += 1
        return self.tokens[self.index]
    
    def match(self, token):
        if self.lookahead == token:
            self.nextToken()
        else:
            raise Exception("Syntax error: expected " + token + " but got " + self.lookahead)

    def parseExpr(self):
        pass

def outputXML(ast, file):
    outFile = file.replace("inputs", "outputs")
    outFile = outFile[:-4] + ".xml"

    xml = unparse(ast, pretty=True)
    open(outFile, "w").write(xml)

main("inputs")