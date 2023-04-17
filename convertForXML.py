from json import dumps
from xmltodict import unparse

def outputXML(ast):
    xml = unparse(ast, pretty=True)
    print(xml)

def convertASTForXML(inputAST):
    def traverse(node):
        parent_tag = f"{node['parent']}-{node['id']}"
        children_ids = ','.join(child['id'] for child in node['children'])

        output_node = {
            '@id': node['id'],
            '@children': children_ids
        }

        for child in node['children']:
            child_output = traverse(child)
            child_tag = f"{child['parent']}-{child['id']}"
            output_node[child_tag] = child_output

        return output_node

    return traverse(inputAST)

inputAST = {
    "parent": "PROG",
    "id": "1",
    "children": [
        {
            "parent": "ALGO",
            "id": "2",
            "children": [
                {
                    "parent": "INSTRS",
                    "id": "5",
                    "children": []
                },
                {
                    "parent": "INSTRS",
                    "id": "6",
                    "children": []
                },
                {
                    "parent": "INSTRS",
                    "id": "4",
                    "children": []
                }
            ]
        },
        {
            "parent": "PROCDEFS",
            "id": "3",
            "children": []
        }
    ]
}

outputAST = convertASTForXML(inputAST)
print(dumps(outputAST, indent=2))
outputXML({"root": outputAST})