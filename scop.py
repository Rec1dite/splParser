# pylint: disable-all
import json

res = {
    "errors": [],
    "warnings": []
}

# Generate a scope table from a *pruned* AST
def scope(ast):
    # Extract intermediate proc tree
    procTree = extractProcTree(ast)

    res = {
        "errors": [],
        "warnings": []
    }

    iterateScopes({"main": procTree})
    print(res)

    # Generate scope table
    tbl = getScopeTable(procTree)

    # tbl["stats"] = res

    # Add global variables
    addVariables(tbl, ast)
    
    return tbl

#========== CHECK SCOPES ==========#

# The procedure called here has no corresponding
# declaraion in this scope
def checkScopeErrors(name, body, siblings, children):
    # procs may call: direct children, siblings, themselves
    return []

# The procedure declared here is not called from
# anywhere within the scope to which it belongs
def checkScopeWarning(name, body, siblings, children):
    # RED = "\033[1;31m"
    # GREEN = "\033[1;32m"
    # BLUE = "\033[1;34m"
    # RESET = "\033[0;0m"
    # print(RED, name, GREEN, body, BLUE, siblings, RESET, children)

    # Check if children list the current node in their calls
    calledInChild = False
    for k, v in body.items():
        childCalls = v.get('calls', [])
        if name in childCalls:
            calledInChild = True
            break

    # Check if siblings list the current node in their calls
    calledInSibling = False
    for k, v in siblings.items():
        siblingCalls = v.get('calls', [])
        if name in siblingCalls:
            calledInSibling = True
            break

    calls = body.get('calls', [])
    calledInSelf = False

    # Check if parent lists the current node in their calls
    if name in calls:
        calledInSelf = True

    if not (calledInSelf or calledInChild or calledInSibling):
        return [f"Procedure {name} is declared but not called within its scope"]

    return []

def iterateScopes(scope_dict, parent=None, siblings=None):
    global res

    siblings = siblings or []
    for key, value in scope_dict.items():
        if isinstance(value, dict):
            # Get the procedure body and children
            body = {k: v for k, v in value.items() if k not in ['calls', 'id']}
            children = [k for k, v in value.items() if isinstance(v, dict)]
            
            # Get siblings
            # current_siblings = [k for k in scope_dict.keys() if k != key and isinstance(scope_dict[k], dict)]
            current_siblings = {k: v for k, v in scope_dict.items() if k != key and isinstance(v, dict)}

            # Check scopes
            res["errors"] += checkScopeErrors(key, body, current_siblings, children)
            res["warnings"] += checkScopeWarning(key, body, current_siblings, children)

            # Recursive call for children
            iterateScopes(value, parent=key, siblings=list(scope_dict.keys()))

def checkCallValid(call, procTree):
    # Check call is to direct child procedure
    for name in procTree.keys():
        if name == call:
            return True
    return False

#========== SCOPE TABLE ==========#

scopes = {
        "global": 0,
        "main": 1,
    }

def getScopeTable(procTree, parentScope="main"):
    res = {}

    for name, body in procTree.items():
        scopes[name] = scopes[parentScope] + 1

        if isinstance(body, dict):
            current_scope = parentScope

            res[body["id"]] = {
                "name": name,
                "scope": current_scope,
                "scopeId": scopes[current_scope]
            }

            # Remove 'calls' and 'id' keys for recursive call
            inner = {k: v for k, v in body.items() if k not in ["calls", "id"]}

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