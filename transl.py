# pylint: disable-all
from json import dumps
from scop import getTypedVars

def translate(ast):
    translator = Translator()
    basic = translator.woodooMagic(ast)
    return basic

class Translator:
    ptbl = {} # Procedure table

    def checkToken(self, children, index, token):
        if index >= len(children):
            return False
        return children[index]["name"] == "term" and children[index]["value"] == token
    
    def checkType(self, children, index, typ):
        return children[index]["name"] == typ

    def addProc(self, proc):
        self.ptbl[proc] = {
            "basic": "",
        }

    def getDefaultVal(self, varType):
        match varType:
            case "num":
                return "0"
            case "bool":
                return "false"
            case "string":
                return "\"\""
            case _:
                return "0"

    # Flatten the BASIC program tree into list of instructions
    def linearize(self, basic):
        # TODO
        return basic

    def woodooMagic(self, ast):
        vars = getTypedVars(ast)

        # Declare variables globally
        basic = "REM ========== GLOBAL VARIABLES ==========\n"
        for v in vars:
            basic += "LET " + v["name"] + ("$" if v["type"] == "string" else "") + " = " + self.getDefaultVal(v["type"]) + "\n"
        basic += "\n"

        # Add call to main procedure
        basic += "REM ========== MAIN PROCEDURE ==========\n"
        basic += "GOSUB p42069\n\n"

        # Wrap the program in 'main' procedure
        wrappedAST = {
            "name": "PROC",
            "id": "10000000",
            "children": [
                {
                    "name": "term",
                    "id": "10000001",
                    "children": [],
                    "value": "{"
                },
                ast,
                {
                    "name": "term",
                    "id": "10000002",
                    "children": [],
                    "value": "}"
                }
            ],
            "value": "p42069"
        }

        self._proc(wrappedAST)

        # Add procedure definitions
        basic += "REM ========== PROCEDURES ==========\n"
        for p in self.ptbl:
            basic += self.ptbl[p]["basic"] + "\n"

        return basic

    #========== CHECKS ==========#
    # Note: This code assumes a perfect input AST. It does not check for errors.

    def _progr(self, progr):
        ch = progr["children"]
        # PROGR -> ALGO PROCDEFS
        res = self._algo(ch[0])

        # self._procdefs(ch[1])
        return res

    def _procdefs(self, procdefs):
        ch = procdefs["children"]

        if self.checkToken(ch, 0, ","):
            # PROCDEFS -> ,PROC PROCDEFS
            self._proc(ch[1])
            self._procdefs(ch[1])

        else:
            # PROCDEFS -> ε
            return []

    def _proc(self, proc):
        ch = proc["children"]
        # PROC -> p DIGITS{PROGR}

        procName = proc["value"]

        if procName not in self.ptbl:
            self.addProc(procName)

        res = procName + ":\n"

        res += self._progr(ch[1])

        res += "RETURN\n"

        self.ptbl[procName]["basic"] = res

    # def _digits(self, digits): # ALL USE CASES ARE PRUNED
    # def _d(self, d): # PRUNED

    def _more(self, more):
        ch = more["children"]
        # MORE -> DIGITS
        # MORE -> ε
        pass

    # Constructs the procedure body
    def _algo(self, algo):
        ch = algo["children"]
        # ALGO -> INSTR COMMENT SEQ
        res = self._instr(ch[0])

        res += self._seq(ch[2])

        return res

    def _seq(self, seq):
        ch = seq["children"]
        if self.checkToken(ch, 0, ";"):
            # SEQ -> ; ALGO
            return self._algo(ch[1])

        else:
            # SEQ -> ε
            return ""

    def _instr(self, instr):
        ch = instr["children"]
        res = ""

        if self.checkType(ch, 0, "INPUT"):
            # INSTR -> INPUT
            res += self._input(ch[0])
        
        elif self.checkType(ch, 0, "OUTPUT"):
            # INSTR -> OUTPUT
            res += self._output(ch[0])

        elif self.checkType(ch, 0, "ASSIGN"):
            # INSTR -> ASSIGN
            res += self._assign(ch[0])

        elif self.checkType(ch, 0, "CALL"):
            # INSTR -> CALL
            return "GOSUB " + ch[0]["value"] + "\n"

            # INSTR -> LOOP
            # INSTR -> BRANCH
            # INSTR -> h //halt

        return res

    # def _call(self, call): # PRUNED

    def _assign(self, assign):
        ch = assign["children"]

        # After pruning, variable name is just stored in "value"
        varName = ch[0]["value"]
        varExpr = ""

        if self.checkType(ch, 0, "NUMVAR"):
            # ASSIGN -> NUMVAR := NUMEXPR
            varExpr = self._numexpr(ch[2])
        elif self.checkType(ch, 0, "BOOLVAR"):
            # ASSIGN -> BOOLVAR := BOOLEXPR
            varExpr = self._boolexpr(ch[2])
        else:
            # ASSIGN -> STRINGV := STRI
            varName = varName + "$"
            varExpr = self._stri(ch[2])

        return "LET " + varName + " = " + varExpr + "\n"

    def _loop(self, loop):
        ch = loop["children"]
        # LOOP -> w(BOOLEXPR)t{ALGO}ELSE
        pass

    def _branch(self, branch):
        ch = branch["children"]
        # BRANCH -> i(BOOLEXPR)t{ALGO}ELSE
        pass

    def _else(self, els):
        ch = els["children"]
        # ELSE -> e{ALGO}
        # ELSE -> ε
        pass

    # SIGNIFICANTLY PRUNED
    # def _numvar(self, numvar):
    # def _boolvar(self, boolvar):
    # def _stringv(self, stringv):

    def _numexpr(self, numexpr):
        ch = numexpr["children"]

        if self.checkToken(ch, 0, "a"):
            # NUMEXPR -> a(NUMEXPR,NUMEXPR)
            return self._numexpr(ch[1]) + " + " + self._numexpr(ch[2])
        elif self.checkToken(ch, 0, "m"):
            # NUMEXPR -> m(NUMEXPR,NUMEXPR)
            return self._numexpr(ch[1]) + " * " + self._numexpr(ch[2])
        elif self.checkToken(ch, 0, "d"):
            # NUMEXPR -> d(NUMEXPR,NUMEXPR)
            return self._numexpr(ch[1]) + " / " + self._numexpr(ch[2])

        elif self.checkType(ch, 0, "NUMVAR"):
            # NUMEXPR -> NUMVAR
            return ch[0]["value"]
        else:
            # NUMEXPR -> DECNUM
            return ch[0]["value"]

    # def _decnum(self, decnum): # PRUNED

    def _neg(self, neg):
        ch = neg["children"]
        # NEG -> -POS
        pass

    def _pos(self, pos):
        ch = pos["children"]
        # POS -> INT.DD
        pass

    def _int(self, int):
        ch = int["children"]
        # INT -> 1MORE | 2MORE | 3MORE | 4MORE | 5MORE | 6MORE | 7MORE | 8MORE | 9MORE
        pass

    def _boolexpr(self, boolexpr):
        ch = boolexpr["children"]
        # BOOLEXPR -> LOGIC
        # BOOLEXPR -> CMPR
        pass

    def _logic(self, logic):
        ch = logic["children"]
        # LOGIC -> BOOLVAR
        # LOGIC -> T | F
        # LOGIC -> ^(BOOLEXPR, BOOLEXPR)
        # LOGIC -> v(BOOLEXPR, BOOLEXPR)
        # LOGIC -> !(BOOLEXPR, BOOLEXPR)
        pass

    def _cmpr(self, cmpr):
        ch = cmpr["children"]
        # CMPR -> E(NUMEXPR, NUMEXPR)
        # CMPR -> <(NUMEXPR, NUMEXPR)
        # CMPR -> >(NUMEXPR, NUMEXPR)
        pass

    def _stri(self, stri):
        ch = stri["children"]
        # STRI -> "CCCCCCCCCCCCCCC"
        pass

    def _c(self, c):
        ch = c["children"]
        # C -> a | b | c | ...
        pass

    # COMMENTS REMOVED FROM FINAL OUTPUT
    # def _comment(self, comment):

    def _input(self, inp):
        ch = inp["children"]
        # INPUT -> g NUMVAR
        # Input can only accept NUMVAR
        return "INPUT " + ch[1]["value"] + "\n"

    def _output(self, output):
        ch = output["children"]
        # OUTPUT -> TEXT | VALUE

        res = "PRINT "
        res += ch[0]["children"][1]["value"]

        if self.checkType(ch, 0, "TEXT"):
            # OUTPUT -> TEXT
            res += "$"

        return res + "\n"

    # REMOVED FOR BREVITY
    # def _value(self, value):
    # def _text(self, text):