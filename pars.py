import os
from lex import tokenize
from xmltodict import unparse

def main(folder):
    for file in os.listdir(folder):
        parse(folder + "/" + file)


def parse(file):
    text = open(file, "r").read()
    tokens = tokenize(text)

    ast = parseTokens(tokens)
    outputXML(ast, "asdf.txt")

# Top-down recursive-descent parser (LL(1))
def parseTokens(tokens):
    return {
    'PROG': {
        '@id': '1',
        '@children': '2,3',

        'ALGO': {
            '@id': '2',
            '@children': '4,5,6'
        },

        'PROCDEFS': {
            '@id': '3',
            '@children': ''
        }
    }
}

def outputXML(ast, file):
    outFile = file[:-4] + ".xml"

    xml = unparse(ast, pretty=True)
    open(outFile, "w").write(xml)

main("inputs")