# Phase B Design: Meshcat Visualization Integration

**Date**: 2026-05-14
**Status**: Design approved, ready for implementation
**Estimated Time**: 2-3 days

---

## Overview

集成 Meshcat web-based 3D 可视化到 robot-toolkit，支持交互式开发和实时监控。

**核心需求**:
- A. 交互式开发调试（Jupyter Notebook）
- C. 实时监控（30Hz 更新）

**技术方案**:
- Web-based 3D 可视化
- 高性能（30-60 FPS）
- 程序化生成机器人模型（默认）+ 可选真实 mesh
- Threading 实时流式更新

---

## Architecture

### Module Organization

```
robot_ik/
├── visualize.py              # matplotlib 实现（保持不变）
├── visualize_meshcat.py      # Meshcat 实现（新增）
└── meshes/                   # 可选 mesh 资源（未来）
    └── README.md
```

**设计决策**:
- ✓ **平行模块** - 不破坏现有 matplotlib 代码
- ✓ **用户选择** - 根据需求选择可视化后端
- ✓ **工具箱思想** - 独立、可组合

---

## API Design (Object-Oriented)

### Main Class

```python
class MeshcatVisualizer:
    """Meshcat 3D 可视化器
    
    特性:
    - Web-based（浏览器访问）
    - Jupyter notebook 原生支持
    - 实时流式更新（30Hz+）
    - 程序化生成 3D 模型（默认）
    - 可选加载真实 mesh
    """
    
    def __init__(self, port=7000, zmq_url=None):
        """初始化可视化器
        
        Args:
            port: Meshcat server 端口（默认 7000）
            zmq_url: ZeroMQ URL（可选，默认自动生成）
        
        Raises:
            MeshcatError: 端口冲突或 zmq 初始化失败
        """
        
    def set_robot(self, robot, color=None):
        """设置机器人模型
        
        Args:
            robot: six_dof_articulated 实例
            color: 连杆颜色 [R, G, B, A]（可选）
        """
        
    def update_joints(self, q):
        """更新关节角度
        
        Args:
            q: 关节角度数组 (6,)
        """
        
    def start_jupyter(self):
        """在 Jupyter Notebook 中显示
        
        Returns:
            IPython.display.IFrame
        """
        
    def start_realtime_stream(self, hardware, freq=30):
        """启动实时监控流
        
        Args:
            hardware: HardwareInterface 实例
            freq: 更新频率（Hz，默认 30）
        
        Raises:
            RuntimeError: 流已在运行
        """
        
    def stop_realtime_stream(self):
        """停止实时监控流"""
```

---

## Implementation Details

### 1. Procedural 3D Model Generation

**默认行为**: 使用简单几何体表示 6-DOF 机械臂

```python
def _create_robot_mesh(self, robot):
    """程序化生成机器人 3D 模型
    
    使用简单几何体:
    - 基座: Box (宽x高x深)
    - 连杆 1-6: Cylinder (长度, 半径)
    - 关节 1-6: Sphere (半径)
    - 末端执行器: Triad (坐标系)
    """
    import meshcat.geometry as mg
    
    # 基座
    self.vis["base"].set_object(mg.Box([0.1, 0.1, 0.1]))
    
    # 连杆和关节
    for i in range(6):
        # 连杆
        length = robot.link_lengths[i] if hasattr(robot, 'link_lengths') else 0.5
        self.vis[f"link{i}"].set_object(
            mg.Cylinder(length, 0.05)
        )
        
        # 关节
        self.vis[f"joint{i}"].set_object(
            mg.Sphere(0.06)
        )
        
        # 坐标系
        self.vis[f"frame{i}"].set_object(
            mg.Triad()
        )
```

**扩展点**: 未来可添加 `load_meshes(path)` 加载真实 STL/OBJ 模型

---

### 2. Joint Update (Forward Kinematics)

```python
def update_joints(self, q):
    """更新关节角度
    
    计算每个连杆的位姿（DH 参数或 homogeneous 变换）
    更新 meshcat 中的 mesh 位置
    """
    # 计算 FK
    T_base = np.eye(4)
    transforms = [T_base]
    
    for i in range(6):
        # 计算 link i 的变换矩阵
        T_i = self._compute_link_transform(i, q[i])
        transforms.append(T_i)
        
        # 更新 meshcat 中的位置
        self.vis[f"link{i}"].set_transform(T_i)
        self.vis[f"joint{i}"].set_transform(T_i)
```

---

### 3. Jupyter Integration

```python
def start_jupyter(self):
    """在 Jupyter Notebook 中嵌入可视化器
    
    Returns:
        IPython.display.IFrame
    """
    from IPython.display import IFrame
    
    # 获取 meshcat URL
    url = self.vis.viewer_url()
    
    # 返回嵌入式 iframe
    return IFrame(src=url, width=800, height=600)
```

---

### 4. Real-time Streaming (Threading)

**架构**: 后台线程定期读取硬件数据并更新可视化

```python
def start_realtime_stream(self, hardware, freq=30):
    """启动实时监控流（后台线程）
    
    Args:
        hardware: HardwareInterface 实例
        freq: 更新频率（Hz，默认 30）
    """
    if self._streaming:
        raise RuntimeError("实时流已在运行")
    
    self._streaming = True
    self._stop_event = threading.Event()
    
    def update_loop():
        """后台更新循环"""
        while not self._stop_event.is_set():
            try:
                # 读取关节位置
                q = hardware.get_joint_positions()
                
                # 更新可视化
                self.update_joints(q)
                
            except Exception as e:
                logger.error(f"实时更新错误: {e}")
                # 继续运行（不中断流）
            
            # 控制频率
            self._stop_event.wait(1.0 / freq)
    
    # 启动后台线程
    self._stream_thread = threading.Thread(
        target=update_loop,
        daemon=True  # 主线程退出时自动终止
    )
    self._stream_thread.start()

def stop_realtime_stream(self):
    """停止实时监控流"""
    if not self._streaming:
        return
    
    self._stop_event.set()
    self._stream_thread.join(timeout=5.0)
    self._streaming = False
```

---

## Usage Examples

### Interactive Development (Jupyter)

```python
# Jupyter Notebook
from robot_ik import MeshcatVisualizer, six_dof_articulated

# 创建可视化器
vis = MeshcatVisualizer()
robot = six_dof_articulated()

# 设置机器人模型
vis.set_robot(robot)

# 在 notebook 中显示
display(vis.start_jupyter())

# 交互式调试
target = np.array([0.5, 0.3, 0.4])
success, q, _, _ = robot.ik_solve(target)

if success:
    vis.update_joints(q)  # 实时更新显示
```

### Real-time Monitoring

```python
from robot_ik.hardware import SimulatedHardware

# 创建硬件接口（模拟）
hardware = SimulatedHardware(dof=6)

# 创建可视化器
vis = MeshcatVisualizer()
vis.set_robot(robot)

# 启动实时流（30Hz）
vis.start_realtime_stream(hardware, freq=30)

# 机器人运行时，浏览器实时显示
# ... 后台自动更新 ...

# 停止流
vis.stop_realtime_stream()
```

### Future: Real Hardware

```python
from robot_ik.hardware import ROS2HardwareInterface

# 连接真实机器人
hardware = ROS2HardwareInterface("/robot_arm")
vis = MeshcatVisualizer()
vis.set_robot(robot)

# 实时监控
vis.start_realtime_stream(hardware, freq=30)
```

---

## Error Handling

### Exception Hierarchy

```python
class MeshcatVisualizer:
    class MeshcatError(Exception):
        """Meshcat 可视化错误"""
        pass
    
    class StreamingError(MeshcatError):
        """实时流式更新错误"""
        pass
    
    class InitializationError(MeshcatError):
        """初始化错误"""
        pass
```

### Error Handling Strategy

- **初始化失败**: 抛出 `MeshcatError`，端口冲突时自动重试
- **实时流错误**: 记录日志但继续运行（不中断监控）
- **并发流启动**: 抛出 `RuntimeError`，防止多个流同时运行
- **硬件断开**: 捕获异常，用户可选择停止或重试

---

## Configuration

### Visualization Config

```python
VIS_CONFIG = {
    'default_port': 7000,
    'default_freq': 30,      # 实时更新频率
    'timeout': 10.0,         # 连接超时
    'max_retries': 3,        # 端口冲突重试次数
}
```

### Robot Model Config (Procedural Generation)

```python
ROBOT_MODEL_CONFIG = {
    'base_size': [0.1, 0.1, 0.1],
    'link_radius': 0.05,
    'joint_radius': 0.06,
    'default_color': [0.3, 0.6, 0.9, 1.0],  # RGBA
}
```

---

## Testing Strategy (TDD)

### Test Files

```
tests/
├── test_visualize_meshcat.py         # 单元测试
└── test_integration_meshcat.py       # 集成测试
```

### Unit Tests

```python
# test_visualize_meshcat.py
import pytest
import numpy as np
from robot_ik.visualize_meshcat import MeshcatVisualizer
from robot_ik import six_dof_articulated

def test_visualizer_initialization():
    """测试可视化器初始化"""
    vis = MeshcatVisualizer(port=7001)
    assert vis.vis is not None
    assert not vis._streaming

def test_set_robot():
    """测试设置机器人模型"""
    vis = MeshcatVisualizer(port=7002)
    robot = six_dof_articulated()
    vis.set_robot(robot)
    
    # 验证 mesh 对象已创建
    assert "base" in dir(vis.vis)
    assert "link0" in dir(vis.vis)

def test_update_joints():
    """测试关节更新"""
    vis = MeshcatVisualizer(port=7003)
    robot = six_dof_articulated()
    vis.set_robot(robot)
    
    # 测试零位
    q_zero = np.zeros(6)
    vis.update_joints(q_zero)
    
    # 测试随机位姿
    q_random = np.random.rand(6) * 2 * np.pi - np.pi
    vis.update_joints(q_random)

def test_realtime_stream():
    """测试实时流式更新"""
    vis = MeshcatVisualizer(port=7004)
    robot = six_dof_articulated()
    vis.set_robot(robot)
    
    from robot_ik.hardware import SimulatedHardware
    hardware = SimulatedHardware(dof=6)
    
    # 启动流
    vis.start_realtime_stream(hardware, freq=30)
    assert vis._streaming
    
    # 运行一小段时间
    time.sleep(0.5)
    
    # 停止流
    vis.stop_realtime_stream()
    assert not vis._streaming

def test_concurrent_stream_error():
    """测试并发流式更新错误"""
    vis = MeshcatVisualizer(port=7005)
    robot = six_dof_articulated()
    vis.set_robot(robot)
    
    hardware = SimulatedHardware(dof=6)
    vis.start_realtime_stream(hardware, freq=30)
    
    # 尝试启动第二个流（应该失败）
    with pytest.raises(RuntimeError):
        vis.start_realtime_stream(hardware, freq=30)
```

### Integration Tests

```python
# test_integration_meshcat.py
def test_ik_visualization_workflow():
    """测试 IK + 可视化集成工作流"""
    from robot_ik import six_dof_articulated
    from robot_ik.visualize_meshcat import MeshcatVisualizer
    
    robot = six_dof_articulated()
    vis = MeshcatVisualizer(port=7006)
    vis.set_robot(robot)
    
    # IK 求解
    target_pose = create_target_pose([0.5, 0.3, 0.4])
    success, q, _, _ = robot.ik_solve(target_pose)
    
    assert success
    
    # 更新可视化
    vis.update_joints(q)
```

---

## Dependencies

### pyproject.toml

```toml
[project.optional-dependencies]
viz = ["matplotlib>=3.7.0"]
meshcat = ["meshcat>=0.3.0", "websocket-client"]
all = ["robot-ik[viz,meshcat]"]
```

### Installation

```bash
# 仅基础包
pip install robot-ik

# 添加 Meshcat 支持
pip install robot-ik[meshcat]

# 全功能
pip install robot-ik[all]
```

---

## Implementation Plan

### Task Breakdown

**Day 1: Core Implementation**
- [ ] 创建 `visualize_meshcat.py`
- [ ] 实现 `MeshcatVisualizer.__init__()`
- [ ] 实现 `_create_robot_mesh()` (程序化生成)
- [ ] 实现 `set_robot()` 和 `update_joints()`
- [ ] 单元测试: 初始化、模型生成、关节更新

**Day 2: Jupyter & Streaming**
- [ ] 实现 `start_jupyter()` (Jupyter 集成)
- [ ] 实现 `start_realtime_stream()` (Threading)
- [ ] 实现 `stop_realtime_stream()`
- [ ] 单元测试: 实时流式更新
- [ ] 集成测试: IK + 可视化工作流

**Day 3: Polish & Documentation**
- [ ] 错误处理和日志
- [ ] 配置管理
- [ ] 文档和使用示例
- [ ] Jupyter notebook 教程
- [ ] 性能测试（验证 30fps）

---

## Success Criteria

- ✅ Meshcat 可视化器可在 Jupyter 中显示
- ✅ 程序化生成的 6-DOF 机器人模型正确显示
- ✅ 关节更新平滑（无卡顿）
- ✅ 实时流式更新达到 30Hz
- ✅ 所有单元测试通过
- ✅ 集成测试验证 IK + 可视化工作流
- ✅ 文档完整（API 文档 + 使用示例）
- ✅ Jupyter notebook 教程可用

---

## Related Documents

- Design: `docs/plans/2026-05-14-scope-roadmap-review.md` (Phase B)
- HAL Design: `docs/plans/2026-05-14-scope-roadmap-review.md` (Hardware Abstraction Layer)
- Implementation Plan: `docs/plans/YYYY-MM-DD-phase-b-implementation.md` (待创建)

---

**批准**: 设计已确认，可以开始实施

**下一步**: 创建详细实施计划（使用 writing-plans skill）
