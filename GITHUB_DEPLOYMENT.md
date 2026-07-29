# GitHub Deployment Guide
# GitHub 部署指南

## English

### Step 1: Create a New Repository on GitHub

1. Go to [GitHub](https://github.com) and log in
2. Click the "+" icon in the top-right corner and select "New repository"
3. Enter repository name: `video-transcription-tool`
4. Choose "Public" or "Private"
5. Click "Create repository"

### Step 2: Push Your Local Repository to GitHub

```bash
# Navigate to your project directory
cd /home/lintzuyang/Opencode/project/website

# Add the remote repository
# Replace the URL with your actual GitHub repository URL
git remote add origin https://github.com/yourusername/video-transcription-tool.git

# Push to GitHub
git push -u origin master
```

### Step 3: Verify the Push

1. Refresh your GitHub repository page
2. Verify all files are present
3. Check the commit history

### Step 4: Add a README (Already Done)

The repository already has a comprehensive bilingual README.md

### Step 5: Add a License (Optional)

```bash
# Create a LICENSE file (MIT License recommended)
echo "MIT License" > LICENSE
echo "" >> LICENSE
echo "Copyright (c) $(date +%Y) Your Name" >> LICENSE
echo "" >> LICENSE
echo "Permission is hereby granted..." >> LICENSE

# Add and commit the license
git add LICENSE
git commit -m "Add MIT License"
git push
```

### Step 6: Enable GitHub Features (Optional)

1. Go to "Settings" → "Features"
2. Enable "Issues" for bug tracking
3. Enable "Wiki" for documentation
4. Enable "Projects" for project management

### Step 7: Add Tags (Optional)

```bash
# Create a version tag
git tag -a v1.0 -m "First stable release"
git push origin v1.0
```

---

## 繁體中文

### 步驟1：在GitHub上創建新專案

1. 前往 [GitHub](https://github.com) 並登入
2. 點擊右上角的「+」圖示並選擇「New repository」
3. 輸入專案名稱：`video-transcription-tool`
4. 選擇「Public」或「Private」
5. 點擊「Create repository」

### 步驟2：將本地專案推送到GitHub

```bash
# 導航到您的專案目錄
cd /home/lintzuyang/Opencode/project/website

# 添加遠端專案
# 將網址替換為您實際的GitHub專案網址
git remote add origin https://github.com/yourusername/video-transcription-tool.git

# 推送到GitHub
git push -u origin master
```

### 步驟3：驗證推送

1. 刷新您的GitHub專案頁面
2. 驗證所有檔案是否存在
3. 檢查提交歷史

### 步驟4：添加README（已完成）

專案已經包含完整的雙語README.md檔案

### 步驟5：添加授權（選擇性）

```bash
# 創建LICENSE檔案（推薦MIT授權）
echo "MIT License" > LICENSE
echo "" >> LICENSE
echo "Copyright (c) $(date +%Y) Your Name" >> LICENSE
echo "" >> LICENSE
echo "Permission is hereby granted..." >> LICENSE

# 添加並提交授權
git add LICENSE
git commit -m "Add MIT License"
git push
```

### 步驟6：啟用GitHub功能（選擇性）

1. 前往「Settings」→「Features」
2. 啟用「Issues」進行錯誤追蹤
3. 啟用「Wiki」進行文件編寫
4. 啟用「Projects」進行專案管理

### 步驟7：添加標籤（選擇性）

```bash
# 創建版本標籤
git tag -a v1.0 -m "First stable release"
git push origin v1.0
```

---

## Additional Tips

### Working with Branches

```bash
# Create a development branch
git checkout -b development
git push -u origin development

# Merge to master when ready
git checkout master
git merge development
git push
```

### Using .gitignore

The project already has appropriate files in .gitignore:
- `__pycache__/` - Python cache files
- `venv/` - Virtual environment
- `output/` - Output files (can be regenerated)

### Collaborating

```bash
# Add collaborators in GitHub Settings
# They can then clone and contribute:
git clone https://github.com/yourusername/video-transcription-tool.git
cd video-transcription-tool
git checkout -b feature-branch
git add .
git commit -m "Add new feature"
git push origin feature-branch
# Create Pull Request on GitHub
```

---

## 額外提示

### 使用分支

```bash
# 創建開發分支
git checkout -b development
git push -u origin development

# 準備好時合併到master
git checkout master
git merge development
git push
```

### 使用.gitignore

專案已經有適當的.gitignore設定：
- `__pycache__/` - Python快取檔案
- `venv/` - 虛擬環境
- `output/` - 輸出檔案（可以重新生成）

### 協作

```bash
# 在GitHub設定中添加協作者
# 協作者可以克隆並貢獻：
git clone https://github.com/yourusername/video-transcription-tool.git
cd video-transcription-tool
git checkout -b feature-branch
git add .
git commit -m "Add new feature"
git push origin feature-branch
# 在GitHub上創建Pull Request
```