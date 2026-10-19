# 拾序 · 个人任务管理器

一个适合练习 Python 后端基础的小项目：用 FastAPI 提供任务 API，以 SQLite 保存数据，并用简洁的网页完成日常管理。

## 功能

- 新建、查看、编辑、删除任务
- 为任务设置描述、截止日期、优先级和进度
- 按进度筛选，按标题搜索
- 查看全部、待办、进行中和已完成的数量
- API 文档：`/docs`

## 环境准备

需要安装 Python 3.10 或更新版本。安装完成后，在项目目录打开终端。

Windows PowerShell：

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

如果 Python 安装没有提供 `ensurepip`，虚拟环境创建会报错。此时使用下面的方式创建环境并安装依赖（不要先激活环境）：

```powershell
python -m venv --without-pip .venv
python -m pip --python .venv install -r requirements.txt
```

如果没有激活虚拟环境，启动和测试时直接调用 `.venv` 里的解释器：

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
.\.venv\Scripts\python.exe -m pytest
```

macOS / Linux：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## 启动

激活了虚拟环境时：

```bash
python -m uvicorn main:app --reload
```

未激活时（Windows）：

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

打开 <http://127.0.0.1:8000> 使用网页，或打开 <http://127.0.0.1:8000/docs> 查看和试用 API。首次启动时会在项目目录创建 `tasks.db`，任务会保存在本地。

## 运行测试

激活了虚拟环境时：

```bash
python -m pytest
```

未激活时（Windows）：

```powershell
.\.venv\Scripts\python.exe -m pytest
```

测试使用临时数据库，不会修改日常使用的任务数据。

## API 一览

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/api/tasks` | 列出任务；支持 `status`、`q` 参数 |
| `GET` | `/api/tasks/{id}` | 获取单条任务 |
| `POST` | `/api/tasks` | 创建任务 |
| `PATCH` | `/api/tasks/{id}` | 修改一个或多个字段 |
| `DELETE` | `/api/tasks/{id}` | 删除任务 |
| `GET` | `/api/summary` | 获取任务统计 |

进度值为 `todo`、`in_progress`、`done`；优先级为 `low`、`medium`、`high`。任务标题必填，最多 100 字；描述最多 1000 字。
