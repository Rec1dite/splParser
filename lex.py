singles = ",p}{0123456789;hcw()itenbsamd-.TF^v!E<>gor"

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
        elif c == '0' and i+3 < len(text) and text[i:i+4] == "0.00" and (not text[i-1] in "0123456789" if i-1 >= 0 else True): # 0.00
            tokens.append("0.00")
            skip_ahead = 3
        elif c == '"' and i+16 < len(text) and text[i+16] == '"': # "string"
            tokens.append("\"" + text[i+1:i+16] + "\"")
            skip_ahead = 16
        elif c == '*' and i+16 < len(text) and text[i+16] == '*': # *comment*
            tokens.append("*" + text[i+1:i+16] + "*")
            skip_ahead = 16
        else:
            if c in singles:
                tokens.append(str(c))
            else:
                print("\033[91mSyntax error: unexpected character: " + c + "({})".format(ord(c)) + "\033[0m")
                print(text[:i] + "\033[91m" + c + "\033[0m" + text[i+1:])
                exit()
        
    tokens.append("$") # eof
    return tokens