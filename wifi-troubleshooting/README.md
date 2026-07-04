# Diagnóstico y Plan de Solución: Interfaz Wi-Fi Inexistente (AIC8800) en Armbian

Este documento registra la falta de conectividad inalámbrica en la TV Box Mortal T1 (Allwinner H313) después de iniciar con éxito en la consola de Armbian, detallando las salidas obtenidas, la causa raíz, la investigación de los Kernel Panics y la metodología de solución por compilación cruzada (cross-compilation) offline.

---

## 1. Síntomas y Errores Presentados

Al intentar configurar la red Wi-Fi `DeltaNet-2G` usando la herramienta interactiva `nmtui` o directamente por comandos de consola, el sistema indicaba que la red era inaccesible o fallaba al realizar la conexión.

### Salida de la Consola en la TV Box:
Al inspeccionar el estado de los dispositivos de red con el comando:
```bash
nmcli device status
```
La consola devolvió la siguiente salida:
```text
DEVICE             TYPE      STATE         CONNECTION
end0               ethernet  unavailable   --
lo                 loopback  unmanaged     --
```
**Observación Crítica:** La interfaz inalámbrica **`wlan0`** no figura en el listado de dispositivos de red.

---

## 2. Análisis del Problema y Causa Raíz

1. **Hardware Inalámbrico Dedicado:** De acuerdo con la información obtenida de la memoria de la sesión anterior en Android, el dispositivo posee un chip Wi-Fi integrado **AIC8800** (que utiliza los módulos de kernel `aic8800_fdrv`, `aic8800_bsp` y `aic8800_btlpm`).
2. **Falta de Soporte Nativo en Linux:** El chip AIC8800 no está soportado nativamente en la rama principal (mainline) del kernel de Linux, por lo que requiere controladores compilados fuera del árbol (out-of-tree drivers).
3. **Ausencia de Drivers y Cabeceras en la Imagen:** La imagen de Armbian no incluye el driver compilado ni los archivos de firmware del fabricante para el chip AIC8800.
4. **Ausencia de Cabeceras de Desarrollo:** Al ejecutar `ls -l /usr/src` la consola devolvió `total 0`, confirmando que no existen las cabeceras del kernel (`linux-headers`) instaladas, lo que impide compilar cualquier driver desde el código fuente directamente en la TV Box.

---

## 3. La Investigación: Inestabilidad y Kernel Panics durante la Instalación Local

Al intentar instalar las cabeceras del kernel (`linux-headers-current-sunxi64_24.8.4_arm64.deb`) directamente en la TV Box usando `dpkg -i`, el sistema se congelaba repetidamente a los pocos minutos, mostrando un **Kernel Panic** en pantalla:

```text
Internal error: Oops: 0000000096000004 [#4] SMP
Hardware name: X96Q TV-Box LPDDR3 (DT) y 6.6.44-current-sunxi64
...
Call trace:
 pick_next_task_fair -> _pick_eevdf -> pick_next_entity
...
---[ end Kernel panic - not syncing: Attempted to kill the idle task! ]---
```

### Análisis Técnico del Fallo:
1. **Fallo de Paginación / Data Abort (Oops: 0000000096000004):** El kernel intentó acceder a una dirección de memoria RAM no válida durante una interrupción de Entrada/Salida (I/O).
2. **Caída en el Planificador EEVDF:** La descompresión de miles de archivos pequeños de cabecera (`.h` y `.c`) saturó el bus de la MicroSD/eMMC y sobrecargó la CPU. El planificador EEVDF (encargado de decidir qué hilo de ejecución utiliza la CPU) experimentó una desreferenciación nula al intentar gestionar los hilos del proceso `dpkg`.
3. **Muerte del Proceso Idle (PID 0):** Al corromperse las estructuras de control en memoria, el kernel intentó terminar erróneamente la tarea inactiva del sistema (`swapper/0` o *idle task*). Debido a que un sistema operativo no puede funcionar sin esta tarea raíz, el kernel entró en pánico protector (*not syncing*) para evitar la corrupción masiva de datos en el almacenamiento.
4. **Factores de Hardware Comunes:** Estos fallos suelen estar relacionados con inestabilidades en la tabla DVFS (escalado de voltaje y frecuencia del procesador H313) configurada en el DTB, caídas de tensión en los reguladores de voltaje bajo carga extrema, o el sobrecalentamiento y mala calidad de los chips de memoria RAM LPDDR3 del TV Box.

---

## 4. Solución: Compilación Cruzada (Cross-Compilation) en el PC Host

Para evitar por completo sobrecargar la TV Box y prevenir los Kernel Panics, cambiamos de estrategia hacia la **compilación cruzada offline** en el PC principal de desarrollo.

### Investigación de Errores de Compilación Cruzada:

Al intentar compilar el driver en el PC host apuntando a las cabeceras extraídas de la TV Box:
```bash
make -C downloads/aic8800/drivers/aic8800 \
  KDIR=/home/dev-jonathan/Escritorio/entorno-prueba/tvBoxLinux/downloads/headers_extracted/usr/src/linux-headers-6.6.44-current-sunxi64 \
  ARCH=arm64 \
  CROSS_COMPILE=aarch64-linux-gnu-
```
Se presentó el siguiente error:
```text
/bin/sh: 1: scripts/basic/fixdep: not found
```

#### Causa del Conflicto de Arquitectura:
El archivo `.deb` de cabeceras se compiló originalmente para **ARM64**. La herramienta `fixdep` (un script auxiliar de compilación) venia precompilada en formato ARM64. Como el PC host de desarrollo corre en arquitectura **AMD64 (x86_64)**, el procesador del PC no pudo ejecutar el binario, interrumpiendo el flujo.

#### Solución Aplicada:
1. **Instalación de Compilador Nativo:** Se instaló `build-essential` en el PC host para disponer del compilador nativo de C (`gcc`).
2. **Reconstrucción de Scripts de Soporte:** Se ejecutó una recompilación local de los scripts de desarrollo del paquete de cabeceras en el PC host para que se ejecuten de forma nativa en x86_64:
   ```bash
   make -C downloads/headers_extracted/usr/src/linux-headers-6.6.44-current-sunxi64 ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- scripts
   ```
   Esto recrea `fixdep` y `modpost` en formato ejecutable para el PC principal.
3. **Compilación del Driver:** Con las herramientas preparadas, se ejecuta la compilación cruzada para generar los módulos `.ko` (`aic_load_fw.ko` y `aic8800_fdrv.ko`) dirigidos al kernel ARM64 de la TV Box.

---

## 5. Metodología de Instalación Final (Offline)

Una vez compilados los módulos `.ko` en el PC:
1. Copiaremos los dos archivos `.ko` y la carpeta de firmwares (`downloads/aic8800/fw/`) a la carpeta personal de tu MicroSD (`/home/dev12/`).
2. Introduciremos la MicroSD en la TV Box e iniciaremos en modo texto.
3. Copiaremos los firmwares y módulos manualmente a las rutas del sistema en la TV Box:
   ```bash
   # Copiar firmwares a su ruta del sistema
   sudo cp -r ~/aic8800/fw/aic8800D80 /lib/firmware/
   
   # Copiar módulos .ko a la ruta de drivers de red de Linux
   sudo mkdir -p /lib/modules/6.6.44-current-sunxi64/kernel/drivers/net/wireless/aic8800/
   sudo cp ~/aic_load_fw.ko /lib/modules/6.6.44-current-sunxi64/kernel/drivers/net/wireless/aic8800/
   sudo cp ~/aic8800_fdrv.ko /lib/modules/6.6.44-current-sunxi64/kernel/drivers/net/wireless/aic8800/
   
   # Registrar módulos en el sistema y levantarlos
   sudo depmod -a
   sudo modprobe aic8800_fdrv
   ```
4. Se configurará el Wi-Fi usando `nmcli`.
