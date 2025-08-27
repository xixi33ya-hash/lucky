# Baby Naming API

## Railway 部署
1. 上传到 GitHub
2. Railway 新建项目，选择 Deploy from GitHub
3. Railway 会自动运行 Procfile:
   ```
   web: uvicorn app:app --host 0.0.0.0 --port $PORT
   ```

## Vercel 部署
1. 上传到 GitHub
2. 新建 vercel.json（已包含在项目中）
3. 在 Vercel 导入项目即可运行
