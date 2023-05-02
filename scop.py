# pylint: disable-all

# Generate a scope table from a *pruned* AST
def scope(ast):
    # Extract intermediate proc tree
    procTree = extractProcTree(ast)

    # Generate scope table
    tbl = getScopeTable(procTree)

    # Add global variables
    addVariables(tbl, ast)
    
    return tbl

#========== SCOPE TABLE ==========#

scopes = ["main"]

def getScopeTable(procTree, parentScope="main"):
    res = {}

    for name, details in procTree.items():
        if isinstance(details, dict):
            current_scope = parentScope

            res[details["id"]] = {
                "name": name,
                "scope": current_scope
            }

            # Remove 'calls' and 'id' keys for recursive call
            inner = {k: v for k, v in details.items() if k not in ["calls", "id"]}

            res.update(getScopeTable(inner, name))

    return res


#========== PROC TREE ==========#
# procTree = {
#   "p1": {
#       "p2": {},
#       "p3": {},
#       "calls": ["p2"]
#       "id": 69
#   }
#   "calls": []
# }

# Traverse a PROGR node to extract a proc tree
def extractProcTree(node):
    # res = {"p1":{}, "calls":[]}

    algo = getNodePart(node, "ALGO")
    defs = getNodePart(node, "PROCDEFS")

    # traverse ALGO for calls
    calls = getCallList(algo)

    res = {}

    # flatten procdefs into a list of procs
    procs = getProcList(defs)

    for proc in procs:
        procProg = getNodePart(proc, "PROG")
        p = {} if procProg is None else extractProcTree(procProg)
        p["id"] = proc["id"]
        res[proc["value"]] = p

    res["calls"] = calls

    return res

# Pass an algo node to get a list of calls
def getCallList(algo):
    instr = getNodePart(algo, "INSTR")
    seq = getNodePart(algo, "SEQ")
    seqAlgo = getNodePart(seq, "ALGO")

    # Check if INSTR is a call
    call = getNodePart(instr, "CALL")

    res = [] if call is None else [call["value"]]

    resTail = [] if seqAlgo is None else getCallList(seqAlgo)

    return res + resTail

# Pass a procdef node to get a list procs
def getProcList(procdef):
    proc = getNodePart(procdef, "PROC")
    procdefs = getNodePart(procdef, "PROCDEFS")

    res = [] if proc is None else [proc]

    resTail = [] if procdefs is None else getProcList(procdefs)

    return res + resTail


def getNodePart(node, part):
    for child in node["children"]:
        if child["name"] == part:
            return child
    return None

#========== VARIABLES ==========#

def addVariables(tbl, ast):
    vars = traverseForVars(ast)
    for v in vars:
        name = extractVarName(v)

        # Check not already in table
        found = False
        for val in tbl.values():
            if val["name"] == name:
                found = True
                break

        if not found:
            tbl[v["id"]] = {
                "name": name,
                "scopeId": "0", # global
                "scope": "global"
            }

def extractVarName(node):
    name = ""

    for child in node["children"]:
        if child["name"] == "term":
            name = child["value"] + name
        elif child["name"] == "DIGITS":
            name += child["value"]
    return name

def traverseForVars(node):
    res = []
    for child in node["children"]:
        if child["name"] in ["NUMVAR", "BOOLVAR", "STRINGV"]:
            res.append(child)
        else:
            res += traverseForVars(child)
    return res