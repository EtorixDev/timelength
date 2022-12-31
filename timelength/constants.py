from timelength.scales import *

SEPERATORS = [
    ",",
    " ",
    "\t"
]

CONNECTORS = [
    "and"
]

SCALES = [Millisecond(), Second(), Minute(), Hour(), Day(), Week(), Month(), Year(), Decade(), Century()]

ABBREVIATIONS = [item for sublist in SCALES for item in sublist.terms]