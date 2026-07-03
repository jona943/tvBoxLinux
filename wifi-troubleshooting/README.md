# Diagnóstico y Plan de Solución: Interfaz Wi-Fi Inexistente (AIC8800) en Armbian

Este documento registra la falta de conectividad inalámbrica en la TV Box Mortal T1 (Allwinner H313) después de iniciar con éxito en la consola de Armbian, detallando las salidas obtenidas, la causa raíz y la metodología de solución fuera de línea (offline).

---

## 1. Síntomas y Errores Presentados

Al intentar configurar la red Wi-Fi `DeltaNet-2G` usando la herramienta interactiva `nmtui` o directamente por comandos de consola, el sistema indicaba que la red era inaccesible o fallaba al realizar la conexión.

### Salida de la Consola en la TV Box:
Al inspeccionar el estado de los dispositivos de red con el comando:
```bash
nmcli device status
```
La consola devolvió una salida similar a la siguiente:
```text
DEVICE             TYPE      STATE         CONNECTION
end0               ethernet  unavailable   --
lo                 loopback  unmanaged     --
```
**Observación Crítica:** La interfaz inalámbrica típica **`wlan0`** no figura en el listado de dispositivos de red.

---

## 2. Análisis del Problema y Causa Raíz

1. **Hardware Inalámbrico Dedicado:** De acuerdo con la información obtenida de la memoria de la sesión anterior en Android, el dispositivo posee un chip Wi-Fi integrado **AIC8800** (que utiliza los módulos de kernel `aic8800_fdrv`, `aic8800_bsp` y `aic8800_btlpm`).
2. **Falta de Soporte Nativo en Linux:** El chip AIC8800 no está soportado nativamente en la rama principal (mainline) del kernel de Linux, por lo que requiere controladores compilados fuera del árbol (out-of-tree drivers).
3. **Ausencia de Drivers y Cabeceras en la Imagen:** La imagen de Armbian no incluye el driver compilado ni los archivos de firmware del fabricante para el chip AIC8800.
4. **Ausencia de Cabeceras de Desarrollo:** Al ejecutar:
   ```bash
   ls -l /usr/src
   ```
   La consola devolvió:
   ```text
   total 0
   ```
   Esto confirma que no existen las cabeceras del kernel (`linux-headers`) instaladas, lo que impide compilar cualquier driver desde el código fuente directamente en la TV Box.
5. **Aislamiento Físico (Sin Ethernet):** Al tratarse de una TV Box reducida en costes, **no dispone de puerto Ethernet físico (RJ45)**, por lo que no es posible conectarla al router por cable para descargar paquetes de forma directa desde internet.

---

## 3. Plan de Solución Offline (Paso a Paso)

Para solucionar esto, realizaremos un puenteo de datos utilizando el PC host para descargar las dependencias y el código del driver, los copiaremos a la tarjeta MicroSD y luego realizaremos la instalación local.

### Paso 1: Descargar Cabeceras del Kernel en el PC Host
Descargaremos el paquete oficial de cabeceras correspondiente exactamente a la versión de kernel en ejecución (`6.6.44-current-sunxi64`):
*   **Paquete:** `linux-headers-current-sunxi64_24.8.4_arm64.deb`
*   **Origen:** Repositorios oficiales de Armbian (`apt.armbian.com`).

### Paso 2: Descargar el Código del Driver en el PC Host
Clonaremos el repositorio del driver Wi-Fi AIC8800 de Larry Finger (`lwfinger/aic8800`) en el PC principal. Este código ya viene preparado con los archivos de firmware del chip listos para ser copiados a la carpeta `/lib/firmware/` de la TV Box.

### Paso 3: Transferir Datos a la MicroSD
Con la tarjeta MicroSD conectada al PC, copiaremos el archivo `.deb` y la carpeta del código fuente a la partición de almacenamiento de usuario (`armbi_root`) bajo el directorio del usuario personal (ej. `/home/dev-jonathan/` o `/root/`).

### Paso 4: Instalar Cabeceras en la TV Box
Una vez que arranquemos la TV Box con la MicroSD, instalaremos el paquete de cabeceras de forma local sin requerir internet:
```bash
sudo dpkg -i linux-headers-current-sunxi64_24.8.4_arm64...deb
```

### Paso 5: Compilar e Instalar el Driver
Entraremos a la carpeta del driver y ejecutaremos la compilación:
```bash
cd aic8800
make
sudo make install
```
*   Esto compilará los módulos `aic8800_fdrv.ko` y los copiará al sistema de módulos de Linux, además de instalar los firmwares necesarios en `/lib/firmware/aic8800/`.

### Paso 6: Activar la Interfaz inalámbrica
Cargaremos el driver en memoria:
```bash
sudo depmod -a
sudo modprobe aic8800_fdrv
```
Y confirmaremos que la interfaz `wlan0` ya está activa y lista para recibir conexiones con `nmcli`.

---

## 4. Conclusión
Este tipo de problemas es habitual al reciclar TV Boxes de bajo coste. Al documentar y seguir el flujo de instalación offline, garantizamos un método replicable para habilitar conectividad inalámbrica sin depender de interfaces físicas como Ethernet.
