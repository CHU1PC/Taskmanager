# これはポモドーロタイマーを使ったtask management applicationです。
---
## バクが見つかったり追加して欲しい機能がありましたら以下のメールアドレス、またはDMのほうで連絡をいただけると幸いです
raikyu70@gmail.com
X: CHU1PC
---
## 使い方
### releaseから最新のversionのzipファイルをダウンロードしてください
### ダウンロードしたらそのzipファイルを解凍していただき, Windows pcであればmain_Windowsを開き、macOS pcであればmain_macOSを開いてください
### ポモドーロの項目には、音量調整ボタン
<img src="readme_img/volume_button.png" alt="音量調整ボタンの画像" style="width: 50%; height: auto;"/>
<img src="readme_img/volume_set.png" alt="音量調整画面の画像" style="width: 50%; height: auto;">

### ポモドーロの時間と休憩時間の設定ボタン
<img src="readme_img/pomodoro_set_btn.png" alt="ポモドーロの設定ボタンの画像" style="width: 50%; height: auto;"/>
<img src="readme_img/pomodoro_set.png" alt="ポモドーロの設定画面の画像" style="width: 50%; height: auto;"/>

### 開始ボタンを押すとポモドーロタイマーが開始し、停止ボタンを押すとストップします、リセットボタンを押すと、累計勉強時間、累計ポモドーロ回数を0にリセットします。
<img src="readme_img/timer_btn.png" alt="タイマーの開始ボタン" style="width: 50%; height: auto;"/>


### 右のタスク選択からタスクを選択ことができます（これは下に書いてある、タスクマネージャーでタスクを追加したら使える）
### タスクを選択して、タイマーを開始することでタスクマネージャの方で色々な情報を管理できます
<img src="readme_img/task_select.png" alt="タスクの選択" style="width: 50%; height: auto;"/>
<img src="readme_img/task_select_screen.png" alt="タスクの選択" style="width: 50%; height: auto;"/>

### 左の欄の上から2つ目のタスクを押すとタスクマネージャーに移動します。

### タスクを追加するためには画面中央上にあるタスク追加欄に文字列を記入して、追加ボタンを押すとタスクを追加できます
<img src="readme_img/task_add_btn.png" alt="タスクの追加ボタン" style="width: 50%; height: auto;"/>

### タスクを追加する際には緊急度と重要度を選択します。　設定すると、タスクの並び替えが行えます
<img src="readme_img/urgency.png" alt="タスクの緊急度と重要度の選択" style="width: 50%; height: auto;">

### タスクを選択すると、右下に各タスクの今までの総合計勉強時間、今日の勉強時間、昨日の勉強時間を表示できる
<img src="readme_img/task_time.png" alt="各タスクの情報" style="width: 50%; height: auto;">

### またタスク選択中では右側のボックスになにかメモであったりをタスクごとに書くことができます
<img src="readme_img/task_description.png" alt="各タスクの情報" style="width: 50%; height: auto;">

### 左上の欄の上から3つ目のタスクを押すとタスクの重要度、緊急度によって表示される画面に切り替わります
<img src="readme_img/urgency_importance.png" alt="各タスクの情報" style="width: 50%; height: auto;">

#　新しいバージョンをダウンロードする前にやっていただきたいこと
### 新しいバージョンに変更した際に今までに追加したデータが消えてしまう可能性があります、そのためバックアップをとっていただきたいです。
### バックアップの仕方は
### 1. Pythonをインストールする, これはバージョンが3.12.9だと望ましいです
### 2.ターミナルで次のコマンドを打つ
```bash
pip install PyQt6
```
### 3.ターミナルで次のコマンドを打つ
```bash
python3 -c "
from PyQt6.QtCore import QSettings
import os

settings = QSettings('CHU1PC', 'TaskManagerApp')

if not os.path.exists(settings.fileName()):
    print('設定ファイルはまだ存在しません')

settings.beginGroup('')
for key in settings.allKeys():
    print(f'  {key}: {settings.value(key)}')
"
```
### もし設定ファイルはまだ存在しませんと表示されたらインストールしてください
### コマンドを打った後にターミナル上に出力される tasks: []の[]の部分をコピーして, restore.pyのtasks = []の[]
<img src="readme_img/restore.png" alt="taskの復元よう画像" style="width: 50%; height: auto;"/>

## もしzipファイルが動かない場合は制作者に連絡するか、自身でローカルにcloneしていただき次のコマンドをカレントディレクトリをGUIにしてから実行してください

## for mac
```bash
pyinstaller --onefile --windowed --add-data 'audio/*.mp3:audio' --add-data 'img/*:img' --hidden-import PyQt6 main.py
```
## for windows
```bash
pyinstaller --onefile --windowed --add-data "audio/*.mp3:audio" --add-data "img/*:img" --hidden-import PyQt6 main.py
```
