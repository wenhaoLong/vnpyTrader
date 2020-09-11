from pathlib import Path
from vnpy.trader.app import BaseApp
from .engine import EditorEngine, APP_NAME


class EditorManagerApp(BaseApp):
    """"""
    app_name = APP_NAME
    app_module = __module__
    app_path = Path(__file__).parent
    display_name = "函数编辑"
    engine_class = EditorEngine
    widget_name = "EditorManager"
    icon_name = "editor.ico"
