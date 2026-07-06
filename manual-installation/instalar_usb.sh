#!/usr/bin/env bash

# Script de instalación manual optimizado para USB externo
# Ejecutar como root (sudo ./instalar_usb.sh)

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

TARGET_DEV="/dev/sda"
TARGET_PART="/dev/sda1"
MOUNT_POINT="/mnt/usb"
EXCLUDE_FILE="/tmp/exclude.txt"

echo "=== INICIANDO INSTALACIÓN MANUAL EN USB EXTERNO ==="
echo "Dispositivo de destino: ${TARGET_DEV}"
echo "--------------------------------------------"

# 1. Desmontar cualquier residuo previo
echo "[1/7] Desmontando dispositivos..."
umount -l ${MOUNT_POINT} 2>/dev/null || true
umount -l /mnt 2>/dev/null || true
partprobe ${TARGET_DEV} || true
sleep 2

# 2. Formatear y preparar el USB
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
cat << 'EXCLUDE' > ${EXCLUDE_FILE}
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
EXCLUDE

# Aplicar límites de caché para estabilidad eléctrica
sysctl -w vm.dirty_background_bytes=4194304
sysctl -w vm.dirty_bytes=8388608

# 5. Copiar sistema raíz (rsync silencioso y controlado)
echo "[5/7] Copiando archivos de forma silenciosa (1.0 MB/s)..."
echo "Esta operación tomará aproximadamente 15-20 minutos. No apagues el dispositivo."
rsync -aqx --delete --bwlimit=1000 --exclude-from=${EXCLUDE_FILE} / ${MOUNT_POINT}/
echo "¡Copia de archivos finalizada con éxito!"

# 6. Configurar UUIDs en el USB
echo "[6/7] Configurando UUIDs en fstab y armbianEnv.txt..."
USB_UUID=$(blkid -o value -s UUID ${TARGET_PART})
echo "UUID detectado para el USB: ${USB_UUID}"

# Actualizar fstab en el destino
cat << 'FSTAB' > ${MOUNT_POINT}/etc/fstab
# <file system>					<mount point>	<type>	<options>							<dump>	<pass>
UUID=${USB_UUID}		/		ext4	defaults,noatime,commit=600,errors=remount-ro		0	1
tmpfs						/tmp		tmpfs	defaults,nosuid							0	0
FSTAB

# Reemplazar UUID en fstab destino con el real
sed -i "s/\${USB_UUID}/${USB_UUID}/g" ${MOUNT_POINT}/etc/fstab

# Actualizar armbianEnv.txt en el destino
if [ -f ${MOUNT_POINT}/boot/armbianEnv.txt ]; then
    sed -i "s/^rootdev=UUID=.*/rootdev=UUID=${USB_UUID}/" ${MOUNT_POINT}/boot/armbianEnv.txt
    if ! grep -q "extraargs=" ${MOUNT_POINT}/boot/armbianEnv.txt; then
        echo "extraargs=systemd.unit=multi-user.target" >> ${MOUNT_POINT}/boot/armbianEnv.txt
    fi
fi

# 7. Escribir cargador de arranque U-Boot
echo "[7/7] Escribiendo cargador de arranque U-Boot..."
dd if=/dev/mmcblk0 of=${TARGET_DEV} bs=1024 skip=8 seek=8 count=1024 conv=fsync,notrunc
echo "¡U-Boot copiado correctamente desde la MicroSD!"

# Desmontar y finalizar
echo "Desmontando USB..."
umount ${MOUNT_POINT}
echo "--------------------------------------------"
echo "=== ¡INSTALACIÓN COMPLETADA CON ÉXITO! ==="
echo "Prueba de copiado a almacenamiento externo USB finalizada."
