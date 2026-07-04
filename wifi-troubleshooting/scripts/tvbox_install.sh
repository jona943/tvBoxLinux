#!/usr/bin/env bash

# Script para automatizar la instalación de los módulos compilados de Wi-Fi y firmwares en la TV Box.
# Debe ejecutarse con privilegios de root (sudo) en la TV Box.

set -e

if [ "$EUID" -ne 0 ]; then
    echo "Error: Este script debe ejecutarse como root (usa sudo)."
    exit 1
fi

KVER=$(uname -r)
FW_SRC="./aic8800D80"
MOD_SRC_1="./aic_load_fw.ko"
MOD_SRC_2="./aic8800_fdrv.ko"
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
if [ -f "$MOD_SRC_1" ] && [ -f "$MOD_SRC_2" ]; then
    echo "Creando directorio de destino $MOD_DEST..."
    mkdir -p "$MOD_DEST"
    echo "Copiando módulos .ko..."
    cp "$MOD_SRC_1" "$MOD_DEST/"
    cp "$MOD_SRC_2" "$MOD_DEST/"
else
    echo "Error: No se encontraron los archivos de módulos compilados (.ko)."
    exit 1
fi

echo "=== 3. Registrando módulos en el sistema ==="
depmod -a

echo "=== 4. Cargando driver de red aic8800 ==="
# Intentamos remover si había alguna carga previa limpia
modprobe -r aic8800_fdrv 2>/dev/null || true
modprobe aic8800_fdrv

echo "=== 5. Comprobando resultado ==="
sleep 2

if ip link show wlan0 >/dev/null 2>&1; then
    echo "=========================================================="
    echo "¡INSTALACIÓN COMPLETADA CON ÉXITO!"
    echo "La interfaz inalámbrica 'wlan0' ya está activa."
    echo "----------------------------------------------------------"
    echo "Estado de la interfaz:"
    nmcli device status | grep wlan0 || ip link show wlan0
    echo "----------------------------------------------------------"
    echo "Para conectarte al Wi-Fi, ejecuta ahora:"
    echo " -> nmcli device wifi connect \"DeltaNet-2G\" password \"TU_CONTRASEÑA\""
    echo "=========================================================="
else
    echo "Error: Los módulos se instalaron, pero la interfaz 'wlan0' no se activó."
    echo "Revisa la salida de dmesg para buscar errores: dmesg | tail -n 20"
fi
