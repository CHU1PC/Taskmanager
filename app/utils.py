import os
import sys


def resource_path(rel_path: str) -> str:
    """
    PyInstaller のビルド方式に合わせて
    リソースが展開されるベースパスを返す。
    """
    if hasattr(sys, "_MEIPASS"):
        # PyInstallerでビルドされた場合
        # _MEIPASSはContents/Resourcesを指すので、appディレクトリを追加
        base_path = os.path.join(sys._MEIPASS, "app")
    else:
        # 開発環境では、このファイル(utils.py)があるディレクトリ(app/)が基準
        base_path = os.path.dirname(__file__)
    return os.path.join(base_path, rel_path)
