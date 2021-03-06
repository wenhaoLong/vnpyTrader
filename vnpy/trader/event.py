"""
Event type string used in VN Trader.
"""

from vnpy.event import EVENT_TIMER  # noqa

EVENT_TICK = "eTick."
EVENT_TRADE = "eTrade."
EVENT_ORDER = "eOrder."
EVENT_POSITION = "ePosition."
EVENT_ACCOUNT = "eAccount."
EVENT_CONTRACT = "eContract."
EVENT_CURRENT_CONTRACT = "eCurrentContract."
EVENT_CURRENT_POSITION = "eCurrentPosition."
EVENT_CURRENT_TRADE = "eCurrentTrade."
EVENT_CURRENT_SYMBOL = "eCurrentSymbol."
EVENT_CURRENT_INTERVAL = "eCurrentInterval."
EVENT_CURRENT_TICK = "eCurrentTick."
EVENT_SAVED_STRATEGY = "eSavedStrategy."
EVENT_LOG = "eLog"
EVENT_SCATTER = "eScatter"
EVENT_MA = "eMa"
EVENT_CLEAN = "eClean"
EVENT_INFO = "eInfo"
EVENT_NEW_K = "eK"
EVENT_CURRENT_ACCOUNT = "eCurrentAccount"