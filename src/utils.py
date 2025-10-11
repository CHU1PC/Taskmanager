import os
import sys


def resource_path(rel_path: str) -> str:
    """
    PyInstaller のビルド方式に合わせて
    リソースが展開されるベースパスを返す。
    """
    # onefile のときは _MEIPASS、一方 onedir や普通の実行時はスクリプトのある場所
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(__file__))
    return os.path.join(base_path, rel_path)
