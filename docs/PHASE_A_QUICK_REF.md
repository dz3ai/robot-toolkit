# Phase A: 快速参考卡

## 🚀 快速开始（3 步）

### 1. 复制脚本到 Mac mini
```bash
scp docs/scripts/mac_mini_runner_setup.sh dannyz@<mac-mini-ip>:~/
```

### 2. SSH 到 Mac mini 并运行
```bash
ssh dannyz@<mac-mini-ip>
chmod +x ~/mac_mini_runner_setup.sh
~/mac_mini_runner_setup.sh
```

**脚本会询问**:
- 安装目录（默认: `$HOME/local/runner`）
- GitHub Token
- Organization 名称

**自动检查**:
- ✓ 磁盘空间（需要 5GB）

### 3. 验证
```
访问: https://github.com/YOUR_ORG/settings/actions/runners
查找: mac-mini-<hostname>-osx-arm64
状态: ▼ Online (Idle)
```

---

## 📋 必需信息

**创建 GitHub Token**:
- URL: https://github.com/settings/tokens
- Name: `mac-mini-runner`
- Scopes: ✅ repo ✅ admin:org ✅ workflow

**Organization 名称**: `YOUR_ORG` (替换为实际)

---

## ⚙️ Runner 管理

```bash
cd ~/actions-runner

./svc.sh start    # 启动
./svc.sh stop     # 停止
./svc.sh restart  # 重启
./svc.sh status   # 状态
```

---

## ✅ 验证构建

```bash
# 在开发机器上
cd /home/dannyz/src/github/robot-toolkit
git commit --allow-empty -m "test self-hosted runner"
git push origin main

# 观察 CI
# https://github.com/dz3ai/robot-toolkit/actions
```

---

## 🐛 故障排除

| 问题 | 解决 |
|------|------|
| Runner 不在线 | `./svc.sh restart` |
| 构建失败 | `brew install cmake` |
| 权限问题 | 验证 Token scopes |
| 超时 | 检查网络/Mac mini 性能 |

---

## 📚 详细文档

- 完整指南: `docs/PHASE_A_SELF_HOSTED_RUNNER.md`
- 设计文档: `docs/plans/2026-05-14-scope-roadmap-review.md`

---

## 🎯 预期结果

- ✓ macOS wheels 构建时间: ~20 分钟
- ✓ 无 queued 等待
- ✓ C++ 扩展包含在 PyPI 包中
- ✓ 服务所有项目

---

**预计时间**: 30 分钟
**完成后**: 继续 Phase B (Meshcat)
