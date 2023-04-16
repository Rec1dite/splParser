singles = ",p}{0123456789;hcw()itenbsamd-.TF^v!E<>gor"

regexes = [
    ":=",
    "0.00",
    "\"",
    "*"
]

def tokenize(text):
    tokens = []
    skip_ahead = 0
    for i, c in enumerate(text):
        if skip_ahead > 0:
            skip_ahead -= 1
            continue

        if c == ':' and i+1 < len(text) and text[i+1] == '=': # :=
            tokens.append(":=")
            skip_ahead = 1
        elif c == '0' and i+3 < len(text) and text[i:i+4] == "0.00": # 0.00
            tokens.append("0.00")
            skip_ahead = 3
        elif c == '"' and i+16 < len(text) and text[i+16] == '"': # "string"
            tokens.append("\"" + text[i+1:i+16])
            skip_ahead = 16
        elif c == '*' and i+16 < len(text) and text[i+16] == '*': # *comment*
            tokens.append("*" + text[i+1:i+16])
            skip_ahead = 16
        else:
            if c in singles:
                tokens.append(str(c))
            else:
                print("\033[91mSyntax error: unexpected character: " + c + "\033[0m")
                print(text[:i] + "\033[91m" + c + "\033[0m" + text[i+1:])
                exit()
        
    tokens.append("$") # eof
    return tokens

# exampleAST = {
#     'PROG': {
#         '@id': '1',
#         '@children': '2,3',

#         'ALGO': {
#             '@id': '2',
#             '@children': '4,5,6'
#         },

#         'PROCDEFS': {
#             '@id': '3',
#             '@children': ''
#         }
#     }
# }
