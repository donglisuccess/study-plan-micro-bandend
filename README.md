# 暑假学习计划助手后端

## 本地启动

项目使用 `uv` 管理 Python 版本、虚拟环境和依赖。

```powershell
uv sync --locked
uv run --locked server.py
```

服务默认监听 `http://127.0.0.1:5000`。

## 接口

- `GET /api/health`
- `GET /api/basic-options`

首次启动时会自动创建 `data/study_plan.db`，并写入首页全部选项。

可通过环境变量修改监听地址、端口和数据库路径：

- `STUDY_PLAN_API_HOST`
- `STUDY_PLAN_API_PORT`
- `STUDY_PLAN_DB_PATH`

## 服务器安装 uv

使用 `deploy` 用户登录服务器后执行：

```bash
curl -LsSf https://astral.sh/uv/0.11.21/install.sh | sh
/home/deploy/.local/bin/uv --version
```

## systemd 服务

将仓库中的服务文件安装到 systemd：

```bash
cd /opt/study-plan-api
/home/deploy/.local/bin/uv sync --locked
sudo cp deploy/study-plan-api.service /etc/systemd/system/study-plan-api.service
sudo systemctl daemon-reload
sudo systemctl enable study-plan-api
sudo systemctl start study-plan-api
```

服务启动命令为：

```bash
/home/deploy/.local/bin/uv run --locked --no-sync server.py
```

部署流程会先执行 `uv sync --locked`，因此 systemd 重启时只使用已经同步好的环境。

为避免 GitHub Actions 等待 sudo 密码，需要由 root 创建最小化免密规则。先确认 systemctl 路径：

```bash
command -v systemctl
```

如果输出是 `/usr/bin/systemctl`，执行：

```bash
echo 'deploy ALL=(root) NOPASSWD: /usr/bin/systemctl restart study-plan-api' \
  | sudo tee /etc/sudoers.d/study-plan-deploy
sudo chmod 440 /etc/sudoers.d/study-plan-deploy
sudo visudo -cf /etc/sudoers.d/study-plan-deploy
sudo -u deploy sudo -n /usr/bin/systemctl restart study-plan-api
```

如果 `command -v systemctl` 返回其他路径，请在 sudoers 规则中使用实际的绝对路径。

## GitHub Actions 自动部署

`.github/workflows/deploy.yml` 会在代码推送到 `main` 后：

1. 检查 `uv.lock` 是否与 `pyproject.toml` 一致。
2. 通过 SSH 将代码同步到服务器。
3. 在服务器执行 `uv sync --locked`。
4. 重启 `study-plan-api`。
5. 请求 `/api/health` 验证部署。

GitHub 仓库需要配置以下 Secrets：

- `SERVER_HOST`
- `SERVER_USER`，填写 `deploy`
- `SERVER_SSH_KEY`
- `SERVER_KNOWN_HOSTS`

还需要配置以下 Variables：

- `SERVER_PORT`，默认可填写 `22`
- `DEPLOY_PATH`，默认可填写 `/opt/study-plan-api`
