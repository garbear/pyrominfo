PyRomInfo
========

PyRomInfo is a convenient, unified way to get data about a file originating from a read-only memory chip, often from a video game cartridge, a computer's firmware, or from an arcade game's main board.

Crash Course
------------

```python
# Import Gameboy support and parse a Gameboy ROM
from pyrominfo import RomInfo
from pyrominfo import gameboy
props = RomInfo.parse("Zelda.gb")

# Register all available ROM info parsers
from pyrominfo import *
props = RomInfo.parse("Super Smash Bros.n64")
props = RomInfo.parse("Super Mario Kart.smc")
```

Useful links
------------
* Enzyme: https://github.com/Diaoul/enzyme
* GuessIt: http://guessit.readthedocs.org
* Heimdall: https://github.com/topfs2/heimdall
* PyMediaInfo: https://github.com/paltman/pymediainfo
* Mutagen: https://code.google.com/p/mutagen
