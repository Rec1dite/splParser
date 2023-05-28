# pylint: disable-all
from json import dumps
from scop import getTypedVars
import random
import re

# TODO: Test with tabs instead of spaces
def translate(ast):
    translator = Translator()
    basic = translator.woodooMagic(ast)
    return basic

class Translator:
    def __init__(self):
        self.ptbl = {} # Procedure table

    def checkToken(self, children, index, token):
        if index >= len(children):
            return False
        return children[index]["name"] == "term" and children[index]["value"] == token
    
    def checkType(self, children, index, typ):
        if index >= len(children):
            return False
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
                return "0" # false
            case "string":
                return "\"\""
            case _:
                return "0"

    def enumerize(self, basic):
        # Enumerate lines
        # Obtain line numbers for absorbtion tags & replace
        lines = basic.split("\n")
        i = 1
        absorbs = {}
        for l in range(len(lines)):
            if lines[l] == "": # or lines[l].startswith("REM"):
                lines[l] += "\n"
                continue

            # Regex match for absorption tags
            match = re.search(r">>~~>(\w+)<~~<<", lines[l])
            if match:
                id = match.group(1)
                if id not in absorbs:
                    absorbs[id] = i*10

                lines[l] = str(i*10) + " REM label: " + id + "\n"

            else:
                lines[l] = str(i*10) + " " + lines[l] + "\n"

            i += 1

        # Replace expansion tags with line numbers
        res = ""
        for l in range(len(lines)):
            # Regex match for expansion tags
            match = re.search(r"<<~~<(\w+)>~~>>", lines[l])
            if match:
                id = match.group(1)
                if id in absorbs:
                    lines[l] = lines[l].replace(match.group(0), str(absorbs[id]))
                else:
                    lines[l] = lines[l].replace(match.group(0), str(absorbs["ERR"]))
            
            res += lines[l]

        return res

    def getRandomNum(self):
        return random.randint(0, 2**32)

    def getRandomId(self):
        id = hex(random.randint(0, 2**32))[2:].zfill(8)
        idDec = f">>~~>{id}<~~<<" # declaration / absorption
        idRef = f"<<~~<{id}>~~>>" # reference / expansion
        return idDec, idRef

    def woodooMagic(self, ast):
        vars = getTypedVars(ast)

        # Declare variables globally
        basic = "REM ========== GLOBAL VARIABLES ==========\n"
        for v in vars:
            basic += "LET " + v["name"] + ("$" if v["type"] == "string" else "") + " = " + self.getDefaultVal(v["type"]) + "\n"
        basic += "\n"

        # Add call to main procedure
        basic += "REM ========== MAIN PROCEDURE ==========\n"
        basic += "GOSUB <<~~<pMain>~~>>\n"
        basic += "STOP\n\n" # After main procedure completes, stop

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
            "value": "pMain"
        }

        self._proc(wrappedAST)

        # Add procedure definitions
        basic += "REM ========== PROCEDURES ==========\n"
        for p in self.ptbl:
            basic += self.ptbl[p]["basic"] + "\n"
        
        # Add ERR catching procedure
        basic += "REM ========== TRANSLATION ERR CATCHER ==========\n"
        # In the event of an invalid GOTO/GOSUB, we compile optimistically
        # and assume this call is never actually made during runtime
        basic += ">>~~>ERR<~~<<\n"

        return self.enumerize(basic)

    #========== CHECKS ==========#
    # Note: This code assumes a perfect input AST. It does not check for errors.

    def _progr(self, progr):
        ch = progr["children"]
        # PROGR -> ALGO PROCDEFS
        res = self._algo(ch[0])

        # This just recursively adds the procedures to the procedure table
        self._procdefs(ch[1])

        return res

    # Just recursively adds the remaining procedures to the procedure table
    def _procdefs(self, procdefs):
        ch = procdefs["children"]

        if self.checkToken(ch, 0, ","):
            # PROCDEFS -> ,PROC PROCDEFS
            self._proc(ch[1])
            self._procdefs(ch[2])
        else:
            # PROCDEFS -> ε
            pass

    def _proc(self, proc):
        ch = proc["children"]
        # PROC -> p DIGITS{PROGR}

        procName = proc["value"]

        if procName not in self.ptbl:
            self.addProc(procName)

        res = f">>~~>{procName}<~~<<\n"

        res += self._progr(ch[1])

        res += "RETURN\n"

        self.ptbl[procName]["basic"] = res

    # def _digits(self, digits): # ALL USE CASES ARE PRUNED
    # def _d(self, d): # PRUNED
    # def _more(self, more): # PRUNED

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

        if self.checkType(ch, 0, "INPUT"):
            # INSTR -> INPUT
            return self._input(ch[0])
        
        elif self.checkType(ch, 0, "OUTPUT"):
            # INSTR -> OUTPUT
            return self._output(ch[0])

        elif self.checkType(ch, 0, "ASSIGN"):
            # INSTR -> ASSIGN
            return self._assign(ch[0])

        elif self.checkType(ch, 0, "CALL"):
            # INSTR -> CALL
            return f"GOSUB <<~~<{ch[0]['value']}>~~>> \n"

        elif self.checkType(ch, 0, "LOOP"):
            # INSTR -> LOOP
            return self._loop(ch[0])
        
        elif self.checkType(ch, 0, "BRANCH"):
            # INSTR -> BRANCH
            return self._branch(ch[0])

        else:
            # INSTR -> h //halt
            return "STOP\n"

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
            cond = self._boolexpr(ch[2])
            varExpr = "x"
        else:
            # ASSIGN -> STRINGV := STRI
            varName += "$"
            varExpr = self._stri(ch[2])

        return "LET " + varName + " = " + varExpr + "\n"

    def _loop(self, loop):
        ch = loop["children"]
        # print("LOOP", dumps(ch, indent=2))

        # LOOP -> w(BOOLEXPR)t{ALGO}
        cond = self._boolexpr(ch[2])

        algo = self._algo(ch[5])

        aDec, aRef = self.getRandomId()
        bDec, bRef = self.getRandomId()

        return f"{aDec}\n{cond}IF x = 0 THEN GOTO {bRef}\n{algo}GOTO {aRef}\n{bDec}\n"

    def _branch(self, branch):
        ch = branch["children"]
        # BRANCH -> i(BOOLEXPR)t{ALGO}ELSE

        cond = self._boolexpr(ch[2])
        algo = self._algo(ch[6])
        els  = self._else(ch[8])

        bDec, bRef = self.getRandomId()
        cDec, cRef = self.getRandomId()

        return f"{cond}IF x = 0 THEN GOTO {bRef}\n{algo}GOTO {cRef}\n{bDec}\n{els}{cDec}\n"

    def _else(self, els):
        ch = els["children"]

        if self.checkToken(ch, 0, "e"):
            # ELSE -> e{ALGO}
            return self._algo(ch[2])
        else:
            # ELSE -> ε
            return ""
    
    # SUFFICIENTLY PRUNED
    # def _numvar(self, numvar):
    # def _boolvar(self, boolvar):
    # def _stringv(self, stringv):

    def _numexpr(self, numexpr):
        ch = numexpr["children"]

        if self.checkToken(ch, 0, "a"):
            # NUMEXPR -> a(NUMEXPR,NUMEXPR)
            return self._numexpr(ch[2]) + " + " + self._numexpr(ch[4])
        elif self.checkToken(ch, 0, "m"):
            # NUMEXPR -> m(NUMEXPR,NUMEXPR)
            return self._numexpr(ch[2]) + " * " + self._numexpr(ch[4])
        elif self.checkToken(ch, 0, "d"):
            # NUMEXPR -> d(NUMEXPR,NUMEXPR)
            return self._numexpr(ch[2]) + " / " + self._numexpr(ch[4])

        elif self.checkType(ch, 0, "NUMVAR"):
            # NUMEXPR -> NUMVAR
            return ch[0]["value"]

        else:
            # NUMEXPR -> DECNUM
            if ch[0]["value"].startswith("-"):
                return "(" + ch[0]["value"] + ")"
            return ch[0]["value"]

    # def _decnum(self, decnum): # PRUNED
    # def _neg(self, neg): # PRUNED
    # def _pos(self, pos): # PRUNED
    # def _int(self, int): # PRUNED

    # Generates a sequence of cascading GOTOs to evaluate the boolean expression
    # Stores the result in a variable called "x"
    def _boolexpr(self, boolexpr):
        ch = boolexpr["children"]
        if self.checkType(ch, 0, "LOGIC"):
            # BOOLEXPR -> LOGIC
            return self._logic(ch[0])
        else:
            # BOOLEXPR -> CMPR
            # xId = self.getRandomHex()

            # res = "LET x = 0\n"
            # res += f"LET x{xId} = {self._cmpr(ch[0])}\n"
            # res += f"IF x{xId} THEN x = 1\n"

            # return res
            return f"LET x = {self._cmpr(ch[0])}\n"

    def _logic(self, logic):
        ch = logic["children"]
        if self.checkType(ch, 0, "BOOLVAR"):
            # LOGIC -> BOOLVAR
            return "LET x = " + ch[0]["value"] + "\n"

        elif self.checkToken(ch, 0, "T"):
            # LOGIC -> T
            return "LET x = 1\n"

        elif self.checkToken(ch, 0, "F"):
            # LOGIC -> F
            return "LET x = 0\n"

        else:
            tDec, tRef = self.getRandomId()
            fDec, fRef = self.getRandomId()
            endDec, endRef = self.getRandomId()

            res = ""

            if self.checkToken(ch, 0, "^"):
                # LOGIC -> ^(BOOLEXPR, BOOLEXPR)
                xA = self.getRandomNum()
                xB = self.getRandomNum()

                res = self._boolexpr(ch[2]) + "\n"
                res += f"LET x{xA} = x\n"
                res += self._boolexpr(ch[4]) + "\n"
                res += f"LET x{xB} = x\n"

                # Logical AND
                res += f"IF x{xA} = 0 THEN GOTO {fRef}\n"
                res += f"IF x{xB} = 0 THEN GOTO {fRef}\n"
                res += f"GOTO {tRef}\n"

            if self.checkToken(ch, 0, "v"):
                # LOGIC -> v(BOOLEXPR, BOOLEXPR)
                xA = self.getRandomNum()
                xB = self.getRandomNum()

                res = self._boolexpr(ch[2]) + "\n"
                res += f"LET x{xA} = x\n"
                res += self._boolexpr(ch[4]) + "\n"
                res += f"LET x{xB} = x\n"

                # Logical OR
                res += f"IF x{xA} = 0 THEN IF x{xB} = 0 THEN GOTO {fRef}\n"
                res += f"GOTO {tRef}\n"

            else:
                # LOGIC -> !(BOOLEXPR)
                res = self._boolexpr(ch[2]) + "\n"

                # Logical NOT
                res += f"IF x = 0 THEN GOTO {tRef}\n"
                res += f"GOTO {fRef}\n"

            res += f"{tDec}\nLET x = 1\nGOTO {endRef}\n"
            res += f"{fDec}\nLET x = 0\n"
            res += f"{endDec}\n"

            return res

    def _cmpr(self, cmpr):
        ch = cmpr["children"]

        if self.checkToken(ch, 0, "E"):
            # CMPR -> E(NUMEXPR, NUMEXPR)
            return self._numexpr(ch[2]) + " = " + self._numexpr(ch[4])

        elif self.checkToken(ch, 0, "<"):
            # CMPR -> <(NUMEXPR, NUMEXPR)
            return self._numexpr(ch[2]) + " < " + self._numexpr(ch[4])

        elif self.checkToken(ch, 0, ">"):
            # CMPR -> >(NUMEXPR, NUMEXPR)
            return self._numexpr(ch[2]) + " > " + self._numexpr(ch[4])

    def _stri(self, stri):
        ch = stri["children"]
        # STRI -> "CCCCCCCCCCCCCCC"
        return ch[0]["value"]

    # def _c(self, c): # PRUNED

    # COMMENTS REMOVED FROM FINAL OUTPUT
    # def _comment(self, comment):

    def _input(self, inp):
        ch = inp["children"]
        # INPUT -> g NUMVAR
        # Input can only accept NUMVAR
        return "INPUT \"Input a number: \"; " + ch[1]["value"] + "\n"

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