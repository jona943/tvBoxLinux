# Diagnóstico y Solución: Congelamiento (Kernel Panic) en la Instalación a eMMC

Este documento detalla la investigación técnica, causas y solución aplicadas al congelamiento del sistema en la TV Box Mortal T1 (Allwinner H313) al intentar ejecutar la instalación de Armbian a la memoria interna eMMC mediante `armbian-install`.

---

## 1. Síntomas del Fallo

Al iniciar el proceso de instalación nativa con:
```bash
sudo armbian-install
```
El sistema se congelaba por completo de forma aleatoria en una de estas dos fases:
1.  En la pantalla estática informativa **`Counting files ... few seconds.`** (durante 15 minutos o indefinidamente).
2.  Poco después de iniciar el copiado, comúnmente al llegar al **3%**.

En ambos casos, el dispositivo no respondía a comandos de consola, teclado ni red (congelamiento total de hardware debido a un Kernel Panic/Oops).

---

## 2. Análisis Técnico y Causa Raíz

### A. El problema del Conteo Síncrono ( rsync --stats )
Al examinar la línea 168 del script `/usr/sbin/armbian-install` original, descubrimos un error grave de optimización:
```bash
TODO=$(rsync -avx --delete --stats --exclude-from=$EX_LIST / "${TempDir}"/rootfs | grep "Number of files:"|awk '{print $4}' | tr -d '.,')
```
Para contar cuántos archivos existen y poder calcular la barra de progreso, el script ejecutaba un `rsync` completo y síncrono. Esto significa que **copiaba todos los gigabytes del sistema a la eMMC por primera vez en segundo plano** antes de iniciar la barra de progreso. Luego, volvía a ejecutar otro `rsync` por segunda vez para mostrar el progreso. Este esfuerzo masivo doble saturaba el hardware.

### B. Vaciado Masivo de Caché de Escritura (Dirty Page Flushing)
Por defecto, Linux utiliza una caché de escritura en RAM para acelerar los procesos de almacenamiento. Al escribir a gran velocidad:
1.  `rsync` llena la memoria RAM con "páginas sucias" (*dirty pages*).
2.  Al alcanzar el umbral del kernel, el sistema detiene el flujo y hace un **vaciado (flush) masivo** forzando la escritura al almacenamiento a la máxima velocidad física permitida por el bus.
3.  Esta transferencia masiva exige el máximo amperaje y disipación térmica tanto del controlador de memoria eMMC como de la RAM LPDDR3 y el SoC Allwinner H313.
4.  Debido a las deficiencias de diseño eléctrico o límites térmicos de estas placas de TV Box, la caída de tensión resultante o la inestabilidad de la memoria RAM congelaban la CPU en un Kernel Panic inmediato.

---

## 3. Estrategia de Solución Implementada

Para resolver este cuello de botella y garantizar una instalación estable, modificamos el instalador aplicando tres parches en el script `/usr/sbin/armbian-install`:

### 1. Reemplazo del Conteo Pesado por Conteo Rápido de Metadatos
Eliminamos la línea del `rsync --stats` síncrono y la reemplazamos por un conteo instantáneo que solo lee metadatos en 2 segundos sin realizar copias físicas:
```bash
TODO=$(find / -xdev | wc -l)
```

### 2. Forzado de Escritura Síncrona (`sync`)
Modificamos el montaje de la partición de la eMMC (líneas 115 y 117 del script) para forzar la opción de montaje **`-o sync`**:
```bash
[[ -n $2 ]] && ( mount -o compress-force=zlib,sync "$2" "${TempDir}"/rootfs 2> /dev/null || mount -o sync "$2" "${TempDir}"/rootfs )
```
Esto obliga a Linux a escribir cada archivo inmediatamente al almacenamiento en lugar de acumularlo en la memoria RAM, eliminando por completo los picos destructivos de vaciado de caché (*dirty page flushing*).

### 3. Límite del Ancho de Banda de Copiado (`--bwlimit`)
Agregamos el parámetro **`--bwlimit=4000`** (limitar el copiado a un máximo estable de 4 MB/s) a los comandos `rsync` reales (líneas 187 y 235). Esto mantiene el consumo eléctrico y la temperatura de los integrados dentro de límites seguros.

---

## 4. Instrucciones de Despliegue en la TV Box

1.  **Limitar el CPU Governor a Ahorro de Energía (powersave):**
    Antes de instalar, fuerza a la CPU a trabajar en su frecuencia mínima para evitar picos de corriente:
    ```bash
    echo "powersave" | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
    ```
2.  **Copiar el Script Parcheado a la TV Box:**
    Copia el archivo `armbian-install.patched` (incluido en este directorio) a la ruta de ejecutables de la TV Box:
    ```bash
    sudo cp armbian-install.patched /usr/sbin/armbian-install
    sudo chmod +x /usr/sbin/armbian-install
    ```
3.  **Ejecutar la Instalación:**
    Lanza de nuevo el instalador. La barra de progreso subirá lentamente pero sin caídas ni Kernel Panics:
    ```bash
    sudo armbian-install
    ```
