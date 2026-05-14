# robot-toolkit Tutorial Examples

Practical tutorials based on real dual-arm robotics challenges from `docs/challenges.md`.

## Overview

These tutorials demonstrate core robotics concepts using robot-toolkit:
- **Tutorial 1**: Dual-arm workspace analysis
- **Tutorial 2**: Self-collision detection
- **Tutorial 3**: Coordinated trajectory planning
- **Tutorial 4**: Collision-free path planning (RRT*)

Each tutorial is fully executable and generates visualizations.

## Prerequisites

```bash
# Install robot-toolkit (from source)
cd /path/to/robot-toolkit
pip install -e .

# Or install from PyPI (after v0.3.0 release)
pip install robot-ik
```

## Running Tutorials

### Individual Tutorials

```bash
# Tutorial 1: Workspace Analysis
python examples/tutorials/tutorial01_workspace_analysis.py

# Tutorial 2: Collision Detection
python examples/tutorials/tutorial02_collision_detection.py

# Tutorial 3: Coordinated Trajectories
python examples/tutorials/tutorial03_coordinated_trajectory.py

# Tutorial 4: Path Planning (RRT*)
python examples/tutorials/tutorial04_path_planning.py
```

### All Tutorials

```bash
# Run all tutorials sequentially
cd examples/tutorials
for t in tutorial*.py; do
    echo "Running $t..."
    python "$t"
done
```

## Tutorial Details

### Tutorial 1: Dual-Arm Workspace Analysis
**Challenge**: "Limited usable shared workspace" (challenges.md §1)

**Learning outcomes**:
- Forward kinematics for workspace sampling
- 3D workspace visualization
- Overlap volume calculation
- Configuration impact analysis

**Output**: `tutorial01_workspace.png`

**Key features**:
- Random joint space sampling
- Voxel-based overlap computation
- Multiple offset comparison (1.0m - 2.5m)

---

### Tutorial 2: Self-Collision Detection
**Challenge**: "Self-collision risk" (challenges.md §2)

**Learning outcomes**:
- Collision primitive modeling (capsules)
- Self-collision detection algorithms
- Contact point visualization
- Trajectory safety validation

**Output**: 
- `tutorial02_collision_safe.png`
- `tutorial02_collision_collision.png`

**Key features**:
- Capsule-based link modeling
- Real-time collision checking
- Trajectory collision analysis

---

### Tutorial 3: Coordinated Trajectory Planning
**Challenge**: "Synchronized trajectory planning" (challenges.md §3)

**Learning outcomes**:
- Multi-waypoint trajectory generation
- S-curve velocity profiling
- Dual-arm temporal coordination
- Gripper constraint validation

**Output**: `tutorial03_trajectory.png`

**Key features**:
- Pick-and-place scenario
- Time-synchronized motion
- Velocity/acceleration analysis
- Gripper distance tracking

---

### Tutorial 4: Collision-Free Path Planning (RRT*)
**Challenge**: "Complex real-time collision detection" (challenges.md §2)

**Learning outcomes**:
- Sampling-based path planning
- Collision constraint integration
- Sequential multi-robot planning
- Path optimization techniques

**Output**: `tutorial04_rrt_star.png`

**Key features**:
- RRT* algorithm implementation
- Obstacle environment modeling
- Sequential dual-arm planning
- Configuration space visualization

## Expected Output

Each tutorial generates:
1. **Console output**: Step-by-step progress and metrics
2. **Visualization**: PNG files with 3D plots and analysis
3. **Assessment**: Safety and quality recommendations

## Teaching Structure

Each tutorial follows a consistent format:

```python
# 1. Setup
#    - Initialize robot models
#    - Configure parameters

# 2. Execution
#    - Run core algorithms
#    - Compute metrics

# 3. Visualization
#    - Generate plots
#    - Save results

# 4. Analysis
#    - Quality assessment
#    - Recommendations
```

## Troubleshooting

### Import Errors
```bash
# Ensure robot-toolkit is installed
pip install -e /path/to/robot-toolkit

# Check PYTHONPATH
echo $PYTHONPATH
```

### Visualization Issues
```bash
# Install matplotlib backend (if needed)
pip install matplotlib PyQt5

# For headless environments
export MPLBACKEND=Agg
```

### Performance
- **Large workspace sampling**: Reduce `n_samples` parameter
- **RRT* planning**: Reduce `max_iter` for faster results
- **Visualization**: Use non-interactive backend

## Extension Ideas

After mastering these tutorials, explore:

1. **Master-slave control** (Phase 16)
   - Implement coordinated grasping
   - Add force feedback

2. **Closed-chain constraints**
   - Dual-arm object manipulation
   - Hybrid position-force control

3. **Advanced planning**
   - CHOMP trajectory optimization
   - Multi-robot parallel planning

## Contributing

To add new tutorials:

1. Create `tutorial05_*.py` in this directory
2. Follow the established structure
3. Add documentation to this README
4. Test on multiple Python versions (3.10-3.12)

## References

- `docs/challenges.md` - Source challenges
- `docs/tutorial-examples.md` - Full tutorial plan
- `ROADMAP.md` - Project roadmap and phases

## License

MIT License - See LICENSE file
