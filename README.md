# <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/linux/linux-original.svg" width="35" height="35" valign="middle" /> Proyecto TV-Box Linux: Mortal T1 (Allwinner H313)

[![OS - Linux ARM64](https://img.shields.io/badge/OS-Linux_ARM64-FCC624?style=for-the-badge&logo=linux&logoColor=black)](#)
[![Distro - Armbian Linux](https://img.shields.io/badge/Distro-Armbian_Linux-111111?style=for-the-badge&logo=arm&logoColor=white)](#)
[![SoC - Allwinner H313](https://img.shields.io/badge/SoC-Allwinner_H313-E31B23?style=for-the-badge&logo=microchip&logoColor=white)](#)
[![Language - Bash & C](https://img.shields.io/badge/Language-Bash_%26_C-4EAA25?style=for-the-badge&logo=gnu-bash&logoColor=white)](#)
[![Field - Hardware Hacking](https://img.shields.io/badge/Field-Hardware_Hacking-0052CC?style=for-the-badge&logo=linux&logoColor=white)](#)

Este repositorio contiene la documentación técnica, scripts de automatización de compilación cruzada y archivos parcheados para la instalación y optimización del sistema operativo **Armbian Linux** en la TV Box china **Mortal T1**.

---

## <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/gcc/gcc-original.svg" width="22" height="22" valign="middle" /> Especificaciones del Hardware

* **Modelo:** Mortal T1 (Clon X96Q)
* **SoC:** Allwinner H313 Quad-Core (Cortex-A53 ARM64)
* **Memoria RAM:** 2 GB LPDDR3 comercial (1.44 GB virtual en Kernel, pero **1 GB física real / Límite seguro < 500 MB**)
* **Almacenamiento:** 16 GB eMMC comercial (**8 GB física real** / ~7.3 GB útil)
* **Chip de Red (Wi-Fi/Bluetooth):** **AICSemi AIC8800** conectado mediante bus **SDIO** (sin puerto Ethernet físico)

---

## <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/debian/debian-original.svg" width="22" height="22" valign="middle" /> Auditoría de Hardware Real (Decodificación de Falsas Especificaciones)

Tras realizar auditorías físicas y pruebas de estrés controladas, se descubrió que el firmware y U-Boot del fabricante vienen adulterados de fábrica para maquillar las especificaciones. A continuación se detallan los límites reales encontrados:

| Componente | Especificación Comercial | Reportado por Kernel / OS | Hardware Físico Real | Límite Seguro de Operación y Observaciones |
| :--- | :---: | :---: | :---: | :--- |
| **Procesador (CPU)** | 4 Cores 1.5 GHz | 4 Cores 1.0 GHz | 4 Cores Cortex-A53 (H313) | **100% de uso estable** (máximo 62.3°C en pruebas de estrés). CPU y disipación térmica excelentes. |
| **Memoria RAM** | 2 GB | 1.44 GB | **1 GB (o 768 MB)** | **Menos de 500 MB** de uso total. El sistema colapsa al superar los ~600 MB debido a direccionamiento de memoria inexistente o caída de tensión en `VDD_DRAM`. |
| **eMMC (Disco)** | 16 GB | 7.3 GB | **8 GB** | **Flasheo secuencial a bajo nivel (2MB/s)** con pausas de sincronización física (`os.fdatasync`) para evitar picos de corriente. |
| **GPU (Video)** | Mali-G31 | Compartida | Mali-G31 MP2 (Shared) | **Modo Consola (sin interfaz gráfica)** para liberar memoria RAM y evitar congelamientos. |

---

## <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/git/git-original.svg" width="22" height="22" valign="middle" /> Estructura del Repositorio

* `boot-troubleshooting/`: Documentación sobre resolución de pantalla negra al iniciar y configuración del árbol de dispositivos (DTB).
* `wifi-troubleshooting/`: Documentación detallada del proceso técnico para compilar y cargar el driver inalámbrico offline.
    * `scripts/`: Scripts de automatización de compilación e instalación:
        * [`host_build.sh`](./wifi-troubleshooting/scripts/host_build.sh): Script ejecutable en el PC Host para configurar cabeceras y compilar drivers cruzados.
        * [`tvbox_install.sh`](./wifi-troubleshooting/scripts/tvbox_install.sh): Script ejecutable en la TV Box para copiar firmwares e instalar módulos.
    * `offline-files/`: Directorio autogestionado con los archivos de instalación offline para la MicroSD.
* `emmc-installation/`: Documentación y script parcheado para la instalación a eMMC de forma síncrona y estable:
    * [`armbian-install.patched`](./emmc-installation/armbian-install.patched): Copia del instalador de Armbian optimizado.
* `downloads/` *(Ignorado en Git)*: Descargas locales de cabeceras de kernel y repositorios clonados.

---

## <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/bash/bash-original.svg" width="22" height="22" valign="middle" /> Bitácora de Desafíos y Soluciones Técnicas

### Desafío 1: Pantalla Negra en el Arranque (LightDM Crash)
* **Síntoma:** Al arrancar Armbian en la TV Box, la salida de video HDMI se quedaba en negro.
* **Solución:** Se editó `/boot/armbianEnv.txt` en la MicroSD para:
    1. Forzar el DTB de hardware correcto: `fdtfile=allwinner/sun50i-h313-x96q-lpddr3.dtb`.
    2. Forzar el arranque en modo consola pura (TTY) desactivando temporalmente la interfaz gráfica: `extraargs=systemd.unit=multi-user.target`.

### Desafío 2: Kernel Panic local por falta de memoria e I/O en la TV Box
* **Síntoma:** Al intentar desempaquetar las cabeceras del kernel (`linux-headers`) en la TV Box, el sistema arrojaba un `Kernel Panic: Oops: 0000000096000004` (Fallo en el planificador EEVDF al intentar matar la tarea idle).
* **Solución:** Se migró a un entorno de **compilación cruzada en el PC Host** (Ubuntu 24.04 Noble) usando el compilador cruzado `aarch64-linux-gnu-gcc`, extrayendo las cabeceras localmente en el PC y evitando sobrecargar la RAM/CPU de la TV Box.

### Desafío 3: Conflicto de Versión del Kernel (`Exec format error`)
* **Síntoma:** Al intentar cargar el primer driver compilado cruzado en la TV Box, devolvía `Exec format error` debido a que el *vermagic* del módulo no coincidía con el del kernel de la TV Box.
* **Solución:** Se parcheó el archivo `include/generated/utsrelease.h` de las cabeceras de compilación en el PC Host para forzar la cadena exacta de la versión de kernel corriendo en la TV Box (`"6.6.44-current-sunxi64"` en lugar de `"6.6.44"`).

### Desafío 4: Error de Bus en Drivers de Wi-Fi (`No such device` / `aic_patch_table_alloc fail`)
* **Síntoma:** Los drivers compilados originalmente bajo el bus USB se cargaban pero no detectaban ningún hardware, y la TV Box requiere drivers SDIO.
* **Solución:** 
    1. Se migró la base de código al repositorio del driver SDIO de Radxa.
    2. Se compilaron los tres módulos esenciales para SDIO: `aic8800_bsp.ko` (módulo de placa), `aic8800_fdrv.ko` (tarjeta de red) y `aic8800_btlpm.ko` (bluetooth).
    3. Se cambió la ruta del firmware dentro de `aic8800_bsp/Makefile` para apuntar al directorio estándar de Linux `/lib/firmware/aic8800D80` en lugar de la ruta de Android `/vendor/etc/firmware`.

### Desafío 5: Congelamiento (Kernel Panic) al intentar instalar en memoria eMMC interna
* **Síntoma:** Durante `armbian-install`, el sistema colapsaba por completo al llegar a "Counting files ... few seconds" o al 3% de copiado.
* **Solución:** Se parcheó el script `armbian-install` en la MicroSD para:
    1. Evitar el `rsync` de conteo síncrono que realizaba una copia completa oculta al inicio; se sustituye por `find / -xdev | wc -l` (conteo de metadatos instantáneo).
    2. Forzar escrituras síncronas al montar la eMMC (`-o sync`) eliminando picos eléctricos/térmicos por vaciado masivo de caché (*dirty page flushing*).
    3. Limitar la tasa de transferencia de datos a un nivel seguro y constante de 4 MB/s (`--bwlimit=4000`).

### Desafío 6: Inestabilidad eléctrica del sistema con interfaz gráfica (Desktop)
* **Síntoma:** El sistema seguía presentando congelamientos al 1% del proceso de instalación en la eMMC, incluso reduciendo el governor de la CPU y limitando la velocidad de copiado. Además, el arranque inicial de la versión con escritorio MATE requería configuraciones manuales de udev y systemd unit para evitar pantallas negras en HDMI.
* **Solución:** Se decidió cambiar de estrategia y migrar a una **imagen Armbian CLI/Minimal (Servidor)**. Esta versión no tiene interfaz gráfica que cause pantallas negras, consume solo ~150 MB de RAM y es un 70% más ligera, reduciendo la carga física sobre el bus de eMMC y el consumo de corriente.

#### Imágenes Armbian Utilizadas:
* **Imagen Anterior (MATE Desktop / Kernel 6.6.44):** [Armbian Unofficial MATE Desktop 24.11.0](https://github.com/sicXnull/armbian-build/releases/download/v24.8.0-trunk.425/Armbian-unofficial_24.11.0-trunk_X96q_bookworm_current_6.6.44_mate_desktop.img.xz)
* **Imagen Nueva (Minimal CLI / Kernel 6.12.64):** [Armbian Unofficial Minimal CLI 26.02.0](https://github.com/sicXnull/armbian-build/releases/download/v24.8.0-trunk.425/Armbian-unofficial_26.02.0-trunk_X96q-v1-3_bookworm_current_6.12.64_minimal.img.xz)

### Desafío 7: La RAM Falsa (Fake RAM) y la Solución Definitiva de Flasheo por Red
* **Síntoma:** El sistema seguía congelándose al copiar archivos grandes por red (como SCP) o al intentar descomprimir la imagen localmente, incluso con baja temperatura y CPU descansada. En `htop`, el consumo se reportaba en 119 MB, pero la barra de memoria (Caché de Páginas) se llenaba provocando un Kernel Panic inmediato (`Internal error: Oops - Undefined instruction` en `swapper/0`).
* **Diagnóstico:** 
    1. **RAM Falseada:** La TV Box está configurada por firmware para reportar virtualmente 1.44 GB al Kernel, pero físicamente cuenta con un chip de apenas **1 GB** (o 768 MB). Al intentar pasar el umbral físico de ~600 MB (incluyendo la caché de escritura de Linux o *Page Cache*), el kernel intenta escribir o escanear direcciones físicas inexistentes, corrompiendo su propio código cargado en memoria.
    2. **Fatiga de la eMMC Worn-Out:** La memoria eMMC tiene entre el 70% y 80% de su vida útil consumida. Escribir de forma continua a alta velocidad genera demandas de corriente tan altas en sus bombas de carga internas que provoca caídas de tensión (sags eléctricos) en los reguladores de la placa.
* **Solución Definitiva:**
    1. **Pre-descompresión en PC Host:** Se descomprime la imagen `.img.xz` en la PC de desarrollo antes de enviarla, eliminando el uso de CPU y buffers pesados de descompresión LZMA en la TV Box.
    2. **Streaming Directo con `oflag=direct`:** Se transmite la imagen cruda mediante SSH volcándola directamente en la eMMC (`/dev/mmcblk2`) usando `dd` con la bandera `oflag=direct`. Esto desactiva el Page Cache de Linux, manteniendo el uso de memoria RAM estrictamente plano en **119 MB** (0% de caché) de inicio a fin.
    3. **Dosificación en Ráfagas Cortas (`sleep` regulado):** Se programó el script de streaming en el Host para enviar bloques de **256 KB** con una pausa de **80 ms** entre bloques (velocidad promedio de ~1.8 MB/s), dando al regulador de la placa el 98% de tiempo en reposo para estabilizar su tensión y temperatura.
    4. **Post-Configuración de UUIDs:** Se realiza de forma automatizada un `tune2fs` para generar un UUID aleatorio para la eMMC y se actualizan de forma síncrona los archivos `/etc/fstab` y `/boot/armbianEnv.txt` en la partición montada.

---

## <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/vscode/vscode-original.svg" width="22" height="22" valign="middle" /> Repositorios Consultados y Créditos

* **Radxa Kernel Modules (Mantenedores de Radxa):** [radxa-pkg/aic8800](https://github.com/radxa-pkg/aic8800) — Código base del controlador SDIO compatible con el kernel 6.6 (`aic8800_bsp`, `aic8800_fdrv`, `aic8800_btlpm`).
* **Shenmintao aic8800d80:** [shenmintao/aic8800d80](https://github.com/shenmintao/aic8800d80) — Archivos de firmware y drivers USB del chip.
* **Linux Kernel Source (Linus Torvalds / ARM64):** [torvalds/linux](https://github.com/torvalds/linux) — Extracción de scripts de arquitectura ARM64 faltantes en las cabeceras de Armbian (`gen-cpucaps.awk`, `cpucaps`, `gen-sysreg.awk`, `sysreg`).
* **Repositorio Oficial de Armbian:** [Armbian Pool](https://apt.armbian.com) — Paquete oficial de cabeceras de desarrollo del kernel (`linux-headers-current-sunxi64_24.8.4_arm64.deb`).

---

<p align="center">
  <sub>Proyecto TV-Box Linux — Allwinner H313 (Mortal T1) | Desarrollado por Jonathan Medina</sub>
</p>
