from enum import Enum

class Sink(Enum):
    """
    Enumeration representing different types of data sinks.
    """
    ALL_URLS = 0
    LS = 1
    SS = 2
    LS_SS = 3
    IDB = 4
    LS_IDB = 5
    SS_IDB = 6
    LS_SS_IDB = 7
    COOKIES = 8
    LS_COOKIES = 9
    SS_COOKIES = 10
    LS_SS_COOKIES = 11
    IDB_COOKIES = 12
    LS_IDB_COOKIES = 13
    SS_IDB_COOKIES = 14
    LS_SS_IDB_COOKIES = 15
    
class Script(Enum):
    """
    Enumeration representing different types of scripts.
    """
    CS = 1
    BG = 2
    CS_BG = 3
    WAR = 4
    CS_WAR = 5
    BG_WAR = 6
    CS_BG_WAR = 7
