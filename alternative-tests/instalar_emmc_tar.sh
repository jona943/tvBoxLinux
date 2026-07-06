#!/usr/bin/env bash

# Script de instalación manual en eMMC usando streaming secuencial con tar
# Desarrollado para evitar el estrés del controlador de RAM (DRAM hang)
# Ejecutar como root (sudo ./instalar_emmc_tar.sh)

set -e

# --- MODO ECO / BAJO CONSUMO ELÉCTRICO ---
echo "Configurando modo de ultra-bajo consumo..."
echo 0 > /sys/devices/system/cpu/cpu1/online || true
echo 0 > /sys/devices/system/cpu/cpu2/online || true
echo 0 > /sys/devices/system/cpu/cpu3/online || true

if [ -f /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq ]; then
    echo 480000 > /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq || true
    echo powersave > /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor || true
fi
# ------------------------------------------

TARGET_DEV="/dev/mmcblk2"
TARGET_PART="${TARGET_DEV}p1"
MOUNT_POINT="/mnt/emmc"

echo "=== INICIANDO INSTALACIÓN EN EMMC CON TAR (STREAMING SECUENCIAL) ==="
echo "Dispositivo de destino: ${TARGET_DEV}"
echo "--------------------------------------------"

# 1. Desmontar cualquier residuo previo
echo "[1/6] Desmontando dispositivos..."
umount -l ${MOUNT_POINT} 2>/dev/null || true
umount -l /mnt 2>/dev/null || true
partprobe ${TARGET_DEV} || true
sleep 2

# 2. Formatear y preparar la eMMC
echo "[2/6] Creando tabla de particiones y formateando..."
parted -s ${TARGET_DEV} mklabel msdos
parted -s ${TARGET_DEV} mkpart primary ext4 4MiB 100%
partprobe ${TARGET_DEV}
sleep 2

echo "Dando formato ext4 a ${TARGET_PART}..."
mkfs.ext4 -F -L "armbi_root" ${TARGET_PART}

# 3. Montar la partición destino
echo "[3/6] Montando la partición en ${MOUNT_POINT}..."
mkdir -p ${MOUNT_POINT}
mount ${TARGET_PART} ${MOUNT_POINT}

# 4. Copiar sistema raíz usando tar secuencial (sin estrés de CPU/RAM)
echo "[4/6] Copiando archivos de forma secuencial con tar..."
echo "Esta operación tomará aproximadamente 15 minutos. No apagues el dispositivo."

# Aplicar límites de caché para estabilidad
sysctl -w vm.dirty_background_bytes=4194304
sysctl -w vm.dirty_bytes=8388608

# Ejecutar el flujo secuencial de tar
cd /
tar --one-file-system --exclude='./home/dev12/automatizacion' -cf - . | tar -xf - -C ${MOUNT_POINT}

echo "¡Copia de archivos finalizada con éxito!"

# 5. Configurar UUIDs en la eMMC
echo "[5/6] Configurando UUIDs en fstab y armbianEnv.txt..."
EMMC_UUID=$(blkid -o value -s UUID ${TARGET_PART})
echo "UUID detectado para la eMMC: ${EMMC_UUID}"

# Actualizar fstab en el destino
cat << 'FSTAB' > ${MOUNT_POINT}/etc/fstab
# <file system>					<mount point>	<type>	<options>							<dump>	<pass>
UUID=${EMMC_UUID}		/		ext4	defaults,noatime,commit=600,errors=remount-ro		0	1
tmpfs						/tmp		tmpfs	defaults,nosuid							0	0
FSTAB

# Reemplazar UUID en fstab destino con el real
sed -i "s/\${EMMC_UUID}/${EMMC_UUID}/g" ${MOUNT_POINT}/etc/fstab

# Actualizar armbianEnv.txt en el destino
if [ -f ${MOUNT_POINT}/boot/armbianEnv.txt ]; then
    sed -i "s/^rootdev=UUID=.*/rootdev=UUID=${EMMC_UUID}/" ${MOUNT_POINT}/boot/armbianEnv.txt
    if ! grep -q "extraargs=" ${MOUNT_POINT}/boot/armbianEnv.txt; then
        echo "extraargs=systemd.unit=multi-user.target" >> ${MOUNT_POINT}/boot/armbianEnv.txt
    fi
fi

# 6. Escribir cargador de arranque U-Boot desde la MicroSD
echo "[6/6] Escribiendo cargador de arranque U-Boot desde la MicroSD (/dev/mmcblk0)..."
dd if=/dev/mmcblk0 of=${TARGET_DEV} bs=1024 skip=8 seek=8 count=1024 conv=fsync,notrunc
echo "¡U-Boot copiado correctamente desde la MicroSD!"

# Desmontar y finalizar
echo "Desmontando eMMC..."
umount ${MOUNT_POINT}
echo "--------------------------------------------"
echo "=== ¡INSTALACIÓN COMPLETADA CON ÉXITO! ==="
echo "Ya puedes apagar la TV Box, retirar la MicroSD y encenderla de nuevo."
