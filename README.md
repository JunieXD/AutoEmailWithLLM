# AutoEmailSender

一个基于 Flask 的「教授信息管理 + 邮件发送」的轻量级应用。支持通过 DOCX 文档模板快速个性化生成邮件、CSV 批量导入教授信息、管理发件人配置与用户资料，并记录发送历史。

## 快速开始（uv）
> 项目使用 uv 管理依赖与运行脚本。请先安装 [uv](https://github.com/astral-sh/uv) ，并在终端中执行以下命令。

1. 同步依赖
   ```bash
   uv sync
   ```

2. 初始化数据库（首次运行必需）
   ```bash
   uv run init_database.py
   ```

3. 启动开发服务
   ```bash
   uv run app.py
   ```

4. 访问：http://localhost:5000



## 功能特性
- 教授信息管理：增/删/改/查、导入导出（CSV）
- 文档驱动邮件：从 DOCX 模板生成预览，按教授批量个性化填充并发送（HTML/纯文本）
- 发件人与资料管理：支持设置默认发件人，上传套磁信/简历等文件
- 发送记录：可查看历史发送状态与详情
- 单机部署友好：内置 SQLite，开箱即用


## 技术栈
- Backend：Flask, Flask-SQLAlchemy, Flask-CORS
- Utilities：pandas（CSV 处理）, python-docx（文档读取）, cryptography（加密）
- Python：3.12+


## 目录结构
```
AutoEmailSender/
├── app.py                       # Flask 入口 & 路由
├── init_database.py             # 数据库初始化脚本
├── backend/
│   ├── config.py                # 应用&邮件配置（可读环境变量）
│   ├── database.py              # 数据库初始化与模型注册
│   ├── email_service.py         # 发送邮件逻辑
│   ├── import_service.py        # CSV 导入/预览/导出
│   ├── document_service.py      # 文档内容读取&提取
│   ├── user_service.py          # 用户与文件管理逻辑
│   └── models/                  # SQLAlchemy 模型
│       ├── user_file.py
│       └── user_profile.py
├── frontend/
│   ├── templates/               # 页面：index, professors, records, settings, ...
│   └── static/                  # 静态资源
└── pyproject.toml               # 依赖声明
```


## 配置说明（环境变量）
可通过环境变量覆盖默认配置（PowerShell 示例：`$env:SECRET_KEY="your-key"` 后再运行）：
- SECRET_KEY：Flask 密钥（默认 "your-secret-key-here"）
- DATABASE_URL：数据库连接（默认 SQLite：`sqlite:///auto_email.db`）
- MAIL_SERVER：SMTP 服务器（默认 `smtp.163.com`）
- MAIL_PORT：SMTP 端口（默认 `25`）
- MAIL_USE_TLS：是否启用 TLS（`true/false`，默认 false）
- MAIL_USE_SSL：是否启用 SSL（`true/false`，默认 false）
- LOG_LEVEL：日志级别（默认 `INFO`）

提示：在「设置/用户管理」页面中也可以为发件人设置 `smtp_server` 与 `smtp_port`。发送时会优先读取默认用户的配置。


## 使用流程
1. 设置发件人
   - 打开「用户管理」页面，新增一个用户（姓名、邮箱、邮箱授权码/密码），并填写 SMTP 服务器与端口。
   - 首个用户会自动设置为默认用户，也可手动切换默认。

2. 上传资料（可选）
   - 在用户管理中上传套磁信 DOCX、简历 PDF 或其它材料。

3. 导入教授
   - 在「教授管理」页面上传 CSV 导入；支持下载模板、预览后导入、跳过重复项。

4. 生成并发送邮件
   - 打开「邮件生成」页面，选择模板文档（DOCX，将被读取为 HTML），选择教授/学院，填写主题可用占位符（如 `{{name}}`）。
   - 预览生成后，确认并发送。系统会记录发送结果到「发送记录」。

占位符支持（示例）：
- `{{name}}`/`{{professor_name}}`、`{{university}}`、`{{department}}`、`{{research_area}}`
- `{{sender_name}}`、`{{sender_email}}`、`{{date}}`、`{{school}}`、`{{college}}`


## 开发提示
- 运行脚本统一使用：`uv run <script.py>`
- 默认监听 0.0.0.0:5000（`app.py` 可修改端口）
- 首次运行请先执行数据库初始化脚本


## 许可证

本项目基于 GNU General Public License v3.0（GPL-3.0）授权开源。你可以自由使用、复制、修改和分发本项目，但任何修改版或衍生作品必须以同一许可证发布，并保留原始的版权与许可声明。

- 许可证全文：参见 [LICENSE](./LICENSE)
- 适用许可：GPL-3.0