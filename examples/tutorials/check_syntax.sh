#!/bin/bash
# Quick syntax check for all tutorial scripts

echo "Checking tutorial scripts..."
echo ""

for script in tutorial*.py; do
    echo -n "Checking $script... "
    python3 -m py_compile "$script" 2>&1
    if [ $? -eq 0 ]; then
        echo "✓ OK"
    else
        echo "✗ FAILED"
        exit 1
    fi
done

echo ""
echo "All tutorials syntax validated!"
echo ""
echo "To run tutorials individually:"
echo "  python tutorial01_workspace_analysis.py"
echo "  python tutorial02_collision_detection.py"
echo "  python tutorial03_coordinated_trajectory.py"
echo "  python tutorial04_path_planning.py"
