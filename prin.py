# pylint: disable-all
import os
import string

def outputScopeTableHTML(tbl, file):
    #=========== OUTPUTS ===========#
    if not os.path.exists("outputs"):
        os.makedirs("outputs")

    outFile = file

    if outFile.startswith("inputs" + os.sep):
        outFile = "outputs" + os.sep + outFile[7:]

    dotIndex = outFile.rfind(".")

    if dotIndex != -1:
        outFile = outFile[:dotIndex] + ".html"
    else:
        outFile += ".html"

    #=========== HTML ===========#
    html_template = string.Template("""
    <html>
    <head>
        <title>Symbol Table</title>
        <style>
        html {
            background-color: #f5f5f5;
            padding: 1em;
            font: 1em mono, sans-serif;
        }
        table {
            border: 2px solid #0a0a0a;
            box-shadow: 3px 3px 0 #0a0a0a;
            border-radius: 0.2em;
            padding: 1em;
        }
        td {
            border: 1px solid #0a0a0a;
            padding: 0.4em;
        }
        </style>
    </head>
    <body>
        <h4>Dino Gironi (u21630276)</h4>
        <h3>Symbol Table</h3>
        <table>
            <tr>
                <th>Node ID</th>
                <th>Name</th>
                <th>Scope</th>
                <th>Scope ID</th>
            </tr>
            $rows
        </table>
        <br />
        <table>
            <tr>
                <th>Warnings</th>
            </tr>
            $warnRows
        </table>
    </body>
    </html>
    """)

    warnRow_template = string.Template("""
    <tr>
        <td>$warn</td>
    </tr>
    """)

    row_template = string.Template("""
    <tr>
        <td>$id</td>
        <td>$name</td>
        <td>$scope</td>
        <td>$scopeId</td>
    </tr>
    """)

    # Generate table rows
    rows = []
    for id, details in tbl.items():
        row = row_template.substitute(id=id, name=details['name'], scope=details['scope'], scopeId=details['scopeId'])
        rows.append(row)

    # Generate warning rows
    warnRows = []
    for id, details in tbl.items():
        # row = warnRow_template.substitute(warn=details['warnings'])
        rows.append(row)

    # Generate HTML
    html = html_template.substitute(rows=''.join(rows), warnRows=''.join(warnRows))

    #=========== WRITE ===========#
    open(outFile, "w").write(html)