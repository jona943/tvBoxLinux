#!/usr/bin/env bash

# Script de instalación manual optimizado para eMMC en TV Box
# Ejecutar como root (sudo ./instalar_emmc.sh)

set -e

# --- MODO ECO / BAJO CONSUMO ELÉCTRICO ---
echo "Configurando modo de ultra-bajo consumo..."
# Apagar núcleos 1, 2 y 3 para reducir consumo de corriente
echo 0 > /sys/devices/system/cpu/cpu1/online || true
echo 0 > /sys/devices/system/cpu/cpu2/online || true
echo 0 > /sys/devices/system/cpu/cpu3/online || true

# Limitar núcleo 0 al mínimo (480 MHz)
if [ -f /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq ]; then
    echo 480000 > /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq || true
    echo powersave > /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor || true
fi
# ------------------------------------------

TARGET_DEV="/dev/mmcblk2"
TARGET_PART="${TARGET_DEV}p1"
MOUNT_POINT="/mnt/emmc"
EXCLUDE_FILE="/tmp/exclude.txt"

echo "=== INICIANDO INSTALACIÓN MANUAL EN EMMC ==="
echo "Dispositivo de destino: ${TARGET_DEV}"
echo "--------------------------------------------"

# 1. Desmontar cualquier residuo previo
echo "[1/7] Desmontando dispositivos..."
umount -l ${MOUNT_POINT} 2>/dev/null || true
umount -l /mnt 2>/dev/null || true
partprobe ${TARGET_DEV} || true
sleep 2

# 2. Formatear y preparar la eMMC
echo "[2/7] Creando tabla de particiones y formateando..."
parted -s ${TARGET_DEV} mklabel msdos
parted -s ${TARGET_DEV} mkpart primary ext4 4MiB 100%
partprobe ${TARGET_DEV}
sleep 2

echo "Dando formato ext4 a ${TARGET_PART}..."
mkfs.ext4 -F -L "armbi_root" ${TARGET_PART}

# 3. Montar la partición destino
echo "[3/7] Montando la partición en ${MOUNT_POINT}..."
mkdir -p ${MOUNT_POINT}
mount ${TARGET_PART} ${MOUNT_POINT}

# 4. Crear archivo de exclusión y configurar límites
echo "[4/7] Configurando filtros y límites del kernel..."
cat <<EOF > ${EXCLUDE_FILE}
/boot/lost+found
/etc/fstab
/etc/fstab.d
/etc/udev/rules.d/70-persistent-net.rules
/var/lib/systemd/random-seed
/var/lib/urandom/random-seed
/var/log.hdd
/var/log
/tmp
/run
/proc
/sys
/dev
/mnt
/media
/lost+found
/home/dev12/automatizacion
EOF

# Aplicar límites de caché para estabilidad eléctrica
sysctl -w vm.dirty_background_bytes=4194304
sysctl -w vm.dirty_bytes=8388608

# 5. Copiar sistema raíz (rsync silencioso y controlado)
echo "[5/7] Copiando archivos de forma silenciosa y controlada (1.0 MB/s)..."
echo "Esta operación tomará aproximadamente 15-20 minutos. No apagues el dispositivo."
rsync -aqx --delete --bwlimit=1000 --exclude-from=${EXCLUDE_FILE} / ${MOUNT_POINT}/
echo "¡Copia de archivos finalizada con éxito!"

# 6. Configurar UUIDs en la eMMC
echo "[6/7] Configurando UUIDs en fstab y armbianEnv.txt..."
EMMC_UUID=$(blkid -o value -s UUID ${TARGET_PART})
echo "UUID detectado para la eMMC: ${EMMC_UUID}"

# Actualizar fstab en el destino
cat <<EOF > ${MOUNT_POINT}/etc/fstab
# <file system>					<mount point>	<type>	<options>							<dump>	<pass>
UUID=${EMMC_UUID}		/		ext4	defaults,noatime,commit=600,errors=remount-ro		0	1
tmpfs						/tmp		tmpfs	defaults,nosuid							0	0
EOF

# Actualizar armbianEnv.txt en el destino
if [ -f ${MOUNT_POINT}/boot/armbianEnv.txt ]; then
    sed -i "s/^rootdev=UUID=.*/rootdev=UUID=${EMMC_UUID}/" ${MOUNT_POINT}/boot/armbianEnv.txt
    # Asegurar argumentos de consola si hiciera falta
    if ! grep -q "extraargs=" ${MOUNT_POINT}/boot/armbianEnv.txt; then
        echo "extraargs=systemd.unit=multi-user.target" >> ${MOUNT_POINT}/boot/armbianEnv.txt
    fi
fi

# 7. Escribir cargador de arranque U-Boot
echo "[7/7] Escribiendo cargador de arranque U-Boot desde la MicroSD (/dev/mmcblk0)..."
dd if=/dev/mmcblk0 of=${TARGET_DEV} bs=1024 skip=8 seek=8 count=1024 conv=fsync,notrunc
echo "¡U-Boot copiado correctamente desde la MicroSD!" 

# Desmontar y finalizar
echo "Desmontando eMMC..."
umount ${MOUNT_POINT}
echo "--------------------------------------------"
echo "=== ¡INSTALACIÓN COMPLETADA CON ÉXITO! ==="
echo "Ya puedes apagar la TV Box, retirar la MicroSD y encenderla de nuevo."
