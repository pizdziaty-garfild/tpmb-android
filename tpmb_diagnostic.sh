#!/data/data/com.termux/files/usr/bin/bash

# TPMB Android Installation Diagnostic
# Diagnostyka problemów z instalacją

echo "🔍 TPMB Android - Diagnostyka Instalacji"
echo "========================================"

echo "📱 System Information:"
echo "  Android Version: $(getprop ro.build.version.release)"
echo "  Architecture: $(uname -m)"
echo "  Kernel: $(uname -r)"

echo ""
echo "📦 Termux Information:"
termux-info 2>/dev/null || echo "  Termux-info not available"

echo ""
echo "🐍 Python Information:"
echo "  Python Version: $(python --version 2>&1)"
echo "  Python Path: $(which python)"
echo "  Pip Version: $(pip --version 2>&1)"

echo ""
echo "🔧 Installed Packages:"
pkg list-installed | grep -E "(python|rust|clang|openssl|libffi)" 2>/dev/null || echo "  Package check failed"

echo ""  
echo "📚 Python Modules:"
python -c "
packages = ['telegram', 'cryptography', 'aiohttp', 'setuptools', 'wheel']
for pkg in packages:
    try:
        __import__(pkg)
        print(f'  ✅ {pkg}')
    except ImportError:
        print(f'  ❌ {pkg} - NOT INSTALLED')
"

echo ""
echo "💾 Storage Information:"  
df -h $HOME 2>/dev/null || echo "  Storage check failed"

echo ""
echo "🔗 Network Connectivity:"
curl -s --connect-timeout 5 https://pypi.org > /dev/null && echo "  ✅ PyPI reachable" || echo "  ❌ PyPI unreachable"
curl -s --connect-timeout 5 https://github.com > /dev/null && echo "  ✅ GitHub reachable" || echo "  ❌ GitHub unreachable"

echo ""
echo "📁 Directory Structure:"
if [ -d "tpmb-android" ]; then
    echo "  ✅ tpmb-android directory exists"
    ls -la tpmb-android/ 2>/dev/null | head -5
else
    echo "  ❌ tpmb-android directory missing"
fi

echo ""
echo "🔍 Common Issues Check:"
echo "  Termux from F-Droid: $([ -f '/data/data/com.termux/files/usr/etc/termux.conf' ] && echo '✅ Likely' || echo '❓ Unknown')"
echo "  Sufficient storage: $(df $HOME | awk 'NR==2{print ($4 > 500000) ? "✅ Yes" : "❌ Low space"}')"
