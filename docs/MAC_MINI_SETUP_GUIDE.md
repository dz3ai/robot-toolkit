# Mac mini Runner 设置执行指南

**目标机器**: danny@192.168.3.143
**脚本位置**: `docs/scripts/mac_mini_runner_setup.sh`

---

## 方法 1: 直接在 Mac mini 上下载脚本（推荐）

### 1. SSH 连接到 Mac mini

```bash
ssh danny@192.168.3.143
# 输入 Mac mini 密码
```

### 2. 下载 robot-toolkit 仓库

```bash
# 克隆仓库（如果还没有）
git clone https://github.com/dz3ai/robot-toolkit.git
cd robot-toolkit

# 或更新已有仓库
git pull
```

### 3. 运行设置脚本

```bash
cd docs/scripts
chmod +x mac_mini_runner_setup.sh
./mac_mini_runner_setup.sh
```

---

## 方法 2: 通过 AirDrop/USB 复制

### 1. 复制脚本到 Mac mini

```bash
# 在开发机器上
scp docs/scripts/mac_mini_runner_setup.sh danny@192.168.3.143:~/
# 输入 Mac mini 密码
```

### 2. SSH 连接并运行

```bash
ssh danny@192.168.3.143
# 输入密码

# 运行脚本
chmod +x ~/mac_mini_runner_setup.sh
~/mac_mini_runner_setup.sh
```

---

## 脚本执行流程

运行后，脚本会引导你完成 **7 个步骤**：

### 步骤 1/7: 环境准备
- ✓ 检查 Xcode Command Line Tools
- ✓ 安装/更新 Homebrew
- ✓ 安装 CMake, pyenv
- ✓ 配置 Python 3.10/3.11/3.12

**预计时间**: 5-10 分钟

---

### 步骤 2/7: GitHub Token

**创建 Token**:
1. 访问: https://github.com/settings/tokens
2. 点击 "Generate new token (classic)"
3. 配置:
   - Name: `mac-mini-runner`
   - Expiration: `90 days` 或 `No expiration`
   - Scopes: ✅ repo ✅ admin:org ✅ workflow
4. 生成并复制 token

**脚本提示**:
```
请输入生成的 token:
[粘贴 token，不会显示]
```

---

### 步骤 3/7: Organization 名称

**脚本提示**:
```
请输入你的 GitHub Organization 名称:
[输入你的 org 名称]
```

例如: `dz3ai` 或其他

---

### 步骤 4/7: 安装位置（新增）

**脚本提示**:
```
请输入 runner 安装基础目录
默认: /Users/danny/local/runner
安装目录: [按回车使用默认，或输入自定义路径]
```

**推荐**:
- 使用默认位置: `/Users/danny/local/runner`
- 或选择有足够空间的路径

**检查点**:
```
磁盘空间检查:
  检查路径: /Users/danny
  可用空间: XXX GB
  预计需要: ~5 GB
✓ 磁盘空间充足
```

---

### 步骤 5/7: 磁盘空间检查（新增）

脚本会自动检查：
- ✓ 最少需要 5GB
- ✓ 包括 runner + Python + 构建缓存
- ✓ 空间不足时会询问是否继续

**如果空间不足**:
```
✗ 错误: 磁盘空间不足!
  需要: ~5 GB
  可用: 2 GB

请清理磁盘空间或选择其他安装目录

是否继续安装? (y/N):
```

---

### 步骤 6/7: 安装 Runner

- ✓ 下载 GitHub Actions Runner
- ✓ 解压并配置
- ✓ 注册到 Organization

**预计时间**: 3-5 分钟

---

### 步骤 7/7: 安装服务

- ✓ 安装 launchd 服务（开机自启）
- ✓ 启动 runner 服务
- ✓ 检查运行状态

---

## 验证 Runner 在线

### 在 GitHub 上验证

访问: `https://github.com/YOUR_ORG/settings/actions/runners`

查找: `mac-mini-Mac-mini的名称-osx-arm64` 或 `osx-x64`

状态应该显示: `▼ Online (Idle)`

---

## 服务管理命令

安装完成后，可以使用以下命令管理：

```bash
# 进入 runner 目录
cd ~/local/runner  # 或你选择的安装目录

# 启动
./svc.sh start

# 停止
./svc.sh stop

# 重启
./svc.sh restart

# 状态
./svc.sh status
```

---

## 常见问题

### SSH 连接失败

```bash
# 检查 Mac mini 是否启用 SSH
# 系统设置 → 共享 → 远程登录 → 打开
```

### 权限问题

```bash
# 确保脚本有执行权限
chmod +x mac_mini_runner_setup.sh

# 或使用 bash 运行
bash mac_mini_runner_setup.sh
```

### 磁盘空间不足

```bash
# 检查空间
df -h

# 清理 Xcode 缓存
rm -rf ~/Library/Developer/Xcode/DerivedData/*

# 清理 Homebrew 缓存
brew cleanup

# 然后重新运行脚本
```

---

## 预期结果

✓ 完成后:
- Runner 运行在 `/Users/danny/local/runner`（或自定义路径）
- 服务开机自启
- 在 GitHub 上显示为 Online
- 准备构建 macOS wheels

---

## 下一步

验证 runner 在线后：
1. 推送测试 commit 触发构建
2. 观察 CI 运行
3. 验证 macOS wheels 构建成功

---

**预计总时间**: 20-30 分钟

**准备好后，在 Mac mini 上执行**:
```bash
ssh danny@192.168.3.143
cd ~/robot-toolkit/docs/scripts  # 或克隆仓库
./mac_mini_runner_setup.sh
```
