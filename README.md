# これはポモドーロタイマーを使ったtask manager applicationです。

## 使い方
### releaseから最新のversionのzipファイルをダウンロードしてください
### ダウンロードしたらそのzipファイルを解凍していただき, Windows pcであればmain_Windowsを開き、macOS pcであればmain_macOSを開いてください
### ポモドーロの項目には、音量調整ボタン
<img src="readme_img/volume_set_btn.png" alt="音量調整ボタンの画像" style="width: 50%; height: auto;"/>
<img src="readme_img/volume_set.png" alt="音量調整画面の画像" style="width: 50%; height: auto;">

### ポモドーロの時間と休憩時間の設定ボタン
<img src="readme_img/pomodoro_set_btn.png" alt="ポモドーロの設定ボタンの画像" style="width: 50%; height: auto;"/>
<img src="readme_img/pomodoro_set.png" alt="ポモドーロの設定画面の画像" style="width: 50%; height: auto;"/>

### 開始ボタンを押すとポモドーロタイマーが開始し、停止ボタンを押すとストップします、リセットボタンを押すと、累計勉強時間、累計ポモドーロ回数を0にリセットします。
<img src="readme_img/timer_start.png" alt="タイマーの開始ボタン" style="width: 50%; height: auto;"/>
<img src="readme_img/timer_stop.png" alt="タイマーの停止ボタン" style="width: 50%; height: auto;"/>

### 目標時間を決めることができます
<img src="readme_img/goal_time.png" alt="目標時間" style="width: 50%; height: auto;"/>

### 右のタスク選択からタスクを選択ことができます（これは下に書いてある、タスクマネージャーでタスクを追加したら使える）
### タスクを選択して、タイマーを開始することでタスクマネージャの方で色々な情報を管理できます
<img src="readme_img/task_select.png" alt="タスクの選択" style="width: 50%; height: auto;"/>

### 左の欄の上から2つ目のタスクを押すとタスクマネージャーに移動します。

### タスクを追加するためには画面中央下にあるタスク追加欄に文字列を記入して、追加ボタンを押すとタスクを追加できます
<img src="readme_img/task_add_btn.png" alt="タスクの追加ボタン" style="width: 50%; height: auto;"/>
<img src="readme_img/task_task_sel.png" alt="タスク追加後の場所" style="width: 50%; height: auto;"/>

### タスクを選択すると、右下に各タスクの今までの総合計勉強時間、今日の勉強時間、昨日の勉強時間を表示できる
<img src="readme_img/task_time.png" alt="各タスクの情報" style="width: 50%; height: auto;">

### タスク選択画面で右クリックを押すと編集と削除を行えます
<img src="readme_img/task_task_name_edit.png" alt="タスクの編集と削除" style="width: 50%; height: auto/"/>

### 左の2つのボタンからその日の合計勉強時間の編集と0にリセットすることができます
<img src="readme_img/sum_time_edit.png" alt="その日の合計時間の編集" style="width: 50%; height: auto;"/>

## もしzipファイルが動かない場合は制作者に連絡するか、自身でローカルにcloneしていただき次のコマンドをカレントディレクトリをGUIにしてから実行してください

## for mac
```bash
pyinstaller --onefile --windowed --add-data 'audio/*.mp3:audio' --add-data 'img/*:img' --hidden-import PyQt6 main.py
```
## for windows
```bash
pyinstaller --onefile --windowed --add-data "audio/*.mp3:audio" --add-data "img/*:img" --hidden-import PyQt6 main.py
```
