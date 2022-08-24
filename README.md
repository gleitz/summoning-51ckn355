# SUMMONING-51CKN355

*AI Generated Magic: The Gathering Cards playable in Cockatrice*

## Installation
- `pip install -r requirements.txt`
- Download [Chromedriver](https://chromedriver.chromium.org/) and place the executable in `./chromedriver`

## Usage
```
» python generate.py -h
usage: generate.py [-h] [-c [COST]] [-n [NAME]]

MTG Card Generator

options:
  -h, --help            show this help message and exit
  -c [COST], --cost [COST]
                        The cost of your card
  -n [NAME], --name [NAME]
                        The name of your card
```

## Example
```
python generate.py --name "Gleitz, The Mellifluous" --cost "{2}{B}{G}"
```

![Gleitz, The Mellifluous](https://dl.dropboxusercontent.com/s/vtpehwtpxiev6hp/gleitz-the-mellifluous_1661320508.png)
