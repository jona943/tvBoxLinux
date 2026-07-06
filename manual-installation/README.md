# Guía de Instalación Manual y Automatizada en eMMC (Armbian Minimal)

Este documento registra la estrategia final utilizada para transferir el sistema operativo Armbian Minimal (Servidor / Kernel 6.12.64) desde la tarjeta MicroSD (16 GB) a la memoria eMMC interna (8 GB) de la TV Box Mortal T1 (X96Q Clone), superando los desafíos eléctricos y de falta de paquetes.

---

## 1. Análisis de Capacidad y Estado de la eMMC
Tras una auditoría realizada el **Domingo 05 de Julio de 2026**, se determinó:
*   **Capacidad Real:** **7.3 GiB** utilizables en `/dev/mmcblk2`. El chip físico soldado es de **8 GB** (los 16 GB anunciados de fábrica son falsos).
*   **Estado de Salud:** Óptimo. Velocidad de escritura directa de **45.2 MB/s** y lectura de **84.0 MB/s**. Desgaste del chip entre el 70% y el 80% (saludable para operar durante años).
*   *Ver resultados completos en:* [AUDIT_RESULTS.md](AUDIT_RESULTS.md)

---

## 2. El Desafío Eléctrico (Wi-Fi + eMMC Writes)
Durante las pruebas de copia, el sistema se congelaba al cabo de unos minutos. El diagnóstico determinó que:
1.  La antena Wi-Fi USB externa demanda un alto consumo de corriente al transmitir miles de líneas de texto a través del SSH (producidas por el modo verbose de `rsync`).
2.  Al sumar el consumo de escritura física de la eMMC, el carril de 5V del puerto USB de la TV Box sufría una caída de tensión, congelando el procesador Allwinner H313.
3.  **Solución:** Desconectar físicamente la antena de Wi-Fi y realizar un copiado 100% local, silencioso (sin salida de terminal) y limitado a **1.0 MB/s** (`--bwlimit=1000`).

---

## 3. Automatización local: El Script `instalar_emmc.sh`
Dado que la imagen Minimal carece del paquete de bootloader de Armbian (`linux-u-boot-current-x96q...`), no disponemos de un archivo `u-boot.bin` precompilado en el sistema de archivos.

**Solución aplicada:** El script extrae y copia el sector de arranque U-Boot directamente de la MicroSD en funcionamiento (`/dev/mmcblk0`) hacia la eMMC (`/dev/mmcblk2`) saltándose la tabla de particiones del sector 0:
```bash
dd if=/dev/mmcblk0 of=/dev/mmcblk2 bs=1024 skip=8 seek=8 count=1024 conv=fsync,notrunc
```

El script finalizado y guardado en `~/automatizacion/instalar_emmc.sh` es el siguiente:

```bash
#!/usr/bin/env bash
set -e

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

# 6. Configurar UUIDs en la eMMC
echo "[6/7] Configurando UUIDs en fstab y armbianEnv.txt..."
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
```

---

## 4. Flujo de Trabajo para la Instalación

1.  Crear la carpeta localmente en la TV Box: `mkdir -p ~/automatizacion`.
2.  Crear el archivo `instalar_emmc.sh` con el contenido del script y darle permisos de ejecución (`chmod +x instalar_emmc.sh`).
3.  Apagar la TV Box y **desconectar físicamente la antena Wi-Fi USB** de la TV Box.
4.  Encender el dispositivo y acceder a la terminal de comandos directamente mediante la salida local (HDMI + Teclado USB).
5.  Correr la automatización:
    ```bash
    cd ~/automatizacion
    sudo ./instalar_emmc.sh
    ```
6.  Esperar a que termine. Cuando el mensaje en pantalla indique la finalización exitosa, retirar la MicroSD y reiniciar.
