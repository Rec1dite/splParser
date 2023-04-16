tokens = {
    "asdf"  : "asdf",
    "!"     : "!",
    "("     : "(",
    ")"     : ")",
    ","     : ",",
    "-"     : "-",
    "."     : ".",

    "0"   : "DIGIT",
    "1"   : "DIGIT",
    "2"   : "DIGIT",
    "3"   : "DIGIT",
    "4"   : "DIGIT",
    "5"   : "DIGIT",
    "6"   : "DIGIT",
    "7"   : "DIGIT",
    "8"   : "DIGIT",
    "9"   : "DIGIT",

    ":="    : ":=",
    ";"     : ";",
    "<"     : "<",
    "C"     : "C",
    "E"     : "E",
    "F"     : "F",
    "T"     : "T",
    "\""    : "QUOTE",
    "^"     : "^",
    "a"     : "a",
    "b"     : "b",
    "c"     : "c",
    "d"     : "d",
    "g"     : "g",
    "h"     : "h",
    "m"     : "m",
    "n"     : "n",
    "o"     : "o",
    "p"     : "p",
    "r"     : "r",
    "s"     : "s",
    "v"     : "v",
    "{"     : "{",
    "|"     : "|",
    "}"     : "}",
}

def tokenize(text):
    # Remove newlines
    print(text)

eg = {
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
