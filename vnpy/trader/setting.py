"""
Global setting of VN Trader.
"""

from logging import CRITICAL

from .utility import load_json

SETTINGS = {
    "font.family": "Arial",
    "font.size": 12,

    "log.active": True,
    "log.level": CRITICAL,
    "log.console": True,
    "log.file": True,

    "email.server": "smtp.qq.com",
    "email.port": 465,
    # "email.username": "",
    # "email.password": "",
    # "email.sender": "",
    # "email.receiver": "",
    "jqdata_account":"15680977680",
    "jqdata_password":"977680",

    "rqdata.username": "license",
    "rqdata.password": "TDyWsBcDlkTxtaE7KM94a9XguTPfsi3E1n7KAtvUjOVimuJ82nnFUFn65ZXLpWY795sjHIFxFiyf7fD2NcsRmn29a1koHppDiypYGdgUrRhcqRCY3XpX0Fnttv22N-HOW0n4Npcui8U_qsGRZshuPm6Wb4Q3bCv5tOxNPP9U3m8=OyNwqnChDMYNVZ6myLAUP3mLTSVWD7aWUtKiBf-aS8apYXoovxtS8qZ0poK9Ar-vUnVkxm6mFev_VHd0RtH_Q01W6YQ97TzwUllUV-EOxhIXWV0q2_GPKHhYMXPw3AS5Rv6sqO7Mwe4TvJ2ZhMlN4AjlYeQCbQrPm3Qm6gsjGck=",

    "database.driver": "sqlite",  # see database.Driver
    "database.database": "database.db",  # for sqlite, use this as filepath
    "database.host": "localhost",
    "database.port": 3306,
    "database.user": "root",
    "database.password": "",
    "database.authentication_source": "admin",  # for mongodb
}

# Load global setting from json file.
SETTING_FILENAME = "vt_setting.json"
SETTINGS.update(load_json(SETTING_FILENAME))


def get_settings(prefix: str = ""):
    prefix_length = len(prefix)
    return {k[prefix_length:]: v for k, v in SETTINGS.items() if k.startswith(prefix)}
