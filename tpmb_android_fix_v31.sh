#!/data/data/com.termux/files/usr/bin/bash

# TPMB Android Installation Fix Script v3.1
# Rozwiązanie problemów z instalacją w Termux na Android
# Specjalna wersja dla problemu z python-dev

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

echo "🛠️  TPMB Android - Naprawa Instalacji v3.1"
echo "📱 Rozwiązywanie problemów z Termux"
echo "🔧 Specjalna wersja dla błędów python-dev"
echo "==========================================\n"

# 1. SPRAWDŹ ŹRÓDŁO TERMUX
log_info "Sprawdzanie źródła instalacji Termux..."

if [ -f "/data/data/com.termux/files/usr/etc/termux-info" ]; then
    TERMUX_VERSION=$(termux-info | grep "TERMUX_VERSION" | cut -d'=' -f2)
    log_info "Wersja Termux: $TERMUX_VERSION"
    
    # Sprawdź czy to F-Droid/GitHub (nie Play Store)  
    if [ "$TERMUX_VERSION" \< "0.118" ]; then
        log_error "KRYTYCZNY PROBLEM: Używasz przestarzałej wersji Termux z Play Store!"
        log_error "Ta wersja nie ma dostępu do najnowszych pakietów!"
        log_warning "MUSISZ zainstalować Termux z F-Droid lub GitHub"
        log_info "1. Odinstaluj obecny Termux"
        log_info "2. Pobierz z: https://f-droid.org/packages/com.termux/"
        log_info "3. Lub z GitHub: https://github.com/termux/termux-app/releases"
        exit 1
    fi
else
    log_warning "Nie można określić wersji Termux - kontynuuję ostrożnie"
fi

# 2. WYCZYŚĆ I NAPRAW REPOZYTORIA
log_info "Intensywne czyszczenie repozytoriów..."
pkg autoclean -y 2>/dev/null || true
pkg clean -y 2>/dev/null || true

# Napraw repozytoria - bardzo ważne!
log_info "Naprawianie i aktualizacja repozytoriów Termux..."
echo "deb https://packages.termux.dev/apt/termux-main stable main" > "$PREFIX/etc/apt/sources.list"
pkg update -y

# 3. SPRAWDŹ DOSTĘPNOŚĆ PAKIETÓW
log_info "Sprawdzanie dostępności pakietów Python..."

# Sprawdź co jest dostępne w repo
PYTHON_AVAILABLE=$(pkg search python 2>/dev/null | grep "^python/" | head -1)
if [ -z "$PYTHON_AVAILABLE" ]; then
    log_error "Brak dostępu do pakietów Python w repozytoriach!"
    log_warning "Próbuję alternatywną metodę..."
    
    # Próba zmiany mirror
    pkg install -y termux-tools 2>/dev/null || true
    termux-change-repo
    pkg update -y
fi

# 4. ZAINSTALUJ PODSTAWOWE NARZĘDZIA
log_info "Instalowanie podstawowych narzędzi..."
pkg install -y curl wget git || {
    log_error "Nie można zainstalować podstawowych narzędzi"
    log_info "Sprawdź połączenie internetowe i spróbuj ponownie"
    exit 1
}

# 5. PYTHON I NARZĘDZIA DEWELOPERSKIE - INTELIGENTNA INSTALACJA
log_info "Inteligentna instalacja Python i narzędzi deweloperskich..."

# Usuń stare problematyczne pakiety
log_info "Usuwanie konfliktowych pakietów..."
pkg uninstall -y python-cryptography 2>/dev/null || true
pip uninstall -y cryptography 2>/dev/null || true

# Sprawdź czy python-dev jest dostępny, jeśli nie - użyj alternatywy
log_info "Sprawdzanie dostępności python-dev..."
if pkg search python-dev 2>/dev/null | grep -q "python-dev"; then
    log_info "python-dev dostępny - instaluję standardowo"
    pkg install -y python python-dev python-pip
else
    log_warning "python-dev niedostępny - używam alternatywnej metody"
    pkg install -y python python-pip
    
    # Zainstaluj headers manual - często wystarczy samyn python
    log_info "Python zainstalowany bez dev headers - to może wystarczyć"
fi

# 6. KOMPILATORY I BIBLIOTEKI - SELEKTYWNA INSTALACJA
log_info "Instalowanie kompilatorów (może potrwać kilka minut)..."

# Lista pakietów do zainstalowania z error handling
PACKAGES=(
    "clang"
    "make" 
    "cmake"
    "pkg-config"
    "openssl"
    "openssl-dev"
    "libffi"
    "libffi-dev"
    "rust"
    "binutils"
    "libc++"
)

for pkg_name in "${PACKAGES[@]}"; do
    if pkg install -y "$pkg_name" 2>/dev/null; then
        log_info "✅ Zainstalowano: $pkg_name"
    else
        log_warning "⚠️  Nie udało się zainstalować: $pkg_name (może nie być dostępny)"
    fi
done

# 7. NAPRAW PIP I SETUPTOOLS
log_info "Naprawianie pip i setuptools..."
python -m pip install --upgrade pip || {
    log_warning "Nie można zaktualizować pip - używam istniejącej wersji"
}

python -m pip install --upgrade setuptools wheel || {
    log_warning "Nie można zaktualizować setuptools/wheel - kontynuuję"
}

# 8. CRYPTOGRAPHY - WIELOETAPOWA INSTALACJA
log_info "Instalowanie cryptography - próba kilku metod..."

# Metoda 1: Prebudowany wheel
log_info "Próba 1: Prebudowany wheel..."
if python -m pip install --only-binary=all cryptography 2>/dev/null; then
    log_success "Cryptography zainstalowana z prebudowanego wheel"
    CRYPTO_INSTALLED=true
else
    log_warning "Prebudowany wheel niedostępny"
    CRYPTO_INSTALLED=false
fi

# Metoda 2: Kompilacja ze źródła (jeśli metoda 1 nie powiodła się)
if [ "$CRYPTO_INSTALLED" = false ]; then
    log_info "Próba 2: Kompilacja ze źródła..."
    
    # Ustaw zmienne środowiskowe
    export CARGO_BUILD_TARGET="$(rustc -Vv 2>/dev/null | grep 'host' | awk '{print $2}' || echo 'aarch64-linux-android')"
    export CRYPTOGRAPHY_DONT_BUILD_RUST=1 2>/dev/null || true
    
    if python -m pip install --no-binary cryptography cryptography 2>/dev/null; then
        log_success "Cryptography skompilowana ze źródła"
        CRYPTO_INSTALLED=true
    else
        log_warning "Kompilacja ze źródła nie powiodła się"
    fi
fi

# Metoda 3: Pakiet systemowy (jeśli metody 1 i 2 nie powiodły się)
if [ "$CRYPTO_INSTALLED" = false ]; then
    log_info "Próba 3: Pakiet systemowy..."
    if pkg install -y python-cryptography 2>/dev/null; then
        log_success "Zainstalowano systemowy pakiet cryptography"
        CRYPTO_INSTALLED=true
    fi
fi

# Metoda 4: Starsza wersja (ostatnia deska ratunku)
if [ "$CRYPTO_INSTALLED" = false ]; then
    log_info "Próba 4: Starsza kompatybilna wersja..."
    python -m pip install cryptography==3.4.8 || {
        log_error "Wszystkie metody instalacji cryptography nie powiodły się!"
        log_info "Bot może działać bez cryptography, ale z ograniczoną funkcjonalnością"
    }
fi

# 9. SKLONUJ REPOZYTORIUM
log_info "Klonowanie/aktualizacja repozytorium TPMB Android..."
cd ~

if [ -d "tpmb-android" ]; then
    log_warning "Katalog tpmb-android już istnieje - aktualizuję..."
    cd tpmb-android
    git pull origin main 2>/dev/null || {
        log_warning "Aktualizacja nie powiodła się - pobieranie na nowo..."
        cd ..
        rm -rf tpmb-android
        git clone https://github.com/pizdziaty-garfild/tpmb-android.git
        cd tpmb-android
    }
else
    git clone https://github.com/pizdziaty-garfild/tpmb-android.git || {
        log_error "Nie można sklonować repozytorium"
        log_info "Sprawdź połączenie internetowe"
        exit 1
    }
    cd tpmb-android
fi

# 10. STWÓRZ MINIMALNE REQUIREMENTS DLA TERMUX
log_info "Tworzenie minimalnych requirements dla Termux..."

cat > requirements_termux_minimal.txt << 'EOF'
# Minimalne requirements dla Termux - tylko niezbędne pakiety
python-telegram-bot>=20.0,<21.0
aiohttp>=3.8.0,<3.10.0
aiofiles>=22.1.0

# Podstawowe bezpieczeństwo
certifi>=2023.7.22
requests>=2.31.0

# Scheduling
APScheduler>=3.10.0
pytz>=2023.3

# Monitoring - tylko podstawowe
colorama>=0.4.6

# Build tools
setuptools>=68.0.0
wheel>=0.41.0

# cryptography jest opcjonalna - jeśli jest problematyczna, bot i tak będzie działać
EOF

# 11. ZAINSTALUJ ZALEŻNOŚCI PYTHON
log_info "Instalowanie minimalnych zależności Python..."

# Instaluj pakiet po pakiecie z error handling
python -m pip install "python-telegram-bot>=20.0,<21.0" || log_warning "Problem z python-telegram-bot"
python -m pip install "aiohttp>=3.8.0,<3.10.0" || log_warning "Problem z aiohttp" 
python -m pip install aiofiles || log_warning "Problem z aiofiles"
python -m pip install certifi || log_warning "Problem z certifi"
python -m pip install requests || log_warning "Problem z requests"
python -m pip install APScheduler || log_warning "Problem z APScheduler"
python -m pip install pytz || log_warning "Problem z pytz"
python -m pip install colorama || log_warning "Problem z colorama"

# 12. TEST IMPORTÓW
log_info "Sprawdzanie kluczowych importów..."
python -c "
import sys
critical_packages = ['telegram', 'aiohttp', 'asyncio']
optional_packages = ['cryptography', 'certifi', 'colorama']
errors = []

print('🔍 Sprawdzanie kluczowych pakietów:')
for pkg in critical_packages:
    try:
        __import__(pkg)
        print(f'✅ {pkg} - OK')
    except ImportError as e:
        print(f'❌ {pkg} - BŁĄD: {e}')
        errors.append(pkg)

print('\n🔍 Sprawdzanie opcjonalnych pakietów:')
for pkg in optional_packages:
    try:
        __import__(pkg)
        print(f'✅ {pkg} - OK')
    except ImportError as e:
        print(f'⚠️  {pkg} - Brak (opcjonalny): {e}')

if errors:
    print(f'\n❌ Krytyczne błędy: {errors}')
    print('Instaluję brakujące pakiety...')
    for pkg in errors:
        if pkg == 'telegram':
            import subprocess
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'python-telegram-bot'])
else:
    print('\n✅ Wszystkie kluczowe pakiety działają!')
"

# 13. STWÓRZ STRUKTURĘ KATALOGÓW
log_info "Tworzenie struktury katalogów..."
mkdir -p instances/default/config instances/default/logs
chmod 755 instances/ instances/default/ instances/default/config/ instances/default/logs/ 2>/dev/null || true

# 14. STWÓRZ PROSTSZY SKRYPT KONFIGURACJI
log_info "Tworzenie prostego skryptu konfiguracyjnego..."
cat > setup_simple.py << 'EOF'
#!/usr/bin/env python3
"""
Prosty konfigurator TPMB Android
Wersja odporna na błędy dla Termux
"""

import os
from pathlib import Path

def main():
    print("🤖 Prosty Konfigurator TPMB Android")
    print("🔧 Wersja odporna na błędy")
    print("=" * 40)
    
    # Stwórz katalogi
    try:
        config_dir = Path("instances/default/config")
        config_dir.mkdir(parents=True, exist_ok=True)
        logs_dir = Path("instances/default/logs")
        logs_dir.mkdir(parents=True, exist_ok=True)
        print("✅ Katalogi utworzone")
    except Exception as e:
        print(f"⚠️  Problem z katalogami: {e}")
        return
    
    # Token bota
    print("\n🔑 Token Telegram Bot:")
    print("💡 Zdobądź token od @BotFather")
    token = input("Wpisz token: ").strip()
    
    if not token:
        token = "PLACEHOLDER_TOKEN"
        print("⚠️  Używam placeholder - zmień później!")
    
    try:
        with open(config_dir / "bot_token.txt", "w") as f:
            f.write(token)
        print("✅ Token zapisany")
    except Exception as e:
        print(f"❌ Błąd zapisu tokena: {e}")
        return
    
    # ID admin
    print("\n👤 Twoje Telegram ID:")
    print("💡 Zdobądź od @userinfobot")
    admin_id = input("Wpisz ID (lub Enter = 123456789): ").strip()
    
    if not admin_id:
        admin_id = "123456789"
    
    try:
        with open(config_dir / "settings.txt", "w") as f:
            f.write(f"interval_minutes=5\n")
            f.write(f"admin_ids={admin_id}\n")
        print("✅ Ustawienia zapisane")
    except Exception as e:
        print(f"❌ Błąd zapisu ustawień: {e}")
        return
    
    # Wiadomość
    message = "Hello from TPMB Android! 🤖📱"
    try:
        with open(config_dir / "messages.txt", "w") as f:
            f.write(message)
        with open(config_dir / "groups.txt", "w") as f:
            f.write("")
        print("✅ Konfiguracja zakończona!")
    except Exception as e:
        print(f"❌ Błąd zapisu konfiguracji: {e}")
        return
    
    print("\n🚀 Uruchom bota: python main.py")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Przerwano przez użytkownika")
    except Exception as e:
        print(f"\n❌ Nieoczekiwany błąd: {e}")
EOF

chmod +x setup_simple.py

# 15. TEST KOŃCOWY
log_info "Test końcowy instalacji..."
python -c "
import sys
print('🧪 Test końcowy:')

# Test podstawowej funkcjonalności Python
try:
    import os, json, asyncio
    print('✅ Podstawowe moduły Python')
except Exception as e:
    print(f'❌ Podstawowe moduły: {e}')

# Test Telegram Bot
try:
    import telegram
    print('✅ Telegram Bot Library')
    telegram_ok = True
except Exception as e:
    print(f'❌ Telegram Bot: {e}')
    telegram_ok = False

# Test struktury katalogów
try:
    from pathlib import Path
    Path('instances/default/config').mkdir(parents=True, exist_ok=True)
    Path('instances/default/logs').mkdir(parents=True, exist_ok=True)
    print('✅ Struktura plików')
except Exception as e:
    print(f'❌ Struktura plików: {e}')

# Podsumowanie
if telegram_ok:
    print('\n🎉 INSTALACJA PRAWDOPODOBNIE UDANA!')
    print('Uruchom: python setup_simple.py')
else:
    print('\n⚠️  INSTALACJA Z PROBLEMAMI')
    print('Telegram Bot może nie działać, ale można spróbować')
"

# 16. PODSUMOWANIE
echo ""
log_success "Proces naprawy zakończony!"
echo ""
log_info "🎯 Następne kroki:"
log_info "1. python setup_simple.py    # Prosta konfiguracja"
log_info "2. python main.py            # Próba uruchomienia"
echo ""
log_info "🔧 W razie problemów:"
log_info "- bash tpmb_diagnostic.sh    # Diagnostyka"  
log_info "- Zrestartuj Termux całkowicie"
log_info "- Sprawdź czy masz wystarczająco miejsca"
echo ""
if [ ! -f "/data/data/com.termux/files/usr/etc/termux.conf" ]; then
    log_error "OSTRZEŻENIE: Prawdopodobnie używasz Termux z Play Store!"
    log_error "Dla pełnej funkcjonalności zainstaluj Termux z F-Droid"
fi

log_info "📱 Status: Instalacja dostosowana do Twoich problemów"
