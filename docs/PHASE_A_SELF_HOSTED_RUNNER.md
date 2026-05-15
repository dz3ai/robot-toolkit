# Phase A: Mac mini 自托管 Runner 设置指南

**预计时间**: 30 分钟
**目标**: 在 Mac mini 上配置 GitHub Actions 自托管 runner，解决 macOS wheels 构建排队问题

---

## 前提条件

- Mac mini 已联网
- macOS 11+ (Big Sur 或更新)
- 4GB+ RAM
- 20GB+ 磁盘空间
- 有 GitHub Organization 的管理员权限

---

## 步骤 1: 准备设置脚本

设置脚本已创建: `/tmp/mac_mini_runner_setup.sh`

**复制到 Mac mini**:

```bash
# 方法 1: 通过 AirDrop 或 USB
# 复制脚本到 Mac mini

# 方法 2: 通过 SSH (如果 Mac mini 已启用远程登录)
scp /tmp/mac_mini_runner_setup.sh dannyz@<mac-mini-ip>:~/

# 方法 3: 直接在 Mac mini 上创建
# 复制脚本内容，在 Mac mini 上创建文件
```

---

## 步骤 2: 在 Mac mini 上运行设置脚本

```bash
# SSH 到 Mac mini (或直接在 Mac mini 上操作)
ssh dannyz@<mac-mini-ip>

# 进入脚本目录
cd ~

# 添加执行权限
chmod +x mac_mini_runner_setup.sh

# 运行设置脚本
./mac_mini_runner_setup.sh
```

**脚本会引导你完成**:
1. ✓ 安装 Xcode Command Line Tools
2. ✓ 安装 Homebrew, CMake, pyenv
3. ✓ 配置 Python 3.10/3.11/3.12
4. ✓ 提示创建 GitHub Token
5. ✓ 下载并配置 GitHub Actions Runner
6. ✓ 安装为开机自启动服务

---

## 步骤 3: 创建 GitHub Personal Access Token

脚本会提示你创建 token，步骤如下:

1. **访问**: https://github.com/settings/tokens
2. **点击**: "Generate new token (classic)"
3. **配置 token**:
   - Name: `mac-mini-runner`
   - Expiration: `90 days` 或 `No expiration`
   - Scopes (勾选以下):
     - ✅ `repo` (Full control of private repositories)
     - ✅ `admin:org` (Read and write access to org and teams)
     - ✅ `workflow` (Update GitHub Action workflows)
4. **点击**: "Generate token"
5. **复制 token** (只显示一次！粘贴到脚本中)

---

## 步骤 4: 提供 Organization 信息

脚本会提示:
```
请输入你的 GitHub Organization 名称:
```

输入你的 GitHub Organization 名称（例如: `dz3ai` 或其他）

---

## 步骤 5: 验证 Runner 在线

脚本完成后，验证 runner 已注册并在线:

1. **访问**: https://github.com/YOUR_ORG/settings/actions/runners
2. **查找 runner**: `mac-mini-<hostname>-osx-arm64` 或 `osx-x64`
3. **检查状态**: 应该显示 `▼ Online (Idle)`

如果没有看到 runner 在线:
```bash
# 在 Mac mini 上检查服务状态
cd ~/actions-runner
./svc.sh status

# 查看日志
cat /tmp/github-runner-$USER.log

# 重启服务
./svc.sh restart
```

---

## 步骤 6: 测试 Runner

**创建测试 commit** (在开发机器上):

```bash
cd /home/dannyz/src/github/robot-toolkit

# 创建测试 commit
git commit --allow-empty -m "test self-hosted runner"

# 推送触发 CI
git push origin main
```

**观察 CI 运行**:
- 访问: https://github.com/dz3ai/robot-toolkit/actions
- 查看最新的 workflow run
- macOS wheels 应该在 `build_macos` job 中运行
- 预计构建时间: 15-20 分钟（不再 queued）

---

## 步骤 7: 验证 PyPI 包包含 C++ 扩展

**构建成功后**，下载并检查 wheel:

```bash
# 下载 wheel
pip download robot-ik==0.3.0 --only-binary :all: --platform macosx_11_0_arm64

# 解压检查
unzip robot_ik-0.3.0-cp310-*.whl -d /tmp/robot_ik_check
ls /tmp/robot_ik_check/robot_ik/

# 应该看到 C++ 扩展:
# ik_fast.so (或 .dylib)
# robot_dyn_fast.so (或 .dylib)
```

---

## Runner 管理命令

**在 Mac mini 上管理服务**:

```bash
cd ~/actions-runner

# 启动
./svc.sh start

# 停止
./svc.sh stop

# 重启
./svc.sh restart

# 状态
./svc.sh status

# 查看日志
cat /tmp/github-runner-$USER.log
```

---

## 故障排除

### 问题 1: Runner 没有显示在 GitHub 上

**检查**:
```bash
cd ~/actions-runner
./svc.sh status
```

**解决**:
```bash
./svc.sh restart
# 检查网络连接
# 验证 GitHub Token 有效期
```

### 问题 2: 构建失败（缺少依赖）

**症状**: `brew install cmake` 失败

**解决**:
```bash
# 在 Mac mini 上手动安装
brew update
brew install cmake
brew install pyenv
```

### 问题 3: 权限问题

**症状**: Runner 无法拉取代码或上传 artifacts

**解决**:
- 验证 Token scopes 包含 `repo`, `admin:org`, `workflow`
- 确认 Runner 有组织权限: Settings → Actions → Runner groups

### 问题 4: 构建超时

**症状**: macOS 构建超过 60 分钟

**解决**:
- 检查 Mac mini 性能（CPU/内存使用）
- 减少构建的 Python 版本（只保留 cp311-*）
- 检查网络带宽

---

## 多项目使用

**Organization 级 runner 自动服务所有项目**:

```yaml
# 其他项目的 workflow
jobs:
  build:
    runs-on: [self-hosted, macos]
```

**排队管理**: 多个项目触发时自动排队，按顺序执行

---

## 下一步

✓ Phase A 完成后:
- ✓ macOS wheels 构建时间可预测 (~20 分钟)
- ✓ 无 GitHub Actions queued 等待
- ✓ 服务于组织的所有项目

**继续**: Phase B - Meshcat 可视化集成

---

## 参考文档

- GitHub Actions Self-hosted runners: https://docs.github.com/en/actions/hosting-your-own-runners
- cibuildwheel documentation: https://cibuildwheel.readthedocs.io/
- robot-toolkit design: `docs/plans/2026-05-14-scope-roadmap-review.md`
