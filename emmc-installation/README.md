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

## 3. Estrategia de Solución Implementada

Para resolver este cuello de botella y garantizar una instalación estable, modificamos el instalador aplicando dos parches en el script `/usr/sbin/armbian-install` y configurando límites de caché de escritura en el kernel:

### 1. Reemplazo del Conteo Pesado por Conteo Rápido de Metadatos
Eliminamos la línea del `rsync --stats` síncrono y la reemplazamos por un conteo instantáneo que solo lee metadatos en 2 segundos sin realizar copias físicas:
```bash
TODO=$(find / -xdev | wc -l)
```

### 2. Limitación de Caché de Escritura en el Kernel (En lugar de `-o sync`)
*Nota histórica: Inicialmente intentamos usar la opción de montaje `-o sync`, pero esto provocó un congelamiento/bloqueo de I/O debido a que el controlador de eMMC (`sunxi-mmc`) entra en timeout si el hardware tarda demasiado en confirmar cada bloque pequeño de escritura individual.*

En su lugar, mantenemos el montaje asíncrono estándar pero limitamos el tamaño de la caché de páginas sucias (*dirty pages*) en el kernel del sistema. Esto se hace ejecutando antes de la instalación:
```bash
# Iniciar vaciado de caché en segundo plano al alcanzar 4 MB
sudo sysctl -w vm.dirty_background_bytes=4194304
# Bloquear procesos de escritura si hay más de 8 MB pendientes de escribir
sudo sysctl -w vm.dirty_bytes=8388608
```
Esto asegura que el sistema nunca acumule más de 8 MB de datos sin escribir en RAM, evitando los picos destructivos de vaciado de caché (*write storms*) pero permitiendo que el hardware maneje las escrituras de forma agrupada y eficiente.

### 3. Límite del Ancho de Banda de Copiado (`--bwlimit`)
Agregamos el parámetro **`--bwlimit=1500`** (limitar el copiado a un máximo estable de 1.5 MB/s) a los comandos `rsync` reales (líneas 187 y 235). Esto mantiene el consumo eléctrico y la temperatura de los integrados dentro de límites seguros.

---

## 4. Instrucciones de Despliegue en la TV Box

1.  **Limitar el CPU Governor a Ahorro de Energía (powersave):**
    Antes de instalar, fuerza a la CPU a trabajar en su frecuencia mínima para evitar picos de corriente:
    ```bash
    echo "powersave" | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
    ```
2.  **Establecer los límites de caché de escritura (dirty page limits):**
    Configura al kernel para mantener un flujo de escritura pequeño y constante en lugar de ráfagas:
    ```bash
    sudo sysctl -w vm.dirty_background_bytes=4194304
    sudo sysctl -w vm.dirty_bytes=8388608
    ```
3.  **Copiar el Script Parcheado a la TV Box:**
    Copia el archivo `armbian-install.patched` (incluido en este directorio) a la ruta de ejecutables de la TV Box:
    ```bash
    sudo cp armbian-install.patched /usr/sbin/armbian-install
    sudo chmod +x /usr/sbin/armbian-install
    ```
4.  **Ejecutar la Instalación:**
    Lanza de nuevo el instalador:
    ```bash
    sudo armbian-install
    ```
