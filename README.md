# Dino Gironi
# u21630276


To run the code, make sure that the requirements are installed through pip: `pip3 install -r requirements.txt`

Place any test files within the `inputs/` folder

Then simply run main.py as follows:
```bash
    # To print a basic help message
    python3 pars.py -h

    # To run a set of regex strings from a .json file
    python3 pars.py -f yourFile.spl
    # (See example regexes.json for format)

    # To run one or more regex strings passed as arguments
    python3 pars.py "regex1,regex2,regex3,..."

    #E.g.
    python3 pars.py "a|b"

```

Command output categories are stored in `out/*`.
The final XML output is stored in `out/xml/`.