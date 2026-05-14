# Pendulum Test Bug Analysis

## Problem Summary

**Test**: `test_pendulum_gravity` at 30°
- **Expected**: 2.45 Nm (mgL sin θ)
- **Actual**: -7.36 Nm
- **Error**: **3x discrepancy** (400%)

## Root Cause

The bug is in how **DH parameters are interpreted** in the forward kinematics.

### Expected vs Actual COM Position

```
Expected COM (correct): [0.433, 0.25, 0] m
  - Distance from joint: 0.5 m
  - Perpendicular distance: 0.5 * sin(30°) = 0.25 m ✓

Actual COM (computed): [1.299, 0.75, 0] m
  - Distance from joint: 1.5 m (3x error!)
  - This is: 0.5 m (COM) + 1.0 m (link length) = 1.5 m
```

### The Bug: Double-Counting Link Length

In `robot_dyn.py`, the COM position is computed as:

```python
com_b = Ts[i+1][:3, :3] @ self.model.links[i].com + Ts[i+1][:3, 3]
```

Where:
- `Ts[i+1][:3, :3] @ com` rotates COM from link to base frame
- `Ts[i+1][:3, 3]` is the **link frame origin** in base coordinates

**Problem**: This adds the link origin position to COM, which is wrong!

For a 1-DOF pendulum with `a=1.0, d=0, α=0`:
- Link origin position: [a*cos(θ), a*sin(θ), 0] = [0.866, 0.5, 0]
- COM in link frame: [0.5, 0, 0] (0.5m along x-axis)
- Rotated COM: [0.433, 0.25, 0]
- **COMputed COM**: [0.433, 0.25, 0] + [0.866, 0.5, 0] = [1.299, 0.75, 0] ❌

The COM should be **0.5m from the joint**, but it's being placed **1.5m from the joint**!

### Why This Causes 3x Error

The moment arm for gravity torque is calculated from joint to COM:

```
τ = r_com × F_gravity

Expected r_com magnitude: 0.5 * sin(30°) = 0.25 m
Actual r_com magnitude: 1.5 * sin(30°) = 0.75 m (3x!)

Torque = m * g * moment_arm
Expected: 1.0 * 9.81 * 0.25 = 2.45 Nm
Actual:   1.0 * 9.81 * 0.75 = 7.36 Nm (3x error!)
```

## The Fix

### Option 1: Remove Link Origin from COM Calculation (Recommended)

```python
# OLD (WRONG):
com_b = Ts[i+1][:3, :3] @ self.model.links[i].com + Ts[i+1][:3, 3]

# NEW (CORRECT):
com_b = Ts[i+1][:3, :3] @ self.model.links[i].com
```

**Why**: COM should be in the link's coordinate frame, not offset by link origin.

### Option 2: Redefine COM to Include Link Origin

Keep the code but change COM definition:
```python
# COM is defined as offset from link origin
links=[LinkInertia(com=np.array([0.0, 0.0, 0.0]))]  # At joint
```

This is **not recommended** because it breaks the standard DH convention.

## DH Convention Reference

In standard DH parameters:
- **Link frame origin**: At the intersection of joint axis and common normal
- **COM**: Should be defined **relative to link frame origin**
- **COM position in base frame**: `R_link * com_link` (rotation only!)

The link origin position (`Ts[:3, 3]`) should **not** be added to COM.

## Impact Assessment

### Affected Functions
1. `inverse_dynamics()` - Line 115, 129
2. `inertia_matrix()` - Indirectly via FK

### Not Affected
- `forward_kinematics()` - Only computes frame transforms
- `coriolis_torque()` - Uses difference, cancels out COM error
- `gravity_torque()` - **Directly affected** (this is why test fails)

### Test Results

Currently passing tests:
- `test_pendulum_zero_velocity` - Passes because error affects both sides equally
- `test_coriolis_no_gravity` - Error cancels out in difference
- `test_6dof_roundtrip` - Errors cancel in summation

Failing test:
- `test_pendulum_gravity` - **Fails** (3x error)

## Validation Plan

1. **Fix COM calculation** in `robot_dyn.py`
2. **Run all tests** to verify no regressions
3. **Add new test** for pendulum at multiple angles
4. **Update C++ code** if it has same bug

## Files to Modify

1. `robot_ik/robot_dyn.py` - Fix lines 115 and 129
2. `test_dyn.py` - Uncomment assertion in `test_pendulum_gravity`
3. `robot_ik/robot_dyn_fast.cpp` - Check if same bug exists (if yes, fix)

## Estimated Time

- Fix Python code: 5 minutes
- Fix C++ code: 10 minutes (if needed)
- Testing: 5 minutes
- **Total**: 20 minutes

---

**Status**: Root cause identified, fix ready to implement
**Priority**: High (affects gravity compensation, critical for real robots)
**Risk**: Low (isolated bug, well-understood fix)
