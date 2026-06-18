# 暑假学习计划助手后端

## 启动

```powershell
python server.py
```

服务默认监听 `http://127.0.0.1:5000`。

## 接口

- `GET /health`
- `GET /api/basic-options`

首次启动时会自动创建 `data/study_plan.db`，并写入首页全部选项。

可通过环境变量修改监听地址、端口和数据库路径：

- `STUDY_PLAN_API_HOST`
- `STUDY_PLAN_API_PORT`
- `STUDY_PLAN_DB_PATH`
