# SPL Parser
**Dino Gironi** - u21630276

> The program takes as input a set of SPL/TXT files, and compiles the code into executable BASIC.

To run the code, make sure that the requirements are installed through pip: `pip3 install -r requirements.txt`

To parse files in bulk, place all input files within the `inputs/` folder (See `(1)` below)

`pars.py` can be run as follows:
```bash
    # 1) To parse all files in the inputs/ folder
    python3 pars.py

    # 2) To print a basic help message
    python3 pars.py -h

    # 3) To parse a specific file
    python3 pars.py -f relative/path/to/yourFile.txt
```

For input files in `inputs/`, the final HTML output will be written to `outputs/yourFile.html`.