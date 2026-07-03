# Proyecto TV-Box Linux

Este repositorio contiene la documentación técnica, scripts y herramientas para la instalación de una distribución Linux compatible en una TV-box china.

## Estructura del Repositorio
* `ai-memory/`: Directorio que contiene las memorias de sesión para el seguimiento de la interacción.
* `.tmp/platform-tools/`: Copia local de Android Platform Tools (contiene `adb`).
* `README.md`: Documentación técnica principal y estado actual del proyecto (este archivo).

---

## Sección 1: Identificación del Hardware (En Proceso)

### Estado Actual del Dispositivo
* **Marca/Modelo Comercial:** Mortal T1 (Motrtal T1)
* **Especificaciones indicadas por carcasa:** 2GB RAM / 16GB ROM / MAC `00:1A:79:30:A6:E8`
* **SoC Detectado:** Allwinner (Vendor ID `1f3a`, Product ID `1007`)
* **Modelo estimado de SoC:** **Allwinner H313** o **Allwinner H616**

### Diagnóstico de Conectividad USB/ADB
Al conectar la TV-box al puerto USB del host, el comando `lsusb` la detecta como:
`Bus 002 Device 013: ID 1f3a:1007 Allwinner Technology Mortal T1`

La interfaz USB expone dos descriptores de clase específica del vendedor, uno de ellos corresponde a la interfaz ADB (`bInterfaceClass 255`, `bInterfaceSubClass 66`, `bInterfaceProtocol 1`).

#### Intentos de Conexión Realizados
1. **Herramienta ADB Local:** Descargada en `.tmp/platform-tools/adb`.
2. **Configuración de Vendor ID:** Se agregó `0x1f3a` a `~/.android/adb_usb.ini`.
3. **Resultado:** `./adb devices` aún no lista el dispositivo.

### Pendientes para la Siguiente Sesión
1. **Activar Depuración USB:** Confirmar si la depuración USB está activa en la TV-box desde la interfaz gráfica de Android TV.
2. **Permisos de udev en el Host:** Crear una regla de udev en `/etc/udev/rules.d/51-android.rules` si se requiere acceso de lectura/escritura sin root para el Vendor ID `1f3a`.
3. **Extracción de Datos Técnicos:**
   Una vez lograda la conexión ADB, extraer:
   * CPU Info: `adb shell cat /proc/cpuinfo`
   * Particiones de Almacenamiento: `adb shell cat /proc/partitions`
   * Módulo de Wi-Fi y Bluetooth: `adb shell dmesg | grep -i wlan`
