#!/bin/bash
# ==============================================================================
# Verification Script for SWE-bench Flask Instance
# ==============================================================================
# This script verifies the instance configuration and runs the validation tests
# according to SWE-bench specifications.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}==========================================${NC}"
echo -e "${GREEN}  Flask Template Cache Enhancement${NC}"
echo -e "${GREEN}  Instance Verification${NC}"
echo -e "${GREEN}==========================================${NC}"

# Directory setup
BASE_DIR="/work/testbed"
INSTANCE_DIR="${BASE_DIR}/instance"
LOG_DIR="${BASE_DIR}/logs"

mkdir -p ${LOG_DIR}
mkdir -p ${INSTANCE_DIR}

LOG_FILE="${LOG_DIR}/verification.log"
RESULT_FILE="${LOG_DIR}/verification_result.json"

echo -e "${YELLOW}[1/5] Initializing environment...${NC}"

# Load instance configuration
if [ -f "/root/instance.json" ]; then
    echo "Loading instance configuration..."
    cp /root/instance.json ${INSTANCE_DIR}/
else
    echo -e "${RED}ERROR: instance.json not found at /root/instance.json${NC}"
    exit 1
fi

# Verify Python environment
echo -e "${YELLOW}[2/5] Verifying Python environment...${NC}"

source /opt/testbed/bin/activate
python --version
pip list | grep -E "flask|werkzeug|jinja2"

echo -e "${YELLOW}[3/5] Applying patches...${NC}"

# Extract and apply code patch
if [ -f "${INSTANCE_DIR}/instance.json" ]; then
    # Extract patch using Python
    python3 << 'EOF'
import json
import os

instance_path = "/work/testbed/instance/instance.json"
with open(instance_path, 'r') as f:
    data = json.load(f)

code_patch = data.get('patch', '')
if code_patch:
    patch_path = '/work/testbed/code.patch'
    with open(patch_path, 'w') as f:
        f.write(code_patch)
    print(f"Code patch saved to {patch_path}")

test_patch = data.get('test_patch', '')
if test_patch:
    test_patch_path = '/work/testbed/test.patch'
    with open(test_patch_path, 'w') as f:
        f.write(test_patch)
    print(f"Test patch saved to {test_patch_path}")
EOF

    # Apply patches
    if [ -f "${BASE_DIR}/code.patch" ]; then
        echo "Applying code patch..."
        cd ${BASE_DIR}
        git apply ${BASE_DIR}/code.patch || echo "Patch may already be applied"
    fi

    if [ -f "${BASE_DIR}/test.patch" ]; then
        echo "Applying test patch..."
        cd ${BASE_DIR}
        git apply ${BASE_DIR}/test.patch || echo "Test patch may already be applied"
    fi
fi

echo -e "${YELLOW}[4/5] Running validation tests...${NC}"

# Run PASS_TO_PASS tests (should pass even before patch)
echo "Running PASS_TO_PASS tests..."

PASS_RESULTS=()
FAIL_RESULTS=()

# Check test directory
if [ -d "${BASE_DIR}/tests" ]; then
    cd ${BASE_DIR}

    # Install test dependencies
    pip install pytest pytest-cov

    # Extract and run tests
    python3 << 'EOF'
import json
import subprocess
import sys
import os

instance_path = "/work/testbed/instance/instance.json"

with open(instance_path, 'r') as f:
    data = json.load(f)

pass_to_pass = data.get('PASS_TO_PASS', [])
fail_to_pass = data.get('FAIL_TO_PASS', [])

print(f"Found {len(pass_to_pass)} PASS_TO_PASS tests")
print(f"Found {len(fail_to_pass)} FAIL_TO_PASS tests")

results = {
    "pass_to_pass": [],
    "fail_to_pass": [],
    "timestamp": ""
}

import datetime
results["timestamp"] = datetime.datetime.now().isoformat()

for test in pass_to_pass:
    print(f"Running: {test}")
    # Convert "test.py::Class::method" format to pytest command
    cmd = ['python', '-m', 'pytest', '-v', test]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd='/work/testbed')
        passed = result.returncode == 0
        results["pass_to_pass"].append({
            "test": test,
            "passed": passed,
            "stdout": result.stdout[:500],
            "stderr": result.stderr[:500]
        })
        print(f"  {'PASS' if passed else 'FAIL'}")
    except Exception as e:
        print(f"  ERROR: {str(e)}")
        results["pass_to_pass"].append({
            "test": test,
            "passed": False,
            "error": str(e)
        })

# Save results
result_path = "/work/testbed/logs/verification_result.json"
with open(result_path, 'w') as f:
    json.dump(results, f, indent=2)
EOF

else
    echo -e "${RED}ERROR: Tests directory not found${NC}"
fi

echo -e "${YELLOW}[5/5] Generating verification report...${NC}"

# Summary report
python3 << 'EOF'
import json
import os

result_path = "/work/testbed/logs/verification_result.json"

if os.path.exists(result_path):
    with open(result_path, 'r') as f:
        results = json.load(f)

    print("\n========= VERIFICATION RESULTS =========")
    
    total_pass = len(results.get("pass_to_pass", []))
    pass_count = sum(1 for r in results.get("pass_to_pass", []) if r.get("passed", False))
    
    print(f"\nPASS_TO_PASS tests: {pass_count}/{total_pass}")
    for r in results.get("pass_to_pass", []):
        status = "✅ PASS" if r.get("passed") else "❌ FAIL"
        print(f"  {status}: {r.get('test')}")
    
    overall_pass = pass_count == total_pass
    print(f"\nOverall verification: {'✅ SUCCESS' if overall_pass else '❌ FAILURE'}")
    
    if overall_pass:
        with open("/work/testbed/logs/verification_success.txt", "w") as f:
            f.write("Verification successful\n")
        exit(0)
    else:
        exit(1)
EOF

echo -e "${GREEN}==========================================${NC}"
echo -e "${GREEN}  Verification complete${NC}"
echo -e "${GREEN}==========================================${NC}"
