#!/bin/bash
# Create Week 2 directory structure for AgentiCraft

echo "🏗️  Creating Week 2 Directory Structure"
echo "======================================"

# Create experimental directories
echo -e "\n📁 Creating experimental/ structure..."
mkdir -p agenticraft/experimental/{protocols,fabric,marketplace,security,reasoning}
touch agenticraft/experimental/__init__.py
touch agenticraft/experimental/{protocols,fabric,marketplace,security,reasoning}/__init__.py

# Create consolidated utils
echo -e "\n📁 Creating consolidated utils/..."
mkdir -p agenticraft/utils
touch agenticraft/utils/__init__.py

# Create legacy compatibility layer
echo -e "\n📁 Creating legacy compatibility layer..."
mkdir -p agenticraft/legacy
touch agenticraft/legacy/__init__.py

# Create proper __init__.py files with module info
cat > agenticraft/experimental/__init__.py << 'EOF'
"""Experimental features for AgentiCraft.

Warning: APIs in this module are unstable and may change without notice.
For production use, stick to the main agenticraft imports.
"""

__all__ = ["protocols", "fabric", "marketplace", "security", "reasoning"]
EOF

cat > agenticraft/utils/__init__.py << 'EOF'
"""Internal utilities for AgentiCraft.

This module is for internal use only. 
Public APIs should be imported from the main agenticraft module.
"""

__all__ = ["config", "logging", "helpers"]
EOF

cat > agenticraft/legacy/__init__.py << 'EOF'
"""Legacy import compatibility layer.

This module provides backwards compatibility for old import paths.
All imports here will show deprecation warnings.
"""

import warnings

warnings.warn(
    "Importing from agenticraft.legacy is deprecated. "
    "Please update your imports to use the main agenticraft module.",
    DeprecationWarning,
    stacklevel=2
)
EOF

echo -e "\n✅ Directory structure created!"

# Show the new structure
echo -e "\n📊 New structure preview:"
tree agenticraft/experimental agenticraft/utils agenticraft/legacy -L 2 2>/dev/null || {
    echo "agenticraft/"
    echo "├── experimental/"
    echo "│   ├── __init__.py"
    echo "│   ├── fabric/"
    echo "│   ├── marketplace/"
    echo "│   ├── protocols/"
    echo "│   ├── reasoning/"
    echo "│   └── security/"
    echo "├── utils/"
    echo "│   └── __init__.py"
    echo "└── legacy/"
    echo "    └── __init__.py"
}

echo -e "\n🎯 Next steps:"
echo "1. Run ./analyze_modules_to_move.sh to see what needs moving"
echo "2. Run ./move_experimental_modules.sh to start the migration"
echo "3. Run tests after each move to ensure nothing breaks"