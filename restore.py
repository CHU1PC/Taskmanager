from PyQt6.QtCore import QSettings

# 設定を読み込み
settings = QSettings("CHU1PC", "TaskManagerApp")

# 以前のタスクデータを復元
tasks = [
    {'checked': False, 'detail': '第一優先', 'text': '事例で学ぶ特徴量エンジニアリング', 'urgency': 'urgent_important'}, 
    {'checked': False, 'detail': '第二優先', 'text': '橋本研究室', 'urgency': 'urgent_important'}, 
    {'checked': False, 'detail': '', 'text': 'Pytorch models', 'urgency': 'not_urgent_important'}, 
    {'checked': False, 'detail': '第三優先', 'text': 'Pytorch実践的入門', 'urgency': 'not_urgent_important'}, 
    {'checked': False, 'detail': '', 'text': 'Time manager App', 'urgency': 'not_urgent_not_important'}, 
    {'checked': False, 'detail': '', 'text': '数学', 'urgency': 'not_urgent_not_important'}, 
    {'checked': False, 'detail': '', 'text': '英語', 'urgency': 'not_urgent_not_important'}
]

# タスクを保存
settings.setValue("tasks", tasks)
print(f"タスクを復元しました。復元されたタスク数: {len(tasks)}")

# 確認
current_tasks = settings.value("tasks", [])
print(f"現在のタスク数: {len(current_tasks)}")
for i, task in enumerate(current_tasks):
    print(f"{i+1}. {task.get('text', '')} ({task.get('urgency', 'normal')})")
