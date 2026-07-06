# Reporte de Prueba de Estrés y Diagnóstico de Colapso (RAM DRAM)

Este documento registra los detalles y conclusiones de la prueba de estrés controlada realizada el **Lunes 06 de Julio de 2026** en la TV Box Mortal T1 (SoC Allwinner H313, 1.5GB RAM).

---

## 1. El Experimento (Prueba Controlada)

* **Objetivo:** Forzar un uso sostenido y controlado de la memoria RAM al **70% (~1035 MB)** y de la CPU al **70%** para aislar variables térmicas y eléctricas y determinar el punto de quiebre del sistema.
* **Metodología:** 
  1. Ejecución del script `stress_test.py` desarrollado específicamente para evitar picos abruptos de I/O.
  2. Asignación secuencial de memoria RAM en bloques de **10 MB** (llenados con datos de prueba `\x01` para asegurar que el Kernel los asigne físicamente en la DRAM y no queden como asignaciones virtuales).
  3. Monitoreo en tiempo real de temperatura, uso de CPU y RAM cada 5 segundos.

---

## 2. Cronología del Fallo

Al iniciar el script con un objetivo de 90 segundos de duración, el sistema reportó las siguientes métricas iniciales:
* **Memoria RAM Total del Sistema:** 1478.8 MB (1.44 GB utilizables).
* **Uso Base del Sistema Operativo:** 214.6 MB.
* **Objetivo de Uso (70%):** 1035.2 MB.
* **Cantidad a Asignar en la Prueba:** 820 MB.

El script comenzó la asignación secuencial y reportó:
```
Allocated 100 MB...
Allocated 200 MB...
Allocated 300 MB...
Allocated 400 MB...
[BLOQUEO COMPLETO DEL SISTEMA / PING INACCESIBLE]
```

### Síntomas detectados:
1. El script dejó de reportar progreso exactamente después de alojar **400 MB** adicionales.
2. El uso total de RAM en el momento del colapso fue de **~614 MB** (214 MB base + 400 MB asignados).
3. Se perdió de inmediato la conexión SSH y la TV Box dejó de responder por completo al ping.
4. La pantalla HDMI mostró el congelamiento visual de inmediato.

---

## 3. Conclusiones del Diagnóstico (Raíz del Problema)

### A. La CPU no fue la causante (Colapso por I/O RAM Puro)
El colapso del sistema ocurrió **durante la fase inicial de reserva de RAM**, mucho antes de que se iniciaran los procesos trabajadores de la CPU (los cores estaban en reposo, en un 2% de uso, y la temperatura estaba estable a 60°C). Esto descarta de forma contundente problemas de sobrecalentamiento de la CPU o fallos del regulador de voltaje de la CPU en esta prueba.

### B. Inestabilidad de timings DRAM / Frecuencia de Memoria
El hecho de que el sistema colapse de forma inmediata al poblar secuencialmente **614 MB de RAM** (apenas el 41% de la capacidad física de la memoria del sistema) confirma que **la controladora de memoria RAM (DRAM) o los chips físicos de memoria LPDDR3 son inestables**. 
Esta inestabilidad ocurre bajo cargas de escritura en memoria constantes. Al rellenar la RAM a gran velocidad con bloques de datos, la controladora DRAM pierde sincronía de timings (típicamente debido a una configuración de timings demasiado agresiva en el U-Boot de arranque o frecuencias DRAM mal calibradas de fábrica para esta placa de bajo costo).

### C. Por qué esto afecta al flasheo (rsync / dd / raw_flash)
El flasheo de un sistema operativo requiere:
1. Leer la imagen comprimida desde la MicroSD a la RAM.
2. Descomprimir los datos en la RAM (lo cual requiere múltiples allocations dinámicas y buffers de descompresión).
3. Transferir los datos descomprimidos desde la RAM hacia la controladora eMMC.

Si la controladora DRAM colapsa simplemente al poblar 400 MB de datos, cualquier proceso de flasheo pesado (como `rsync`, que genera miles de accesos aleatorios a memoria y acumula caché del sistema de archivos, o el flasheo de imágenes comprimidas en tiempo real) inevitablemente corromperá la RAM y colgará la TV Box.

---

## 4. Estrategia de Mitigación para el Flasheo en eMMC

Dado que no podemos modificar fácilmente los timings de la RAM sin recompilar el U-Boot (Secondary Program Loader), debemos adaptar nuestro método de flasheo para que trabaje **dentro de los límites de estabilidad de esta RAM**:

1. **Eliminar la descompresión en tiempo real:** Debemos descomprimir la imagen `.img.xz` a su estado raw `.img` directamente en la MicroSD *antes* de flashear. La descompresión es el proceso que más allocations y movimiento de páginas genera en la RAM.
2. **Reducir la velocidad del bus eMMC (Ya aplicado):** Mantener el parche del DTB a 25 MHz en el bootloader actual. Esto reduce la velocidad de transferencia DMA de datos hacia la eMMC, limitando el estrés concurrente del bus y de la RAM.
3. **Flujo Offline y Silencioso:** Realizar el flasheo de forma local, sin dongle Wi-Fi conectado (para reducir el ruido eléctrico en la placa) y sin transmisión SSH (reduciendo interrupciones de red en el kernel).
