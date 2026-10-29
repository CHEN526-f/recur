# Assignment 3 — 提交步骤

本项目按**公开 GitHub 源码仓库 + 本地 Python 交互作品**提交，不部署网页。
正式要求：https://github.com/sd5913/teaching/blob/main/syllabus/03-interactive-experience.md

**仓库已创建并上传：https://github.com/CHEN526-f/recur**

下面第 2、3 节的首次创建和推送已经完成，不要重复创建 `origin`。
现在请完成本机最终运行检查、核对 PROCESS 的实际试用记录，并按第 4 节向 Canvas
提交上面的仓库链接。浏览器版保留在源代码中，但没有部署网页。

后续修改文件后，在本项目终端使用：

```powershell
git status
git add .
git commit -m "Describe the actual change"
git push
```

`commit` 是保存本地快照，`push` 才会把新快照上传；只在 GitHub 网页刷新不会上传本机改动。

## 仓库应包含的内容

| 要求 | 本项目对应内容 |
|---|---|
| 可运行源码 | `app.py`、`recur/` |
| 依赖与精确命令 | `pyproject.toml`、`uv.lock`、README 的 `uv sync --frozen` / `uv run python app.py` |
| 必要素材与使用授权 | `assets/music/technological-messup.ogg`、`assets/music/CREDITS.md`、根目录 `CREDITS.md` |
| 创意、目标用户、互动、限制 | `README.md` |
| 截图与运行效果 | `docs/python-preview.png`、`docs/demo.mp4`；后者是程序渲染预览，不是真人试用录像 |
| 过程与 AI 使用说明 | `PROCESS.md`，包括保留与修改/拒绝的建议 |
| 真人试用与对应改动 | PROCESS 已记录作者确认的键盘、滑块试用及三个反馈；尚未确认修改后的复测 |
| 开发历史 | 保留本地真实 commits；已有代码集中建立的快照不冒充过去的逐日提交 |
| 可选开发实验 | `web/` 保留；Pages 工作流只允许手动触发，推送不会自动发布网页 |

不要上传 `.venv/`、`.reference/`、`captures/`、原参考视频、私人音乐、密钥或他人的录音。
`.gitignore` 已排除这些本地目录。保留 `docs/demo.mp4` 和授权的示范 OGG。

## 1. 先在本机完成最后一次检查

在项目根目录新开终端运行：

```powershell
uv sync --frozen
uv run python app.py
```

按 T 试听示范，按 A/S/D/J/K/L 测试声音与形变，拖动推杆，按 U 导入音乐。
再打开导入窗口后取消，确认已有音乐可以继续。检查 README 中的图和视频能打开。
阅读 PROCESS，确认它准确反映你的真实试用；不要写成“对方认可修改后的效果”，
除非确实找同一位试用者再次体验过。

## 2. 在 GitHub 网页创建公开仓库

你已经登录账号 **CHEN526-f**。点击右上角 **+ → New repository**：

- Repository name：建议 `recur`。
- Description：`RECUR / 环生 — an interactive audiovisual artwork for SD5913 Assignment 3`。
- Visibility：选 **Public**。
- **不要勾选**自动添加 README、.gitignore 或 License；这些内容已经在本地。
- 点击 **Create repository**。

浏览器登录和 `gh` 命令行登录是独立的。可以用 Git for Windows 的浏览器认证直接
推送，也可以先在终端运行 `gh auth login`，选择 GitHub.com → HTTPS → 浏览器登录。
不要把 token 或密码发到聊天里。

## 3. 推送本地 Git 历史

如果严格按上面名称创建了 `CHEN526-f/recur`，在项目根目录执行：

```powershell
git branch -M main
git remote add origin https://github.com/CHEN526-f/recur.git
git push -u origin main
```

前提是本地已有提交。若此时尚未提交，先运行 `git status` 检查待提交文件，然后：

```powershell
git add .
git commit -m "Prepare RECUR interactive artwork submission"
```

若 `origin` 已存在，不要重复添加；用 `git remote -v` 核对它是否指向你新建的仓库。
推送若要求登录，在 Git for Windows 弹出的浏览器认证中自行完成。GitHub 网页上传
文件可以作为备用，但应优先推送本地仓库，以保留真实提交历史。

## 4. 核验，再提交 Canvas

打开无痕/退出登录的浏览器，确认仓库页面可访问，README 的图片与视频链接正常，
源码、依赖、素材和 PROCESS 都存在。不要只上传压缩包而没有可浏览的源文件。

**如果你确实创建并成功推送了上面的仓库**，Canvas 要提交的地址才是：

`https://github.com/CHEN526-f/recur`

该地址现已创建并上传。不要提交 `localhost` 地址、本机路径、zip 下载链接或 GitHub 首页。

截止时间：**2026 年 11 月 1 日 23:59，香港时间**。在线网页链接不是强制项。
