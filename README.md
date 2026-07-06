# Proyecto TV-Box Linux: Mortal T1 (Allwinner H313)

Este repositorio contiene la documentación técnica, scripts de automatización y archivos compilados para la instalación y configuración de la distribución Armbian Linux en la TV Box china **Mortal T1**.

---

## 1. Especificaciones del Hardware
*   **Modelo:** Mortal T1 (X96Q Clone)
*   **SoC:** Allwinner H313 Quad-Core (Cortex-A53)
*   **Memoria RAM:** 2 GB LPDDR3 comercial (1.44 GB virtual en Kernel, pero **~1 GB física real / Límite seguro < 500 MB**)
*   **Almacenamiento:** 16 GB eMMC comercial (**8 GB física real** / ~7.3 GB útil)
*   **Chip de Red (Wi-Fi/Bluetooth):** **AICSemi AIC8800** conectado mediante el bus **SDIO** (sin puerto Ethernet físico).

---

## 2. Auditoría de Hardware Real (Fake Specs Decrypted)
Tras realizar auditorías físicas y pruebas de estrés controladas, se descubrió que el firmware y U-Boot del fabricante vienen trucados de fábrica para maquillar las especificaciones. A continuación se detallan los límites reales que encontramos al someter al equipo a pruebas:

| Componente | Especificación Comercial | Reportado por Kernel / OS | Hardware Físico Real | Límite Seguro de Operación / Observaciones |
| :--- | :---: | :---: | :---: | :--- |
| **Procesador (CPU)** | 4 Cores 1.5 GHz | 4 Cores 1.0 GHz | 4 Cores Cortex-A53 (H313) | **100% de uso estable** (máx. 62.3°C en pruebas de estrés). La CPU y su disipación térmica son excelentes. |
| **Memoria RAM** | 2 GB | 1.44 GB | **1 GB (o 768 MB)** | **Menos de 500 MB** de uso total. El sistema colapsa de forma instantánea al superar los ~600 MB (se congela el SoC con ruido visual en pantalla) debido a direccionamiento de memoria física inexistente o caída de tensión en el carril `VDD_DRAM` por escritura masiva. |
| **eMMC (Disco)** | 16 GB | 7.3 GB | **8 GB** | **Flasheo secuencial a bajo nivel (2MB/s)** con pausas de sincronización física (`os.fdatasync`) para evitar picos de corriente. |
| **GPU (Video)** | Mali-G31 | Compartida | Mali-G31 MP2 (Shared) | **Modo Consola (sin interfaz gráfica)** para liberar memoria RAM y evitar congelamientos. |

---

## 3. Estructura del Repositorio
*   `boot-troubleshooting/`: Documentación sobre cómo resolver la pantalla negra al iniciar y configurar el árbol de dispositivos (DTB).
*   `wifi-troubleshooting/`: Documentación detallada del proceso técnico para compilar y cargar el driver inalámbrico offline.
    *   `scripts/`: Contiene los scripts de automatización de compilación e instalación.
        *   [host_build.sh](file:///home/dev-jonathan/Escritorio/entorno-prueba/tvBoxLinux/wifi-troubleshooting/scripts/host_build.sh): Script ejecutable en el PC Host para configurar cabeceras y compilar drivers cruzados.
        *   [tvbox_install.sh](file:///home/dev-jonathan/Escritorio/entorno-prueba/tvBoxLinux/wifi-troubleshooting/scripts/tvbox_install.sh): Script ejecutable en la TV Box para copiar firmwares e instalar módulos.
    *   `offline-files/`: Directorio autogestionado con los archivos de instalación offline listos para ser pasados a la MicroSD.
*   `emmc-installation/`: Documentación y script parcheado para la instalación a eMMC de forma síncrona y estable.
    *   [armbian-install.patched](file:///home/dev-jonathan/Escritorio/entorno-prueba/tvBoxLinux/emmc-installation/armbian-install.patched): Copia del instalador de Armbian optimizado y documentado.
*   `downloads/` *(Ignorado en Git)*: Descargas locales de cabeceras de kernel y repositorios clonados.

---

## 4. Bitácora de Desafíos y Soluciones

### Desafío 1: Pantalla Negra en el Arranque (LightDM Crash)
*   **Síntoma:** Al arrancar Armbian en la TV Box, la salida de video HDMI se quedaba en negro.
*   **Solución:** Editamos `/boot/armbianEnv.txt` en la MicroSD para:
    1.  Forzar el DTB de hardware correcto: `fdtfile=allwinner/sun50i-h313-x96q-lpddr3.dtb`.
    2.  Forzar el arranque en modo consola pura (TTY) desactivando temporalmente la interfaz gráfica: `extraargs=systemd.unit=multi-user.target`.

### Desafío 2: Kernel Panic local por falta de memoria e I/O en la TV Box
*   **Síntoma:** Al intentar desempaquetar las cabeceras del kernel (`linux-headers`) en la TV Box, el sistema arrojaba un `Kernel Panic: Oops: 0000000096000004` (Fallo en el planificador EEVDF al intentar matar la tarea idle).
*   **Solución:** Migramos a un entorno de **compilación cruzada en el PC Host** (Ubuntu 24.04 Noble) usando el compilador cruzado `aarch64-linux-gnu-gcc`, extrayendo las cabeceras localmente en el PC y evitando sobrecargar la RAM/CPU de la TV Box.

### Desafío 3: Conflicto de Versión del Kernel (`Exec format error`)
*   **Síntoma:** Al intentar cargar el primer driver compilado cruzado en la TV Box, devolvía `Exec format error` debido a que el *vermagic* del módulo no coincidía con el del kernel de la TV Box.
*   **Solución:** Parcheamos el archivo `include/generated/utsrelease.h` de las cabeceras de compilación en el PC Host para forzar la cadena exacta de la versión de kernel corriendo en la TV Box (`"6.6.44-current-sunxi64"` en lugar de `"6.6.44"`).

### Desafío 4: Error de Bus en Drivers de Wi-Fi (`No such device` / `aic_patch_table_alloc fail`)
*   **Síntoma:** Los drivers compilados originalmente bajo el bus USB se cargaban pero no detectaban ningún hardware, y la TV Box requiere drivers SDIO.
*   **Solución:** 
    1.  Migramos la base de código al repositorio del driver SDIO de Radxa.
    2.  Compilamos los tres módulos esenciales para SDIO: `aic8800_bsp.ko` (módulo de placa), `aic8800_fdrv.ko` (tarjeta de red) y `aic8800_btlpm.ko` (bluetooth).
    3.  Cambiamos la ruta del firmware dentro de `aic8800_bsp/Makefile` para que apunte al directorio estándar de Linux `/lib/firmware/aic8800D80` en lugar de la ruta de Android `/vendor/etc/firmware`.

### Desafío 5: Congelamiento (Kernel Panic) al intentar instalar en memoria eMMC interna
*   **Síntoma:** Durante `armbian-install`, el sistema colapsaba por completo al llegar a "Counting files ... few seconds" o al 3% de copiado.
*   **Solución:** Parcheamos el script `armbian-install` en la MicroSD para:
    1.  Evitar el `rsync` de conteo síncrono que realizaba una copia completa oculta al inicio; se sustituye por `find / -xdev | wc -l` (conteo de metadatos instantáneo).
    2.  Forzar escrituras síncronas al montar la eMMC (`-o sync`) eliminando picos eléctricos/térmicos por vaciado masivo de caché (*dirty page flushing*).
    3.  Limitar la tasa de transferencia de datos a un nivel seguro y constante de 4 MB/s (`--bwlimit=4000`).

### Desafío 6: Inestabilidad eléctrica del sistema con interfaz gráfica (Desktop)
*   **Síntoma:** El sistema seguía presentando congelamientos al 1% del proceso de instalación en la eMMC, incluso reduciendo el governor de la CPU y limitando la velocidad de copiado. Además, el arranque inicial de la versión con escritorio MATE requería configuraciones manuales de udev y systemd unit para evitar pantallas negras en HDMI.
*   **Solución:** Decidimos cambiar de estrategia y migrar a una **imagen Armbian CLI/Minimal (Servidor)**. Esta versión no tiene interfaz gráfica que cause pantallas negras, consume solo ~150 MB de RAM y es un 70% más ligera, lo que reduce la carga física sobre el bus de eMMC y el consumo de corriente, permitiendo una instalación 100% estable.

#### Imágenes Armbian Utilizadas:
*   **Imagen Anterior (MATE Desktop / Kernel 6.6.44):** [Armbian Unofficial MATE Desktop 24.11.0](https://github.com/sicXnull/armbian-build/releases/download/v24.8.0-trunk.425/Armbian-unofficial_24.11.0-trunk_X96q_bookworm_current_6.6.44_mate_desktop.img.xz)
*   **Imagen Nueva (Minimal CLI / Kernel 6.12.64):** [Armbian Unofficial Minimal CLI 26.02.0](https://github.com/sicXnull/armbian-build/releases/download/v24.8.0-trunk.425/Armbian-unofficial_26.02.0-trunk_X96q-v1-3_bookworm_current_6.12.64_minimal.img.xz)

### Desafío 7: La RAM Falsa (Fake RAM) y la Solución Definitiva de Flasheo por Red
*   **Síntoma:** El sistema seguía congelándose misteriosamente al copiar o subir archivos grandes por red (como SCP) o al intentar descomprimir la imagen localmente, incluso con baja temperatura y CPU descansada. En `htop`, el consumo se reportaba en apenas 119 MB de procesos, pero la barra visual de memoria (Caché de Páginas) se llenaba a más del 50%, provocando un Kernel Panic inmediato (`Internal error: Oops - Undefined instruction` en `swapper/0`).
*   **Diagnóstico:** 
    1. **RAM Falseada:** La TV Box está configurada por firmware para reportar virtualmente 1.44 GB al Kernel, pero físicamente cuenta con un chip de apenas **1 GB** (o 768 MB). Al intentar pasar el umbral físico de ~600 MB (incluyendo la caché de escritura de Linux o *Page Cache*), el kernel intenta escribir o escanear direcciones físicas inexistentes, lo que corrompe su propio código cargado en memoria y cuelga el SoC.
    2. **Fatiga de la eMMC Worn-Out:** La memoria eMMC tiene entre el 70% y 80% de su vida útil consumida. Escribir de forma continua a alta velocidad genera demandas de corriente tan altas en sus bombas de carga internas que provoca caídas de tensión (sags eléctricos) en los reguladores de la placa.
*   **Solución Definitiva:**
    1. **Pre-descompresión en PC Host:** Descomprimimos la imagen `.img.xz` en la PC de desarrollo antes de enviarla, eliminando el uso de CPU y buffers pesados de descompresión LZMA en la TV Box.
    2. **Streaming Directo con `oflag=direct`:** Transmitimos la imagen cruda mediante SSH y la volcamos directamente en la eMMC (`/dev/mmcblk2`) usando `dd` con la bandera `oflag=direct`. Esto desactiva el Page Cache de Linux, manteniendo el uso de memoria RAM estrictamente plano en **119 MB** (0% de caché) de inicio a fin.
    3. **Dosificación en Ráfagas Cortas (`sleep` regulado):** Programamos el script de streaming en el Host para enviar bloques de **256 KB** con una pausa de **80 ms** entre bloques (velocidad promedio de ~1.8 MB/s), dando al regulador de la placa el 98% de tiempo en reposo para estabilizar su tensión y temperatura.
    4. **Post-Configuración de UUIDs:** Una vez finalizada la transmisión sin un solo cuelgue, el script realiza de forma automatizada un `tune2fs` para generar un UUID aleatorio para la eMMC y actualiza de forma síncrona los archivos `/etc/fstab` y `/boot/armbianEnv.txt` en la partición montada.

---

## 5. Repositorios Consultados y Créditos
Agradecemos a los desarrolladores y mantenedores de los siguientes repositorios de software libre, los cuales sirvieron de base técnica, código y descarga de parches para hacer posible este proyecto:

*   **Radxa Kernel Modules (Mantenedores de Radxa):**
    *   *Repositorio:* [radxa-pkg/aic8800](https://github.com/radxa-pkg/aic8800)
    *   *Uso:* Código base del controlador SDIO compatible con el kernel 6.6 para los módulos `aic8800_bsp`, `aic8800_fdrv` y `aic8800_btlpm`.
*   **Shenmintao aic8800d80:**
    *   *Repositorio:* [shenmintao/aic8800d80](https://github.com/shenmintao/aic8800d80)
    *   *Uso:* Consulta inicial de archivos de firmware y drivers USB del chip.
*   **Linux Kernel Source (Linus Torvalds / ARM64 Mantenedores):**
    *   *Repositorio:* [torvalds/linux](https://github.com/torvalds/linux)
    *   *Uso:* Extracción de archivos de scripts de arquitectura ARM64 faltantes en el paquete de cabeceras de Armbian (`gen-cpucaps.awk`, `cpucaps`, `gen-sysreg.awk`, `sysreg`).
*   **Repositorio Oficial de Armbian:**
    *   *Servidor:* [Armbian Pool](https://apt.armbian.com)
    *   *Uso:* Descarga del paquete oficial de cabeceras de desarrollo del kernel (`linux-headers-current-sunxi64_24.8.4_arm64.deb`).
