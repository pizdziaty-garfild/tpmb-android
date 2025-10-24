#!/data/data/com.termux/files/usr/bin/bash

# TPMB Android Installation Fix Script
# Rozwiązanie problemów z instalacją w Termux na Android
# Version 3.0 - Comprehensive Fix

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'  
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUKCES]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[OSTRZEŻENIE]${NC} $1"  
}

log_error() {
    echo -e "${RED}[BŁĄD]${NC} $1"
}

echo "🛠️  TPMB Android - Naprawa Instalacji"
echo "📱 Rozwiązywanie problemów z Termux"
echo "========================================\n"

# 1. SPRAWDŹ ŹRÓDŁO TERMUX
log_info "Sprawdzanie źródła instalacji Termux..."

if [ -f "/data/data/com.termux/files/usr/etc/termux-info" ]; then
    TERMUX_VERSION=$(termux-info | grep "TERMUX_VERSION" | cut -d'=' -f2)
    log_info "Wersja Termux: $TERMUX_VERSION"
    
    # Sprawdź czy to F-Droid/GitHub (nie Play Store)
    if [ "$TERMUX_VERSION" \< "0.118" ]; then
        log_error "Używasz przestarzałej wersji Termux z Play Store!"
        log_warning "Musisz zainstalować Termux z F-Droid lub GitHub"
        log_info "1. Odinstaluj obecny Termux"
        log_info "2. Pobierz z: https://f-droid.org/packages/com.termux/"
        log_info "3. Lub z GitHub: https://github.com/termux/termux-app/releases"
        exit 1
    fi
else
    log_warning "Nie można określić wersji Termux"
fi

# 2. WYCZYŚĆ STARE INSTALACJE
log_info "Czyszczenie poprzednich instalacji..."
pkg autoclean -y 2>/dev/null || true
pkg clean -y 2>/dev/null || true

# 3. NAPRAW REPOZYTORIA
log_info "Naprawianie repozytoriów Termux..."
pkg update -y

# 4. ZAINSTALUJ PODSTAWOWE NARZĘDZIA
log_info "Instalowanie podstawowych narzędzi..."
pkg install -y curl wget git

# 5. SPRAWDŹ I NAPRAW PYTHON
log_info "Sprawdzanie instalacji Python..."

# Usuń problematyczne pakiety jeśli istnieją
pkg uninstall -y python-cryptography 2>/dev/null || true
pip uninstall -y cryptography 2>/dev/null || true

# Zainstaluj Python i narzędzia deweloperskie
log_info "Instalowanie Python i narzędzi deweloperskich..."
pkg install -y python python-dev python-pip

# 6. ZAINSTALUJ KOMPILATORY I BIBLIOTEKI
log_info "Instalowanie kompilatorów i bibliotek systemowych..."
pkg install -y clang make cmake pkg-config
pkg install -y openssl openssl-dev libffi libffi-dev  
pkg install -y rust binutils libc++

# 7. NAPRAW PIP I SETUPTOOLS
log_info "Naprawianie pip i setuptools..."
python -m pip install --upgrade pip
python -m pip install --upgrade setuptools wheel

# 8. ZAINSTALUJ CRYPTOGRAPHY Z PREBUDOWANYM KOLEM
log_info "Instalowanie cryptography (może potrwać kilka minut)..."

# Spróbuj najpierw zainstalować z gotowym wheel
python -m pip install --only-binary=all cryptography 2>/dev/null || {
    log_warning "Prebudowane wheel niedostępne, kompilowanie ze źródła..."
    
    # Ustaw zmienne środowiskowe dla kompilacji
    export CARGO_BUILD_TARGET="$(rustc -Vv 2>/dev/null | grep 'host' | awk '{print $2}' || echo 'unknown')"
    export CRYPTOGRAPHY_DONT_BUILD_RUST=1 2>/dev/null || true
    
    # Zainstaluj dependencies dla Rust
    pkg install -y rust-std-wasm32-unknown-unknown 2>/dev/null || true
    
    # Kompiluj cryptography
    python -m pip install --no-binary cryptography cryptography || {
        log_error "Nie udało się zainstalować cryptography"
        log_info "Próbuję alternatywną metodę..."
        
        # Alternatywna metoda - użyj pakietu systemowego
        pkg install -y python-cryptography
        python -c "import cryptography; print('Cryptography zainstalowana systemowo')"
    }
}

# 9. SKLONUJ REPOZYTORIUM
log_info "Klonowanie repozytorium TPMB Android..."
cd ~

if [ -d "tpmb-android" ]; then
    log_warning "Katalog tpmb-android już istnieje, aktualizuję..."
    cd tpmb-android
    git pull origin main || {
        log_warning "Aktualizacja nie powiodła się, pobieranie na nowo..."
        cd ..
        rm -rf tpmb-android
        git clone https://github.com/pizdziaty-garfild/tpmb-android.git
        cd tpmb-android
    }
else
    git clone https://github.com/pizdziaty-garfild/tpmb-android.git
    cd tpmb-android
fi

# 10. MODYFIKUJ REQUIREMENTS.TXT DLA TERMUX
log_info "Optymalizowanie requirements.txt dla Termux..."

cat > requirements_termux.txt << 'EOF'
# Termux-optimized requirements for TPMB Android
python-telegram-bot>=20.0
aiohttp>=3.8.0
aiofiles>=22.1.0

# Use system cryptography if available
# cryptography>=41.0.0
certifi>=2023.7.22

# Time handling  
APScheduler>=3.10.0
pytz>=2023.3

# Monitoring (lightweight versions)
colorama>=0.4.6
psutil>=5.9.0

# Network
requests>=2.31.0
urllib3>=2.0.0

# Build tools
setuptools>=68.0.0
wheel>=0.41.0
EOF

# 11. ZAINSTALUJ ZALEŻNOŚCI PYTHON
log_info "Instalowanie zależności Python..."

# Najpierw spróbuj z systemowym cryptography
python -c "import cryptography" 2>/dev/null || {
    log_info "Instalowanie cryptography z requirements..."
    python -m pip install cryptography==41.0.7  # Sprawdzona wersja dla Termux
}

# Zainstaluj pozostałe pakiety
python -m pip install -r requirements_termux.txt

# 12. NAPRAW PROBLEMY Z IMPORTAMI
log_info "Sprawdzanie importów..."
python -c "
import sys
packages = ['telegram', 'aiohttp', 'cryptography', 'certifi', 'colorama']
for pkg in packages:
    try:
        __import__(pkg)
        print(f'✅ {pkg} - OK')
    except ImportError as e:
        print(f'❌ {pkg} - BŁĄD: {e}')
        if pkg == 'telegram':
            import subprocess
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'python-telegram-bot'])
" || {
    log_warning "Niektóre pakiety wymagają ponownej instalacji"
    python -m pip install --force-reinstall python-telegram-bot
}

# 13. STWÓRZ INSTANCJĘ
log_info "Tworzenie domyślnej instancji..."
python -c "
import sys, os
sys.path.append('.')

try:
    from utils.multi_instance_manager import MultiInstanceManager
    manager = MultiInstanceManager()
    
    instances = manager.list_instances()
    if not any(instance['name'] == 'default' for instance in instances):
        result = manager.create_instance('default', {
            'admin_ids': [],
            'interval_minutes': 5,
            'auto_start': False
        })
        print('✅ Domyślna instancja utworzona')
    else:
        print('ℹ️  Domyślna instancja już istnieje')
        
except Exception as e:
    print(f'⚠️  Problem z tworzeniem instancji: {e}')
    # Stwórz ręcznie strukturę katalogów
    os.makedirs('instances/default/config', exist_ok=True)
    os.makedirs('instances/default/logs', exist_ok=True)
    print('📁 Struktura katalogów utworzona ręcznie')
"

# 14. STWÓRZ POMOCNICZY SKRYPT KONFIGURACJI
log_info "Tworzenie skryptu konfiguracyjnego..."
cat > configure_bot.py << 'EOF'
#!/usr/bin/env python3
"""
Asystent konfiguracji TPMB Android Bot
Wersja zoptymalizowana dla Termux
"""

import os
from pathlib import Path

def main():
    print("🤖 Asystent Konfiguracji TPMB Android")
    print("📱 Wersja dla Termux")
    print("=" * 40)
    
    # Stwórz katalogi
    config_dir = Path("instances/default/config")
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # Token bota
    print("\n🔑 Krok 1: Token bota")
    print("💡 Pobierz token od @BotFather na Telegram")
    token = input("Wpisz token bota: ").strip()
    
    if not token or ':' not in token:
        print("❌ Nieprawidłowy format tokena")
        return
    
    with open(config_dir / "bot_token.txt", "w") as f:
        f.write(token)
    print("✅ Token zapisany")
    
    # ID administratora
    print("\n👤 Krok 2: ID Administratora") 
    print("💡 Pobierz swoje ID od @userinfobot")
    admin_id = input("Wpisz swoje Telegram ID: ").strip()
    
    if admin_id.isdigit():
        with open(config_dir / "settings.txt", "w") as f:
            f.write(f"interval_minutes=5\n")
            f.write(f"admin_ids={admin_id}\n")
            f.write(f"auto_start=false\n")
        print("✅ ID administratora skonfigurowane")
    
    # Domyślna wiadomość
    print("\n💬 Krok 3: Domyślna wiadomość")
    message = input("Wiadomość bota (Enter = domyślna): ").strip()
    if not message:
        message = "Witaj! Bot TPMB Android działa! 📱🤖"
    
    with open(config_dir / "messages.txt", "w") as f:
        f.write(message)
    
    # Puste grupy
    with open(config_dir / "groups.txt", "w") as f:
        f.write("")
    
    print("\n🎉 Konfiguracja zakończona!")
    print("\n📋 Następne kroki:")
    print("1. Uruchom bota: python main.py") 
    print("2. Dodaj grupy: /add_group [id_grupy]")
    print("3. Steruj przez Telegram: /help")

if __name__ == "__main__":
    main()
EOF

chmod +x configure_bot.py

# 15. TEST KOŃCOWY
log_info "Test końcowy instalacji..."
python -c "
print('🧪 Test komponentów:')
try:
    import telegram
    print('✅ Telegram Bot API')
except Exception as e:
    print(f'❌ Telegram: {e}')

try:
    import cryptography
    print('✅ Cryptography')  
except Exception as e:
    print(f'❌ Cryptography: {e}')

try:
    import aiohttp
    print('✅ Async HTTP')
except Exception as e:
    print(f'❌ AioHTTP: {e}')

try:
    from pathlib import Path
    Path('instances/default/config').mkdir(parents=True, exist_ok=True)
    print('✅ Struktura plików')
except Exception as e:
    print(f'❌ Pliki: {e}')
"

# 16. PODSUMOWANIE
log_success "Instalacja TPMB Android zakończona!"
echo ""
log_info "🚀 Jak uruchomić:"
log_info "1. python configure_bot.py  # Konfiguracja"
log_info "2. python main.py           # Uruchomienie"
echo ""
log_info "🔧 Rozwiązywanie problemów:"
log_info "- Sprawdź logi w instances/default/logs/"
log_info "- Upewnij się że Termux jest z F-Droid"
log_info "- Restartuj Termux jeśli występują błędy"
echo ""
log_warning "⚠️  Jeśli nadal masz problemy:"
log_warning "1. Zrestartuj Termux całkowicie"
log_warning "2. Uruchom ponownie ten skrypt"
log_warning "3. Sprawdź czy masz wystarczającą ilość pamięci"
