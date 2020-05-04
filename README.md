# PickPlaceViewer

A tool for assisting with manual assembly of PCBs using surface mount components.
The locations of components of the same type are indicated to simplify assembly.

[![https://imgur.com/lyLrGrQ.png](https://imgur.com/lyLrGrQl.png)](https://imgur.com/lyLrGrQl.png)

## Usage

* Generate geber files using the protel extensions (this is an option when generating with Kicad, but is the default for Altium)
* Generate the pick and place file (Footprint position file in Kicad)
* Select the folder containing the gerber files for your PCB using the `Open Gerber folder` option from the file menu.
* Select the pick and place file using the `Open pick and place file` option from the file menu.
* Select the component you want to place using the table on the right.

## Setup

### Linux

#### Manual (Ubuntu)
* `sudo apt install libcairo2-dev pkg-config python3-dev python3-pip python3-tk python python3-pil.imagetk python3-cairocffi python3-cairocffi`
* `pip3 install pcb-tools paphra_tktable`
* `python3 ./pickplaceviewer.py`

#### Using pipenv
* install `libcairo2-dev` and `pkg-config` from your package manager
* `pipenv install`
* `./pickplaceviewer.sh`

### Windows

* Download and install cairocffi, pycairo from https://www.lfd.uci.edu/~gohlke/pythonlibs/
* install dependencies with pip: pillow, paphra_tktable, pcb-tools
* run with `py pickplaceviewer.py`