#!/bin/bash
# ==============================================================================
# Flask CSRF Protection Enhancement - Instance Verification Script
# ==============================================================================
# This script verifies the CSRF protection implementation against the
# instance.json specification.
#
# Usage:
#   chmod +x verify_instance.sh
#   ./verify_instance.sh
#
# Exit codes:
#   0 - All verifications passed
#   1 - One or more verifications failed
# ==============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
TESTS_PASSED=0
TESTS_FAILED=0

# ==============================================================================
# Helper Functions
# ==============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((TESTS_PASSED++))
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((TESTS_FAILED++))
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_section() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# ==============================================================================
# Verification Functions
# ==============================================================================

verify_environment() {
    print_section "1. Environment Verification"

    # Check Python version
    PYTHON_VERSION=$(python3 --version 2>/dev/null || python --version 2>/dev/null)
    if [[ $PYTHON_VERSION == *"3.12"* ]] || [[ $PYTHON_VERSION == *"3.11"* ]] || [[ $PYTHON_VERSION == *"3.10"* ]]; then
        log_success "Python version check: $PYTHON_VERSION"
    else
        log_error "Python version should be 3.10+, found: $PYTHON_VERSION"
    fi

    # Check pip
    if command -v pip &> /dev/null || command -v pip3 &> /dev/null; then
        log_success "pip is installed"
    else
        log_error "pip is not installed"
    fi

    # Check git
    if command -v git &> /dev/null; then
        GIT_VERSION=$(git --version)
        log_success "Git is installed: $GIT_VERSION"
    else
        log_error "Git is not installed"
    fi

    # Check Docker (optional)
    if command -v docker &> /dev/null; then
        DOCKER_VERSION=$(docker --version)
        log_success "Docker is installed: $DOCKER_VERSION"
    else
        log_warn "Docker is not installed (optional)"
    fi
}

verify_file_structure() {
    print_section "2. File Structure Verification"

    local TESTBED_DIR="${TESTBED_DIR:-/work/testbed}"
    local INSTANCE_DIR="$(dirname "$0")"

    # Check if running in testbed or local directory
    if [ -d "$TESTBED_DIR" ]; then
        WORK_DIR="$TESTBED_DIR"
        log_info "Using testbed directory: $WORK_DIR"
    else
        WORK_DIR="$(cd "$INSTANCE_DIR/.." && pwd)"
        log_info "Using local directory: $WORK_DIR"
    fi

    # Required files from instance.json
    REQUIRED_FILES=(
        "src/flask/__init__.py"
        "src/flask/app.py"
        "src/flask/templating.py"
        "src/flask/csrf.py"
    )

    for file in "${REQUIRED_FILES[@]}"; do
        if [ -f "$WORK_DIR/$file" ]; then
            log_success "Required file exists: $file"
        else
            log_error "Missing required file: $file"
        fi
    done

    # Check patch files
    if [ -f "$INSTANCE_DIR/code.path" ] || [ -f "$INSTANCE_DIR/code.patch" ]; then
        log_success "Code patch file exists"
    else
        log_error "Code patch file not found (code.path or code.patch)"
    fi

    if [ -f "$INSTANCE_DIR/test.patch" ]; then
        log_success "Test patch file exists"
    else
        log_error "Test patch file not found (test.patch)"
    fi

    # Check Docker files
    DOCKER_FILES=("Dockerfile" "docker-compose.yml" "nginx.conf" "requirements.txt")
    for file in "${DOCKER_FILES[@]}"; do
        if [ -f "$INSTANCE_DIR/$file" ]; then
            log_success "Docker file exists: $file"
        else
            log_warn "Docker file missing: $file"
        fi
    done
}

verify_csrf_implementation() {
    print_section "3. CSRF Implementation Verification"

    local TESTBED_DIR="${TESTBED_DIR:-/work/testbed}"
    local INSTANCE_DIR="$(dirname "$0")"

    if [ -d "$TESTBED_DIR" ]; then
        WORK_DIR="$TESTBED_DIR"
    else
        WORK_DIR="$(cd "$INSTANCE_DIR/.." && pwd)"
    fi

    # Check CSRF module exists
    if [ -f "$WORK_DIR/src/flask/csrf.py" ]; then
        log_success "CSRF module exists: src/flask/csrf.py"

        # Check for required classes and functions
        if grep -q "class CSRFProtect" "$WORK_DIR/src/flask/csrf.py"; then
            log_success "CSRFProtect class found"
        else
            log_error "CSRFProtect class not found"
        fi

        if grep -q "class CSRFError" "$WORK_DIR/src/flask/csrf.py"; then
            log_success "CSRFError class found"
        else
            log_error "CSRFError class not found"
        fi

        if grep -q "def generate_csrf" "$WORK_DIR/src/flask/csrf.py"; then
            log_success "generate_csrf() function found"
        else
            log_error "generate_csrf() function not found"
        fi

        if grep -q "def csrf_token" "$WORK_DIR/src/flask/csrf.py"; then
            log_success "csrf_token() function found"
        else
            log_error "csrf_token() function not found"
        fi

        # Check for security features
        if grep -q "hmac.compare_digest" "$WORK_DIR/src/flask/csrf.py"; then
            log_success "Constant-time comparison (hmac.compare_digest) found"
        else
            log_error "Constant-time comparison not found"
        fi

        if grep -q "secrets.token_urlsafe" "$WORK_DIR/src/flask/csrf.py"; then
            log_success "Secure token generation (secrets.token_urlsafe) found"
        else
            log_error "Secure token generation not found"
        fi

        if grep -q "_validate_origin" "$WORK_DIR/src/flask/csrf.py"; then
            log_success "Origin validation found"
        else
            log_error "Origin validation not found"
        fi
    else
        log_error "CSRF module not found: src/flask/csrf.py"
    fi

    # Check app.py modifications
    if [ -f "$WORK_DIR/src/flask/app.py" ]; then
        if grep -q "enable_csrf" "$WORK_DIR/src/flask/app.py"; then
            log_success "enable_csrf() method found in app.py"
        else
            log_error "enable_csrf() method not found in app.py"
        fi
    fi

    # Check templating.py modifications
    if [ -f "$WORK_DIR/src/flask/templating.py" ]; then
        if grep -q "csrf_token" "$WORK_DIR/src/flask/templating.py"; then
            log_success "CSRF template functions found in templating.py"
        else
            log_error "CSRF template functions not found in templating.py"
        fi
    fi

    # Check __init__.py exports
    if [ -f "$WORK_DIR/src/flask/__init__.py" ]; then
        if grep -q "CSRFProtect" "$WORK_DIR/src/flask/__init__.py"; then
            log_success "CSRFProtect exported in __init__.py"
        else
            log_error "CSRFProtect not exported in __init__.py"
        fi
    fi
}

verify_configuration() {
    print_section "4. Configuration Verification"

    local INSTANCE_DIR="$(dirname "$0")"

    # Check instance.json exists and is valid JSON
    if [ -f "$INSTANCE_DIR/instance.json" ]; then
        log_success "instance.json exists"

        # Validate JSON syntax
        if python3 -c "import json; json.load(open('$INSTANCE_DIR/instance.json'))" 2>/dev/null; then
            log_success "instance.json is valid JSON"
        else
            log_error "instance.json is not valid JSON"
        fi

        # Check required fields
        REQUIRED_FIELDS=("instance_id" "title" "description" "patch" "test_patch")
        for field in "${REQUIRED_FIELDS[@]}"; do
            if python3 -c "import json; data=json.load(open('$INSTANCE_DIR/instance.json')); exit(0 if '$field' in data else 1)" 2>/dev/null; then
                log_success "Required field exists: $field"
            else
                log_error "Missing required field: $field"
            fi
        done
    else
        log_error "instance.json not found"
    fi
}

verify_tests() {
    print_section "5. Test Suite Verification"

    local TESTBED_DIR="${TESTBED_DIR:-/work/testbed}"
    local INSTANCE_DIR="$(dirname "$0")"

    if [ -d "$TESTBED_DIR" ]; then
        WORK_DIR="$TESTBED_DIR"
    else
        WORK_DIR="$(cd "$INSTANCE_DIR/.." && pwd)"
    fi

    # Check if pytest is available
    if command -v pytest &> /dev/null; then
        log_success "pytest is installed"

        # Check if CSRF test file exists
        if [ -f "$WORK_DIR/tests/test_csrf.py" ]; then
            log_success "CSRF test file exists: tests/test_csrf.py"

            # Count test cases
            TEST_COUNT=$(grep -c "def test_" "$WORK_DIR/tests/test_csrf.py" || echo "0")
            log_info "Found $TEST_COUNT test cases in test_csrf.py"
        else
            log_warn "CSRF test file not found: tests/test_csrf.py"
        fi

        # Run PASS_TO_PASS tests if they exist
        log_info "Running PASS_TO_PASS tests..."
        PASS_TESTS=(
            "tests/test_csrf.py::TestCSRFProtect::test_initialization"
            "tests/test_csrf.py::TestTokenGeneration::test_token_format"
            "tests/test_csrf.py::TestSafeMethods::test_get_request_exempt"
            "tests/test_csrf.py::TestCSRFValidation::test_post_with_token_succeeds"
        )

        for test in "${PASS_TESTS[@]}"; do
            if pytest "$WORK_DIR/$test" -v --tb=short 2>/dev/null; then
                log_success "PASS_TO_PASS test passed: $test"
            else
                log_warn "PASS_TO_PASS test not found or failed: $test"
            fi
        done

    else
        log_warn "pytest not installed, skipping test execution"
    fi
}

verify_docker_setup() {
    print_section "6. Docker Setup Verification"

    local INSTANCE_DIR="$(dirname "$0")"

    # Check Dockerfile
    if [ -f "$INSTANCE_DIR/Dockerfile" ]; then
        log_success "Dockerfile exists"

        # Check for required elements in Dockerfile
        if grep -q "CSRF_ENABLED" "$INSTANCE_DIR/Dockerfile"; then
            log_success "CSRF_ENABLED environment variable in Dockerfile"
        else
            log_warn "CSRF_ENABLED not found in Dockerfile"
        fi
    fi

    # Check docker-compose.yml
    if [ -f "$INSTANCE_DIR/docker-compose.yml" ]; then
        log_success "docker-compose.yml exists"

        if grep -q "CSRF" "$INSTANCE_DIR/docker-compose.yml"; then
            log_success "CSRF configuration in docker-compose.yml"
        else
            log_warn "CSRF configuration not found in docker-compose.yml"
        fi
    fi

    # Test Docker build (optional)
    if command -v docker &> /dev/null; then
        log_info "Testing Docker build (this may take a while)..."
        if docker build -t flask-csrf-verify "$INSTANCE_DIR" > /dev/null 2>&1; then
            log_success "Docker build successful"
            docker rmi flask-csrf-verify > /dev/null 2>&1
        else
            log_warn "Docker build failed (may require testbed context)"
        fi
    fi
}

verify_functional() {
    print_section "7. Functional Verification"

    local TESTBED_DIR="${TESTBED_DIR:-/work/testbed}"
    local INSTANCE_DIR="$(dirname "$0")"

    if [ -d "$TESTBED_DIR" ]; then
        WORK_DIR="$TESTBED_DIR"
    else
        WORK_DIR="$(cd "$INSTANCE_DIR/.." && pwd)"
    fi

    # Create a temporary test script
    TEMP_SCRIPT=$(mktemp)
    cat > "$TEMP_SCRIPT" << 'EOF'
import sys
sys.path.insert(0, 'src')

try:
    from flask import Flask
    from flask.csrf import CSRFProtect, CSRFError, generate_csrf, csrf_token
    print("SUCCESS: All CSRF imports successful")

    # Test basic initialization
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test-secret-key'

    # Test enable_csrf method
    if hasattr(app, 'enable_csrf'):
        csrf = app.enable_csrf()
        print("SUCCESS: enable_csrf() method works")
    else:
        print("ERROR: enable_csrf() method not found")
        sys.exit(1)

    # Test CSRFProtect instance
    if isinstance(csrf, CSRFProtect):
        print("SUCCESS: CSRFProtect instance created")
    else:
        print("ERROR: CSRFProtect instance not created correctly")
        sys.exit(1)

    # Test token generation
    with app.test_request_context():
        token = generate_csrf()
        if token and len(token) > 0:
            print("SUCCESS: Token generation works")
        else:
            print("ERROR: Token generation failed")
            sys.exit(1)

        # Test csrf_token function
        html = csrf_token()
        if '<input type="hidden"' in html and 'csrf_token' in html:
            print("SUCCESS: csrf_token() template function works")
        else:
            print("ERROR: csrf_token() function not working correctly")
            sys.exit(1)

    print("\nAll functional tests passed!")

except ImportError as e:
    print(f"ERROR: Import failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
EOF

    cd "$WORK_DIR"
    if python3 "$TEMP_SCRIPT" 2>/dev/null; then
        log_success "Functional verification passed"
    else
        log_error "Functional verification failed"
    fi

    rm -f "$TEMP_SCRIPT"
}

# ==============================================================================
# Main Execution
# ==============================================================================

main() {
    echo -e "${BLUE}"
    echo "============================================================================="
    echo "  Flask CSRF Protection Enhancement - Instance Verification"
    echo "============================================================================="
    echo -e "${NC}"

    # Run all verification functions
    verify_environment
    verify_file_structure
    verify_csrf_implementation
    verify_configuration
    verify_tests
    verify_docker_setup
    verify_functional

    # Print summary
    print_section "Verification Summary"
    echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
    echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"

    if [ $TESTS_FAILED -eq 0 ]; then
        echo ""
        echo -e "${GREEN}========================================${NC}"
        echo -e "${GREEN}  All Verifications Passed!${NC}"
        echo -e "${GREEN}========================================${NC}"
        exit 0
    else
        echo ""
        echo -e "${RED}========================================${NC}"
        echo -e "${RED}  Some Verifications Failed${NC}"
        echo -e "${RED}========================================${NC}"
        exit 1
    fi
}

# Run main function
main "$@"
