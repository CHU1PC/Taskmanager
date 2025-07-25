import sys, os


def resource_path(rel_path):
    # onefile の場合は _MEIPASS、onedir の場合はスクリプトのディレクトリ
    base = getattr(sys, "_MEIPASS", os.path.dirname(__file__))
    return os.path.join(base, rel_path)


# 使い方
audio_file = resource_path("audio/alert.mp3")
print(audio_file)  # 存在するか要確認