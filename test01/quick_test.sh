#!/bin/bash
# ==============================================================================
# Quick verification script for testing
# ==============================================================================

cd /work/testbed

# Verify Python
python --version

# Verify Flask installation
python -c "from flask import Flask; app = Flask(__name__); print('Flask OK')"

# Verify instance configuration
ls -la /work/testbed/instance/

# Create a simple test script
cat > test_simple.py << 'EOF'
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello Flask!'

if __name__ == '__main__':
    print('Flask test app created successfully')
EOF

python test_simple.py

echo "Quick verification completed!"
