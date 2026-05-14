# Game Industry Daily — 使用说明

每天早上 7:00（北京时间）自动从 6 个英文游戏新闻源抓取最新资讯，生成 Markdown 文件并推送到此仓库。

## 新闻来源

- Game Developer
- PC Gamer
- Rock Paper Shotgun
- Eurogamer
- IndieGames
- Engadget Gaming
- Reddit r/gamedev

## 查看新闻

### 方式一：浏览器（最方便）

打开此链接即可查看当日新闻：
<https://github.com/TerryZ874/game-daily-news/blob/main/news/YYYY-MM-DD.md>

把 `YYYY-MM-DD` 替换成对应日期，例如 `2026-05-14.md`。

### 方式二：本地查看

```bash
cd /Users/saoteman/AIProjects/game-daily-news
git pull
ls news/
cat news/2026-05-14.md
```

## 停止自动推送

如果不想再接收每日新闻：

1. 打开 <https://github.com/TerryZ874/game-daily-news/actions>
2. 左侧菜单点击 **Generate Game Industry Daily News**
3. 点击右侧 **···** → **Disable workflow**

重新开启同理，点 **Enable workflow** 即可。

## 技术原理

- **定时触发**：GitHub Actions 每天早上 23:00 UTC（北京时间 07:00）运行
- **新闻抓取**：Python 脚本通过 RSS 获取各来源最新 5 条新闻
- **文件生成**：生成 Markdown 文件到 `news/` 目录，含标题、链接、摘要
- **自动提交**：GitHub Actions 自动将文件提交并推送到仓库

## 文件结构

```
game-daily-news/
├── send_news.py              # 新闻抓取脚本
├── requirements.txt          # Python 依赖
├── .github/workflows/
│   └── send_news.yml         # GitHub Actions 工作流配置
├── news/                     # 每日新闻文件
│   ├── 2026-05-14.md
│   └── ...
└── USAGE.md                  # 本文件
```
