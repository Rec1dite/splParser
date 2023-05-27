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

    # Generate call table
    callTbl = getCallTable({ "main": procTree })
    # print("CALL TABLE", json.dumps(callTbl, indent=4))

    # Check scopes for errors/warnings
    checkScopes("main", procTree, callTbl)
    print(res)

    # Generate scope table
    print("PROC TREE", json.dumps(procTree, indent=4))
    tbl = getScopeTable(procTree)
    # print("SCOPE TABLE", json.dumps(tbl, indent=4))
    # print("SCOPES", json.dumps(scopes, indent=4))

    # Add global variables
    addVariables(tbl, ast)

    tbl["stats"] = res
    
    return tbl

#========== CHECK SCOPES ==========#

# The procedure called here has no corresponding
# declaraion in this scope
def checkScopeErrors(name, body, siblings, children):
    # procs may call: direct children, siblings, themselves
    return []

# The procedure declared here is not called from
# anywhere within the scope to which it belongs
def checkScopeWarnings(name, body, siblings, children):
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

# name = name of current scope
# body = body of current scope
# parent = name of parent scope
# siblings = list of sibling scope names
def checkScopes(name, body, callTbl, parent=None, siblings=[]):
    global res

    children = [
        k for k in body.keys()
        if k not in ["calls", "id"]
    ] 

    print()
    print("NAME", name)
    print("SIBLINGS", siblings)
    print("PARENT", parent)
    print("CHILDREN", children)
    
    # Check scoped calls
    calledInChild = False
    for child in children:
        if name in callTbl[child]:
            calledInChild = True
            break

    calledInSibling = False
    for sib in siblings:
        if name in callTbl[sib]:
            calledInSibling = True
            break

    calledInSelf = False
    # Check if parent lists the current node in their calls

    if not (calledInSelf or calledInChild or calledInSibling):
        res["warnings"] += [f"Procedure {name} is declared but not called within its scope"]

    # res["errors"] += checkScopeErrors(key, body, current_siblings, children)
    # res["warnings"] += checkScopeWarnings(key, body, current_siblings, children)

    # Recurse
    for child in children:
        checkScopes(
            name=child,
            body=body[child],
            callTbl=callTbl,
            parent=name,
            siblings=[
                k for k in body.keys()
                if k != child and k not in ['calls', 'id']
            ]
        )

def checkCallValid(call, procTree):
    # Check call is to direct child procedure
    for name in procTree.keys():
        if name == call:
            return True
    return False

#========== CALL TABLE ==========#

# Summarizes calls each proc makes
# callTbl = {
#   "p1": ["p2", "p3"],
#   "p2": ["p3"],
#   "p3": []
# }
def getCallTable(procTree, result=None):
    if result is None:
        result = {}
        
    for name, body in procTree.items():
        if isinstance(body, dict):
            calls = body.get("calls", [])
            result[name] = calls
            getCallTable(body, result)
            
    return result

#========== SCOPE TABLE ==========#

scopes = {
        "global": 0,
        "main": 1,
    }

# Recursively build scope table from proc tree
def getScopeTable(procTree, parentScope="main"):
    res = {}

    for name, body in procTree.items():
        scopes[name] = len(scopes.keys())

        if isinstance(body, dict):
            current_scope = parentScope

            res[body["id"]] = {
                "name": name,
                "scope": current_scope,
                "scopeId": scopes[current_scope],
                "calls": body.get("calls", [])
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

# res = [
#   {
#       "name": "x",
#       "type": "num"
#   },
#   ...
# ]
def getTypedVars(ast):
    vars = traverseForVars(ast)
    res = []

    for v in vars:
        name = v["value"]
        typ = "num" if v["name"]=="NUMVAR" else "bool" if v["name"]=="BOOLVAR" else "string"

        # Skip if already in res
        found = False
        for r in res:
            if r["name"] == name:
                found = True
                break

        if not found:
            res.append({
                "name": name,
                "type": typ
            })
    return res


def addVariables(tbl, ast):
    vars = traverseForVars(ast)

    for v in vars:
        # print(">  ", v)
        name = v["value"]

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

def traverseForVars(node):
    res = []
    for child in node["children"]:
        if child["name"] in ["NUMVAR", "BOOLVAR", "STRINGV"]:
            res.append(child)
        else:
            res += traverseForVars(child)
    return res