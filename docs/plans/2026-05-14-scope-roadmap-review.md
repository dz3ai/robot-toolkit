# robot-toolkit Project Scope & Roadmap Review

**Date**: 2026-05-14
**Status**: Design approved, ready for implementation

## Executive Summary

基于**工程化工具箱**设计思想，完成项目范围和路线图审查：
- ✓ 保持完整 8 模块工具集（非 monolithic 平台）
- ✓ 识别并优先处理技术债务
- ✓ 设计多协议硬件抽象层架构

**优先次序**: A (优化当前范围) → D (技术债务清理) → B (扩展新方向) → C (发布准备)

---

## 1. 当前范围确认

### 设计哲学：工程化工具箱

robot-toolkit 定位为**工具集**，类似 numpy/scipy：
- ✓ **模块独立** - 每个工具精确、高效
- ✓ **可组合** - 根据需求选择使用
- ✓ **可扩展** - 新需求创造新工具
- ✓ **非 monolithic** - 不是一体化平台

### 当前 8 个模块（全部保留）

| 模块 | 功能 | 状态 |
|------|------|------|
| IK 求解 | DH参数FK/IK, Jacobian | ✓ 完成 |
| 刚体动力学 | RNEA, CRBA | ✓ 完成 |
| 轨迹规划 | 7种插值方法 | ✓ 完成 |
| 碰撞检测 | Sphere/Capsule/Box | ✓ 完成 |
| 路径规划 | RRT* | ✓ 完成 |
| 可视化 | Matplotlib 3D | ⚠️ 需升级 |
| URDF 解析 | URDF→DH | ✓ 完成 |
| ROS2 集成 | Service server | ✓ 完成 |

**代码统计**:
- Python: ~4,500 行 (18源文件 + 5测试)
- C++: ~500 行 (2扩展模块)
- 测试: 60+ 测试用例
- 文档: 10+ 文档文件

---

## 2. 技术债务清理计划

### 优先级 A: 部署（C++ 扩展分发）

**问题**: CI macOS runners queued 34+ 分钟
**方案**: 自托管 macOS runner（Organization 级）

#### Mac mini 自托管 Runner 配置

**硬件**: 用户已有 Mac mini 可用

**架构**: 混合 CI
```
GitHub Actions (Ubuntu/Windows)
  +
Self-hosted macOS runner (Mac mini)
  ↓
Artifacts 合并
  ↓
PyPI 发布
```

**配置步骤** (30 分钟):
1. Mac mini 环境准备
2. 创建 GitHub Personal Access Token
3. Organization 级 runner 注册
4. 安装并启动 runner 服务
5. 修改 `build-wheels.yml`
6. 测试构建

**优势**:
- ✓ 一台 Mac mini 服务所有项目
- ✓ 自动排队管理
- ✓ 构建时间可预测 (~20 分钟)
- ✓ 无 GitHub Actions 分钟数限制

**关键配置**:
```yaml
# .github/workflows/build-wheels.yml
jobs:
  build_wheels:
    runs-on: [self-hosted, macos]  # 自托管
    strategy:
      matrix:
        os: [ubuntu-22.04, windows-2022]  # 移除 macos-13
```

**PyPI 包验证**:
- ✓ setup.py 已配置 C++ 扩展 (`ik_fast.cpp`, `robot_dyn_fast.cpp`)
- ✓ cibuildwheel 会自动编译并打包到 wheels
- ✓ 用户 `pip install` 后直接可用 137x 加速

**待修复**: setup.py 版本号 0.2.0 → 0.3.0

---

### 优先级 B: 性能优化（可视化升级）

**问题**: matplotlib 性能限制 (~2-5 FPS)
**需求**: A (交互式开发) + C (实时监控)
**方案**: Meshcat web-based 可视化

#### Meshcat 可视化架构

**选择原因**:
- ✓ 原生 web-based (浏览器访问)
- ✓ Jupyter 原生支持 (`vis.jupyter_cell()`)
- ✓ 高性能 (30-60 FPS)
- ✓ 机器人专用 (mesh, transform, trajectory)
- ✓ WebSocket 支持 (为实时监控准备)

**实时监控架构**:
```
机器人实验样机 (未来)
  ↓ (标准协议: ROS2/Modbus/TCP)
硬件抽象层 (HAL)
  ↓ (WebSocket)
Meshcat Visualizer
  ↓ (Web Browser)
开发人员监控界面
```

**新增模块**:
```
robot_ik/
└── visualize_meshcat.py  # Meshcat 可视化器
```

**使用示例**:
```python
# Jupyter 交互式开发
from robot_ik import MeshcatVisualizer, six_dof_articulated

vis = MeshcatVisualizer()
vis.start_jupyter()  # notebook 中显示

robot = six_dof_articulated()
q = robot.ik_solve(target)
vis.update_robot(q)  # 交互式调试
```

---

## 3. 新功能扩展：硬件抽象层

### 设计原则

基于机器人开发 OS/中间件多样性：
- ✓ **协议无关** - 核心算法不依赖特定硬件
- ✓ **可插拔** - 用户选择需要的协议实现
- ✓ **可选依赖** - ROS2/Modbus 等作为 extras 安装
- ✓ **统一接口** - 所有协议共享相同 API

### 架构设计

**分层架构**:
```
robot-toolkit 核心算法 (IK, Dynamics, Trajectory)
  ↓
HardwareInterface (ABC)
  - get_joint_positions()
  - set_joint_targets()
  - get_joint_velocities()
  - stop()
  ↓
┌────────┬────────┬────────┬────────┐
│Simulated│ ROS2   │ Modbus │ Custom │
│(built-in)│(opt)  │ (opt)  │ (user) │
└────────┴────────┴────────┴────────┘
```

**模块结构**:
```
robot_ik/
├── hardware/
│   ├── __init__.py
│   ├── base.py              # HardwareInterface ABC
│   ├── simulated.py         # 内置仿真实现
│   ├── ros2.py              # ROS2 实现 (可选)
│   ├── modbus.py            # Modbus 实现 (可选)
│   └── registry.py          # 协议注册与工厂
```

**关键设计**:
```python
# 统一接口
class HardwareInterface(ABC):
    @abstractmethod
    def get_joint_positions(self) -> np.ndarray: pass
    
    @abstractmethod
    def set_joint_targets(self, q: np.ndarray): pass
    
    @abstractmethod
    def get_joint_velocities(self) -> np.ndarray: pass
    
    @abstractmethod
    def stop(self): pass

# 协议工厂
hardware = HardwareRegistry.create("simulated", dof=6)
hardware = HardwareRegistry.create("ros2", node_name="robot_arm")
hardware = HardwareRegistry.create("modbus", host="192.168.1.100")
```

**依赖管理**:
```toml
[project.optional-dependencies]
viz = ["matplotlib>=3.7.0"]
ros2 = ["rclpy>=3.0.0"]
modbus = ["pymodbus>=3.0.0"]
meshcat = ["meshcat>=0.3.0"]
all = ["robot-ik[viz,ros2,modbus,meshcat]"]
```

---

## 4. 实施路线图

### Phase A: 自托管 Runner 设置 (1-2 天)
- [ ] Mac mini 环境配置
- [ ] GitHub Organization runner 注册
- [ ] 修改 `build-wheels.yml`
- [ ] 测试构建
- [ ] 修复 setup.py 版本号

### Phase B: Meshcat 可视化 (2-3 天)
- [ ] 实现 `visualize_meshcat.py`
- [ ] Jupyter 集成测试
- [ ] 实时流式更新支持
- [ ] 文档和示例

### Phase C: 硬件抽象层 (3-5 天)
- [ ] 实现 `hardware/base.py`, `simulated.py`, `registry.py`
- [ ] 单元测试 (TDD)
- [ ] 集成测试
- [ ] 文档和使用示例

### Phase D: 可选协议实现 (后续)
- [ ] ROS2 接口 (`ros2.py`)
- [ ] Modbus 接口 (`modbus.py`)
- [ ] 用户自定义协议示例

### Phase E: v0.4.0 发布
- [ ] 整合所有新功能
- [ ] 完整文档更新
- [ ] PyPI 发布 (macOS wheels 通过自托管 runner)

---

## 5. 设计决策记录

| 决策 | 选择 | 原因 |
|------|------|------|
| **范围** | 保持完整 8 模块 | 工程化工具箱思想 |
| **CI** | 自托管 macOS runner | 解决 queued 问题，服务多项目 |
| **可视化** | Meshcat | Web-based + Jupyter + 高性能 |
| **硬件协议** | 多协议支持 | 机器人生态多样性，可扩展 |
| **部署** | Organization 级 runner | 一台 Mac mini 服务所有项目 |
| **依赖管理** | 可选 extras | 用户按需安装，无强制依赖 |

---

## 6. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| Mac mini 维护成本 | 中 | 自动化更新、监控脚本 |
| Meshcat 性能瓶颈 | 低 | 30-60 FPS 足够需求 |
| HAL 接口变更 | 高 | 严格版本控制、废弃警告 |
| 多协议维护成本 | 中 | 社区贡献、插件化架构 |

---

## 7. 成功指标

- ✓ v0.3.0 发布到 PyPI (包含 C++ 扩展)
- ✓ macOS 构建时间 <30 分钟 (无 queued 等待)
- ✓ Meshcat 集成可用 (Jupyter + Web)
- ✓ HAL 框架实现 (至少 2 个协议)
- ✓ 用户采用率提升 (pip install 统计)

---

## 8. 相关文档

- `ROADMAP.md` - 项目路线图
- `README.md` - 快速开始
- `docs/challenges.md` - 技术挑战
- `.github/workflows/build-wheels.yml` - CI 配置

---

**批准**: 设计已确认，可以开始实施

**下一步**: Phase A - 自托管 Runner 设置
