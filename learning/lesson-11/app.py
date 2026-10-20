import json
from pathlib import Path

data_file = Path(__file__).with_name("tasks.json")

if data_file.exists():
    tasks = json.loads(data_file.read_text(encoding="utf-8"))
else:
    tasks = [
        {"title": "整理书桌", "status": "待办"},
        {"title": "阅读 Python 教程", "status": "进行中"},
        {"title": "检查邮件", "status": "已完成"},
    ]
def get_tasks_by_status(tasks, target_status):
    result = []

    for task in tasks:
        if task["status"] == target_status:
            result.append(task)

    return result


new_title = input("请输入一条新任务：").strip()

if new_title:
    tasks.append({
        "title": new_title,
        "status": "待办",
    })
else:
    print("任务标题不能为空")

title_to_update = input("请输入要修改状态的任务名称：").strip()

if title_to_update:
    new_status = input("请输入新状态（待办 / 进行中 / 已完成）：").strip()
    allowed_statuses = ["待办", "进行中", "已完成"]

    if new_status not in allowed_statuses:
        print("状态无效，没有修改")
    else:
        found = False

        for task in tasks:
            if task["title"] == title_to_update:
                task["status"] = new_status
                found = True
                break

        if found:
            print("任务状态已更新")
        else:
            print("没有找到这条任务")

status_to_show = input(
    "输入状态筛选（待办 / 进行中 / 已完成）；直接回车看全部："
).strip()

if status_to_show:
    visible_tasks = get_tasks_by_status(tasks, status_to_show)
else:
    visible_tasks = tasks

for task in visible_tasks:
    print(f"{task['title']}（{task['status']}）")
