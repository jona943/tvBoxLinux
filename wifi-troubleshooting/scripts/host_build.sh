#!/usr/bin/env bash

# Script para automatizar la compilación cruzada del driver de Wi-Fi AIC8800 en el PC Host.
# Debe ejecutarse en el PC principal de desarrollo.

set -e

# Configuración de rutas
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DOWNLOADS_DIR="$BASE_DIR/downloads"
HEADERS_DEB="$DOWNLOADS_DIR/linux-headers-current-sunxi64_24.8.4_arm64.deb"
HEADERS_EXTRACTED="$DOWNLOADS_DIR/headers_extracted"
KDIR="$HEADERS_EXTRACTED/usr/src/linux-headers-6.6.44-current-sunxi64"
DRIVER_DIR="$DOWNLOADS_DIR/aic8800"
DEPLOY_DIR="$BASE_DIR/wifi-troubleshooting/deploy"

echo "=== 1. Verificando e instalando herramientas de compilación en el PC Host ==="
REQUIRED_PACKAGES=(build-essential gcc-aarch64-linux-gnu flex bison curl git)
MISSING_PACKAGES=()

for pkg in "${REQUIRED_PACKAGES[@]}"; do
    if ! dpkg -l | grep -q "ii  $pkg "; then
        MISSING_PACKAGES+=("$pkg")
    fi
done

if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
    echo "Instalando paquetes faltantes: ${MISSING_PACKAGES[*]}"
    sudo apt update
    sudo apt install -y "${MISSING_PACKAGES[@]}"
else
    echo "Todas las herramientas necesarias ya están instaladas."
fi

echo "=== 2. Preparando directorios ==="
mkdir -p "$DOWNLOADS_DIR"
mkdir -p "$DEPLOY_DIR"

# Verificar si el .deb de las cabeceras existe
if [ ! -f "$HEADERS_DEB" ]; then
    echo "Descargando cabeceras del kernel 6.6.44..."
    wget -O "$HEADERS_DEB" "https://apt.armbian.com/pool/main/l/linux-headers-current-sunxi64/linux-headers-current-sunxi64_24.8.4_arm64__6.6.44-S7213-D53de-P4ceb-Cc287H5c21-HK01ba-Vc222-B58e9-R448a.deb"
fi

# Extraer el .deb si no se ha hecho
if [ ! -d "$HEADERS_EXTRACTED" ]; then
    echo "Extrayendo cabeceras de kernel..."
    mkdir -p "$HEADERS_EXTRACTED"
    dpkg -x "$HEADERS_DEB" "$HEADERS_EXTRACTED"
fi

# Clonar el driver si no existe
if [ ! -d "$DRIVER_DIR" ]; then
    echo "Clonando repositorio del driver aic8800..."
    git clone https://github.com/shenmintao/aic8800d80.git "$DRIVER_DIR"
fi

echo "=== 3. Descargando parches de herramientas de arquitectura ARM64 ==="
ARCH_TOOLS_DIR="$KDIR/arch/arm64/tools"
mkdir -p "$ARCH_TOOLS_DIR"

FILES_TO_PATCH=(
    "gen-cpucaps.awk"
    "cpucaps"
    "gen-sysreg.awk"
    "sysreg"
)

for file in "${FILES_TO_PATCH[@]}"; do
    if [ ! -f "$ARCH_TOOLS_DIR/$file" ]; then
        echo "Descargando $file..."
        curl -sL "https://raw.githubusercontent.com/torvalds/linux/v6.6/arch/arm64/tools/$file" > "$ARCH_TOOLS_DIR/$file"
    fi
done

echo "=== 4. Configurando y preparando las utilidades del kernel (modpost) ==="
make -C "$KDIR" ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- olddefconfig
make -C "$KDIR" ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- M=scripts/mod

echo "=== 5. Compilando el driver Wi-Fi aic8800 ==="
make -C "$DRIVER_DIR/drivers/aic8800" KDIR="$KDIR" ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu-

echo "=== 6. Creando paquete de despliegue para la TV Box ==="
cp "$DRIVER_DIR/drivers/aic8800/aic_load_fw/aic_load_fw.ko" "$DEPLOY_DIR/"
cp "$DRIVER_DIR/drivers/aic8800/aic8800_fdrv/aic8800_fdrv.ko" "$DEPLOY_DIR/"
cp -r "$DRIVER_DIR/fw/aic8800D80" "$DEPLOY_DIR/"
cp "$BASE_DIR/wifi-troubleshooting/scripts/tvbox_install.sh" "$DEPLOY_DIR/"

echo "=========================================================="
echo "¡Compilación completada con éxito!"
echo "Los archivos listos para la TV Box se encuentran en:"
echo " -> $DEPLOY_DIR"
echo "Copia toda esa carpeta 'deploy' a la MicroSD de tu TV Box."
echo "=========================================================="
