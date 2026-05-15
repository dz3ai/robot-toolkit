#!/bin/bash
# Mac mini Self-Hosted Runner Setup Script
# 用于 robot-toolkit 的 macOS wheels 构建
# 预计时间: 30 分钟

set -e  # 遇到错误立即退出

echo "=================================="
echo "Mac mini Self-Hosted Runner Setup"
echo "=================================="
echo ""

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# === 步骤 1: 环境准备 (5 分钟) ===
echo -e "${YELLOW}[1/7] 环境准备...${NC}"
echo ""

# 检查 Xcode Command Line Tools
if ! command -v xcodebuild &> /dev/null; then
    echo "安装 Xcode Command Line Tools..."
    xcode-select --install
    echo "请等待安装完成，然后按回车继续..."
    read
else
    echo "✓ Xcode Command Line Tools 已安装"
fi

# 检查 Homebrew
if ! command -v brew &> /dev/null; then
    echo "安装 Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    echo "✓ Homebrew 已安装"
fi

# 更新 Homebrew
echo "更新 Homebrew..."
brew update

# 安装构建工具
echo "安装构建工具..."
brew list cmake &> /dev/null || brew install cmake
brew list pyenv &> /dev/null || brew install pyenv

# 安装多版本 Python
echo "配置 Python 多版本..."
pyenv install 3.10.0 2>/dev/null || echo "Python 3.10.0 已安装"
pyenv install 3.11.0 2>/dev/null || echo "Python 3.11.0 已安装"
pyenv install 3.12.0 2>/dev/null || echo "Python 3.12.0 已安装"

# 配置 pyenv
if ! grep -q 'pyenv' ~/.zshrc 2>/dev/null; then
    echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
    echo '[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
    echo 'eval "$(pyenv init -)"' >> ~/.zshrc
fi

echo -e "${GREEN}✓ 步骤 1 完成: 环境准备${NC}"
echo ""

# === 步骤 2: 创建 GitHub Personal Access Token ===
echo -e "${YELLOW}[2/7] GitHub Personal Access Token${NC}"
echo ""
echo "请按以下步骤创建 Token:"
echo ""
echo "1. 访问: https://github.com/settings/tokens"
echo "2. 点击 'Generate new token (classic)'"
echo "3. 配置 token:"
echo "   - Name: mac-mini-runner"
echo "   - Expiration: 90 days (或 No expiration)"
echo "   - Scopes (勾选):"
echo "     ✓ repo (Full control of private repositories)"
echo "     ✓ admin:org (Read and write access to org and teams)"
echo "     ✓ workflow (Update GitHub Action workflows)"
echo "4. 点击 'Generate token'"
echo "5. 复制 token (只显示一次!)"
echo ""
echo "请输入生成的 token:"
read -s GITHUB_TOKEN
echo ""
echo -e "${GREEN}✓ Token 已保存${NC}"
echo ""

# === 步骤 3: 获取 Organization 信息 ===
echo -e "${YELLOW}[3/7] Organization 信息${NC}"
echo ""
echo "请输入你的 GitHub Organization 名称:"
read ORG_NAME
echo ""
echo "Organization: $ORG_NAME"
echo -e "${GREEN}✓${NC}"
echo ""

# === 步骤 4: 确定安装位置 ===
echo -e "${YELLOW}[4/7] 确定安装位置${NC}"
echo ""

# 默认安装目录
DEFAULT_RUNNER_DIR="$HOME/local/runner"
echo "请输入 runner 安装基础目录"
echo "默认: $DEFAULT_RUNNER_DIR"
read -p "安装目录 [$DEFAULT_RUNNER_DIR]: " INPUT_DIR

# 使用输入或默认值
if [ -z "$INPUT_DIR" ]; then
    RUNNER_DIR="$DEFAULT_RUNNER_DIR"
else
    # 扩展 ~ 为完整路径
    RUNNER_DIR="${INPUT_DIR/#\~/$HOME}"
fi

echo ""
echo "安装目录: $RUNNER_DIR"

# === 步骤 5: 检查磁盘空间 ===
echo -e "${YELLOW}[5/7] 检查磁盘空间${NC}"
echo ""

# 检查安装目录所在的卷
if [ -d "$RUNNER_DIR" ]; then
    # 目录已存在，检查其所在卷
    CHECK_PATH="$RUNNER_DIR"
else
    # 目录不存在，检查其父目录所在卷
    CHECK_PATH="$(dirname "$RUNNER_DIR")"
fi

# 获取可用空间（单位: GB）
AVAILABLE_GB=$(df -g "$CHECK_PATH" | tail -1 | awk '{print $4}')
AVAILABLE_MB=$((AVAILABLE_GB * 1024))

# 估算所需空间（保守估计）
REQUIRED_MB=5000  # 5GB (包括 runner、Python、构建缓存、临时文件)

echo "磁盘空间检查:"
echo "  检查路径: $CHECK_PATH"
echo "  可用空间: ${AVAILABLE_GB} GB"
echo "  预计需要: ~5 GB (runner + Python + 构建缓存)"
echo ""

# 检查空间是否足够
if [ $AVAILABLE_MB -lt $REQUIRED_MB ]; then
    echo -e "${RED}✗ 错误: 磁盘空间不足!${NC}"
    echo "  需要: ~5 GB"
    echo "  可用: ${AVAILABLE_GB} GB"
    echo ""
    echo "请清理磁盘空间或选择其他安装目录"
    echo ""
    read -p "是否继续安装? (y/N): " CONFIRM
    if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
        echo "安装已取消"
        exit 1
    fi
else
    echo -e "${GREEN}✓ 磁盘空间充足${NC}"
fi

echo ""

# === 步骤 6: 安装 Runner ===
echo -e "${YELLOW}[6/7] 安装 GitHub Actions Runner${NC}"
echo ""

# 创建 runner 目录
echo "创建安装目录: $RUNNER_DIR"
mkdir -p "$RUNNER_DIR"
cd "$RUNNER_DIR"

# 下载最新 runner (检测架构)
ARCH=$(uname -m)
if [ "$ARCH" = "arm64" ]; then
    RUNNER_OS="osx-arm64"
else
    RUNNER_OS="osx-x64"
fi

echo "检测到架构: $ARCH"
echo "下载 runner for $RUNNER_OS..."

# 获取最新版本
LATEST_VERSION=$(curl -s https://api.github.com/repos/actions/runner/releases/latest | grep '"tag_name"' | sed -E 's/.*"([^"]+)".*/\1/')
echo "最新版本: $LATEST_VERSION"

# 下载 runner
RUNNER_URL="https://github.com/actions/runner/releases/download/$LATEST_VERSION/actions-runner-$RUNNER_OS-$LATEST_VERSION.tar.gz"
echo "正在下载..."
curl -o actions-runner.tar.gz -L "$RUNNER_URL"

# 检查下载是否成功
if [ ! -f "actions-runner.tar.gz" ]; then
    echo -e "${RED}✗ 下载失败${NC}"
    exit 1
fi

# 解压
echo "解压 runner..."
tar xzf ./actions-runner.tar.gz

# 配置 runner
echo "配置 runner (Organization: $ORG_NAME)..."
./config.sh \
    --url "https://github.com/$ORG_NAME" \
    --token "$GITHUB_TOKEN" \
    --name "mac-mini-$(hostname)-$RUNNER_OS" \
    --labels "macos,$RUNNER_OS,self-hosted" \
    --work "_work" \
    --unattended \
    --replace

echo -e "${GREEN}✓ 步骤 6 完成: Runner 已配置${NC}"
echo ""

# === 步骤 7: 安装为服务 ===
echo -e "${YELLOW}[7/7] 安装 Runner 服务${NC}"
echo ""

# 安装服务
echo "安装 launchd 服务..."
./svc.sh install

# 启动服务
echo "启动 runner 服务..."
./svc.sh start

# 检查状态
sleep 3
if ./svc.sh status | grep -q "running"; then
    echo -e "${GREEN}✓ Runner 服务运行中${NC}"
else
    echo "⚠️  Runner 服务可能未启动，请检查:"
    echo "   ./svc.sh status"
    echo "   cat /tmp/github-runner-$USER.log"
fi

echo ""

# === 验证 ===
echo -e "${YELLOW}验证 Runner 在线状态${NC}"
echo ""
echo "请在 GitHub 上验证:"
echo ""
echo "1. 访问: https://github.com/$ORG_NAME/settings/actions/runners"
echo "2. 查找 runner: mac-mini-$(hostname)-$RUNNER_OS"
echo "3. 状态应该显示: ▼ Online (Idle)"
echo ""
echo "如果没有看到 runner 在线:"
echo "  - 检查: cd $RUNNER_DIR && ./svc.sh status"
echo "  - 日志: cat /tmp/github-runner-$USER.log"
echo "  - 重启: cd $RUNNER_DIR && ./svc.sh restart"
echo ""

# === 完成 ===
echo "=================================="
echo -e "${GREEN}✓ Setup 完成!${NC}"
echo "=================================="
echo ""
echo "安装摘要:"
echo "  Runner 目录: $RUNNER_DIR"
echo "  架构: $RUNNER_OS"
echo "  Organization: $ORG_NAME"
echo "  Runner 名称: mac-mini-$(hostname)-$RUNNER_OS"
echo ""
echo "服务管理:"
echo "  启动: cd $RUNNER_DIR && ./svc.sh start"
echo "  停止: cd $RUNNER_DIR && ./svc.sh stop"
echo "  状态: cd $RUNNER_DIR && ./svc.sh status"
echo "  重启: cd $RUNNER_DIR && ./svc.sh restart"
echo ""
echo "下一步:"
echo "  1. 在 GitHub 上验证 runner 在线"
echo "  2. 推送测试 commit 触发构建"
echo ""
echo "配置文件位置:"
echo "  - Runner config: $RUNNER_DIR/.runner"
echo "  - Service plist: ~/Library/LaunchAgents/com.github.runner.$USER.plist"
echo "  - 工作目录: $RUNNER_DIR/_work"
echo ""
