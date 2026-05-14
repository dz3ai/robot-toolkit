# GitHub Actions Workflows Queued - Analysis

## Current Situation

**Workflow**: Phase 15b CI (Run #25865445497)
**Status**: Partially completed, 3 jobs queued for 34+ minutes

### Job Status

```
✓ test (ubuntu-22.04, 3.10) - Completed (46s)
✓ test (ubuntu-22.04, 3.11) - Completed (56s)
✓ test (ubuntu-22.04, 3.12) - Completed (58s)
✓ test (windows-2022, 3.11) - Completed (2m 24s)
✓ test (windows-2022, 3.12) - Completed (2m 13s)
✗ lint                      - Failed (black formatting)

* test (macos-13, 3.10)      - QUEUED (34+ minutes)
* test (macos-13, 3.11)      - QUEUED (34+ minutes)
* test (macos-13, 3.12)      - QUEUED (34+ minutes)
```

## Root Causes

### 1. **macOS Runner Availability** (Most Likely)

GitHub Actions has **limited macOS runner capacity**, especially for:
- **Free tier public repositories**
- **Peak usage times**
- **Multiple concurrent workflows**

**Current situation**:
- You have multiple workflows running simultaneously:
  - Build wheels (from earlier pushes)
  - CI (current run)
- Both need macOS runners
- GitHub's macOS runner pool is much smaller than Linux/Windows

**Evidence**:
```
Triggered via push about 34 minutes ago
macOS jobs still: QUEUED
Runner name: "" (no runner assigned yet)
```

### 2. **Concurrent Workflow Limitations**

GitHub has limits on concurrent jobs:
- **Free account**: 20 concurrent jobs (total)
- **macOS-specific**: ~2-4 concurrent jobs (shared pool)
- **Your usage**: 5 Linux + 2 Windows + 3 queued macOS = 10 jobs

### 3. **Previous Workflow Interference**

Multiple workflows were triggered in quick succession:
```
1. Build wheels (v0.3.0) - Cancelled after 14+ hours
2. Build wheels (main)   - Cancelled after 14+ hours
3. CI (main)             - Currently running
```

These previous runs may have:
- Exhausted macOS runner quota
- Created queue backup
- Left orphaned jobs

### 4. **No Concurrency Control**

CI workflow lacks concurrency limits:
```yaml
# Missing:
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

This means:
- Old workflows aren't cancelled when new ones are pushed
- Multiple workflows compete for runners
- Resources are wasted

## Solutions

### Immediate Fixes

#### 1. **Add Concurrency Control**

Update `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
  workflow_dispatch:

# ADD THIS:
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  test:
    # ... rest of workflow
```

**Effect**: Old CI runs are cancelled when new code is pushed.

#### 2. **Reduce macOS Matrix Size**

Temporarily reduce macOS jobs to 1 Python version:

```yaml
strategy:
  fail-fast: false
  matrix:
    os: [ubuntu-22.04, macos-13, windows-2022]
    python-version: ['3.10', '3.11', '3.12']
    exclude:
      - os: windows-2022
        python-version: '3.10'
      # ADD THIS: Only test 3.11 on macOS
      - os: macos-13
        python-version: '3.10'
      - os: macos-13
        python-version: '3.12'
```

**Effect**: 1 macOS job instead of 3 (3x faster queue).

#### 3. **Cancel Stuck Workflows**

```bash
# Cancel old workflows
gh run list --repo dz3ai/robot-toolkit --json databaseId,status \
  --jq '.[] | select(.status == "queued" or .status == "in_progress") | .databaseId' \
  | xargs -I {} gh run cancel {}

# Or manually cancel specific runs
gh run cancel 25833654497  # Old build wheels
gh run cancel 25833650110  # Old CI
```

### Long-term Solutions

#### 4. **Use GitHub Actions Concurrency Group**

Add to all workflows:
```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.head_ref || github.ref }}
  cancel-in-progress: true
```

#### 5. **Optimize CI Strategy**

Options:
- **Use ubuntu-only for quick checks** (macOS on release only)
- **Add separate workflow for release builds**
- **Use caching more aggressively**

#### 6. **Upgrade to GitHub Team/Enterprise**

If macOS runners are critical:
- **Team plan**: Higher concurrent job limits
- **Enterprise**: Dedicated runners (self-hosted macOS)

## Current Blockers

### Lint Failure

```
✗ lint in 13s
  ✗ Check formatting with black
```

**Fix**:
```bash
# Auto-format code
black robot_ik/ test_*.py

# Commit and push
git add -A
git commit -m "Fix formatting: apply black"
git push
```

### Why Black Failed

Recent changes probably didn't follow black formatting:
- `robot_dyn.py` - Modified lines
- `test_dyn.py` - Changed assertion
- New files may not be formatted

## Recommendations

### For Immediate Relief

1. **Cancel stuck workflows**
2. **Fix black formatting** (blocking current CI)
3. **Add concurrency control** (prevent future queue)
4. **Reduce macOS matrix** (temporary, until queue clears)

### For Future

1. **Separate workflows**:
   - `ci.yml` - Quick tests (ubuntu only)
   - `ci-full.yml` - Full matrix (on release)
   - `build-wheels.yml` - Release builds (manual trigger)

2. **Use smarter strategy**:
   - PRs: Ubuntu + 1 macOS + 1 Windows
   - Main: Full matrix
   - Tags: Full + build wheels

3. **Monitor queue times**:
   - If macOS > 30min consistently, reduce matrix
   - Consider self-hosted runners for macOS

## Action Items

**Now**:
- [ ] Cancel stuck workflows
- [ ] Fix black formatting
- [ ] Add concurrency control

**Soon**:
- [ ] Reduce macOS matrix (temporary)
- [ ] Split CI into quick/full workflows

**Later**:
- [ ] Consider GitHub Team plan (if macOS critical)
- [ ] Set up self-hosted runners (optional)

---

## Summary

**Why queued?**
- GitHub's macOS runner pool is small
- Multiple concurrent workflows competing
- No concurrency control to cancel old runs

**What to do?**
1. Fix black formatting (unblock current run)
2. Add concurrency control (prevent future issues)
3. Reduce macOS jobs (temporary workaround)
