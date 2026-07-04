#!/usr/bin/env bash

# Script para automatizar la instalación de los módulos compilados de Wi-Fi y Bluetooth por SDIO en la TV Box.
# Debe ejecutarse con privilegios de root (sudo) en la TV Box.

set -e

if [ "$EUID" -ne 0 ]; then
    echo "Error: Este script debe ejecutarse como root (usa sudo)."
    exit 1
fi

KVER=$(uname -r)
FW_SRC="./aic8800D80"
FW_DEST="/lib/firmware"
MOD_DEST="/lib/modules/$KVER/kernel/drivers/net/wireless/aic8800"

echo "=== 1. Instalando archivos de firmware ==="
if [ -d "$FW_SRC" ]; then
    echo "Copiando carpeta de firmware a $FW_DEST..."
    cp -r "$FW_SRC" "$FW_DEST/"
else
    echo "Error: No se encontró la carpeta de firmware $FW_SRC."
    exit 1
fi

echo "=== 2. Instalando módulos de kernel (.ko) ==="
MODS=(
    "aic8800_bsp.ko"
    "aic8800_btlpm.ko"
    "aic8800_fdrv.ko"
)

mkdir -p "$MOD_DEST"

for mod in "${MODS[@]}"; do
    if [ -f "./$mod" ]; then
        echo "Copiando $mod a la ruta del sistema..."
        cp "./$mod" "$MOD_DEST/"
    else
        echo "Error: No se encontró el archivo del módulo ./$mod en el directorio actual."
        exit 1
    fi
done

echo "=== 3. Registrando módulos en el sistema ==="
depmod -a

echo "=== 4. Cargando drivers de red y bluetooth (SDIO) ==="
# Descargar previos si estaban activos
modprobe -r aic8800_btlpm 2>/dev/null || true
modprobe -r aic8800_fdrv 2>/dev/null || true
modprobe -r aic8800_bsp 2>/dev/null || true

# Cargar en orden de dependencia
echo "Cargando aic8800_bsp..."
modprobe aic8800_bsp
sleep 1

echo "Cargando aic8800_fdrv..."
modprobe aic8800_fdrv
sleep 1

echo "Cargando aic8800_btlpm (opcional, para Bluetooth)..."
modprobe aic8800_btlpm 2>/dev/null || true

echo "=== 5. Comprobando resultado ==="
sleep 2

if ip link show wlan0 >/dev/null 2>&1; then
    echo "=========================================================="
    echo "¡INSTALACIÓN COMPLETADA CON ÉXITO!"
    echo "La interfaz inalámbrica 'wlan0' ya está activa en modo SDIO."
    echo "----------------------------------------------------------"
    echo "Estado de la interfaz:"
    nmcli device status | grep wlan0 || ip link show wlan0
    echo "----------------------------------------------------------"
    echo "Para conectarte al Wi-Fi, ejecuta ahora:"
    echo " -> nmcli device wifi connect \"DeltaNet-2G\" password \"TU_CONTRASEÑA\""
    echo "=========================================================="
else
    echo "Error: Los módulos de SDIO se instalaron, pero la interfaz 'wlan0' no se activó."
    echo "Revisa la salida de dmesg para buscar errores: dmesg | tail -n 20"
fi
