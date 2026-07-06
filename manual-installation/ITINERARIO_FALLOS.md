# Itinerario de Fallos y Diagnóstico de Bloqueos

Este documento registra cronológicamente cada uno de los congelamientos y fallos del sistema durante el proceso de instalación en la eMMC de la TV Box Mortal T1, detallando las condiciones del hardware, síntomas y las hipótesis analizadas.

---

## Historial Cronológico de Fallos

### Fallo 1: Congelamiento Inmediato al 1% (Imagen Desktop - Kernel 6.6.44)
*   **Condiciones:** Ejecutando `armbian-install` oficial. Imagen con entorno gráfico MATE. Antena Wi-Fi conectada. Teclado mecánico retroiluminado conectado.
*   **Síntoma:** El sistema se congelaba inmediatamente al alcanzar el 1% del copiado de archivos.
*   **Hipótesis:** El conteo inicial de archivos por `rsync --stats` síncrono y la velocidad libre de copiado saturaban el bus de I/O, generando un pico de calor y consumo eléctrico que el cargador de 5V 2A no podía suministrar.

### Fallo 2: Pantalla Negra en Arranque (Primer Boot tras re-flasheo MATE)
*   **Condiciones:** Primer arranque tras re-flasheo de la tarjeta.
*   **Síntoma:** Pantalla HDMI negra con cursor estático después del asistente de creación de usuario. Teclado sin responder.
*   **Hipótesis:** LightDM / X11 intentando arrancar aceleración gráfica no compatible con el SoC H313 sin la asignación explícita del DTB adecuado (`sun50i-h313-x96q-lpddr3.dtb`).
*   **Solución:** Modificación de `armbianEnv.txt` para forzar modo consola (`systemd.unit=multi-user.target`) y forzar el DTB correcto.

### Fallo 3: Initramfs "No Init Found" (Tras re-flasheo de Minimal - Kernel 6.12.64)
*   **Condiciones:** Primer boot de la nueva imagen Minimal.
*   **Síntoma:** El sistema caía a la consola de recuperación BusyBox `(initramfs)` indicando que no encontraba `/sbin/init` en el dispositivo de arranque.
*   **Diagnóstico:** El U-Boot del eMMC interno arrancaba primero y leía su configuración antigua. Intentaba montar como root la partición de la eMMC (`mmcblk2p1` de 7.3G), la cual tenía una instalación corrupta e incompleta (solo 3,727 archivos) producto del corte del Fallo 1.
*   **Solución:** Forzar el arranque directo desde la MicroSD manteniendo presionado el botón de Reset físico en el conector AV durante 10 segundos al conectar la energía.

### Fallo 4: Congelamiento a medias en copiado manual (rsync verbose)
*   **Condiciones:** Corriendo `rsync -avx` manual con límite de 1.5 MB/s. Antena Wi-Fi USB activa. Sesión SSH activa.
*   **Síntoma:** El copiado se congeló a la mitad (en la línea 2085, copiando librerías en `/usr/lib/`).
*   **Diagnóstico:** El modo verbose (`-v`) forzaba a la terminal SSH a transmitir miles de líneas de texto a través del Wi-Fi en tiempo real. La transmisión de radio RF constante del dongle USB Wi-Fi sumada al consumo de escritura de la eMMC saturó la alimentación del bus USB, provocando una caída de voltaje de la CPU.

### Fallo 5: Congelamiento local (rsync silencioso a 1.0 MB/s con DTB 50MHz)
*   **Condiciones:** Corriendo `rsync -aqx` (silencioso) a 1.0 MB/s. Antena Wi-Fi desconectada físicamente. Teclado mecánico retroiluminado desconectado. DTB modificado en la MicroSD para desactivar modos eMMC de alta velocidad (HS200/HS400) limitando el bus a 50 MHz.
*   **Síntoma:** Se congeló nuevamente a los pocos minutos de iniciar el copiado local en la pantalla HDMI (el cursor LED pasó de azul a rojo indicando apagado por protección del PMIC).
*   **Diagnóstico:** Descartado el consumo de la antena Wi-Fi, teclado y velocidad del bus de la eMMC. El congelamiento bajo I/O constante se mantiene incluso en las condiciones más favorables de energía.

### Fallo 6: Congelamiento al copiar a USB Externo (sda)
*   **Condiciones:** Corriendo `sudo ./instalar_usb.sh` apuntando a un disco USB externo de 60 GB (`/dev/sda`). Modo Eco activado (3 de los 4 núcleos del procesador apagados, único núcleo activo limitado a 480 MHz).
*   **Síntoma:** Congelamiento inmediato o temprano durante la preparación del USB.
*   **Diagnóstico:** Dado que el fallo se reproduce al escribir en un dispositivo USB externo, **se descarta de forma definitiva que el problema sea un fallo físico del chip eMMC interno de 8 GB**.
*   **Hipótesis Principal Actual:** El congelamiento se produce por una **inestabilidad general del kernel 6.12/6.6** o de los controladores de bus (MMC y USB) al realizar escrituras sostenidas en sistemas de archivos ext4, o bien debido a que el cargador de energía (cargador/cable) no soporta el incremento de corriente del SoC al realizar operaciones de I/O concurrentes (incluso con la CPU bajo consumo).

### Fallo 7: Congelamiento con Power Bank (eMMC y USB)
*   **Condiciones:** Alimentando la TV Box mediante una Power Bank (batería portátil) con cables de alta calidad.
*   **Síntoma:** El sistema sigue congelándose con el LED rojo durante operaciones de copia pesadas.
*   **Diagnóstico:** Al estar descartada la caída de tensión de la fuente de poder externa (la Power Bank suministra 5V estables), el problema se enfoca en una inestabilidad de la controladora de memoria RAM debido a timings/frecuencias DRAM inestables en el U-Boot.

### Fallo 8: Congelamiento casi inmediato en copiado con `tar` (Streaming)
*   **Condiciones:** Ejecutando `sudo ./instalar_emmc_tar.sh`. Copia con `tar --one-file-system`.
*   **Síntoma:** El bloqueo ocurrió mucho más rápido que con `rsync`.
*   **Diagnóstico:** `tar` realiza un pipeline de streaming puro (`tar | tar`), ejecutando de forma paralela la lectura masiva de la MicroSD y la escritura masiva en la eMMC. Esto maximiza la concurrencia de acceso DMA a la memoria RAM. El hecho de que colapse casi instantáneamente bajo este estrés máximo de I/O concurrente apunta de forma definitiva a un fallo de sincronización de la controladora RAM por timings incorrectos.

---

## Tabla Resumen de Diagnóstico Cruzado

| Prueba / Condición | Dispositivo Destino | Wi-Fi Activo | CPU Cores / Frecuencia | Resultado | Conclusión |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `dd` de 100MB (rápido) | eMMC (`mmcblk2`) | Sí | 4 Cores (Max Freq) | **ÉXITO** (45MB/s) | El chip eMMC puede escribir a alta velocidad en ráfagas cortas sin problemas de silicio. |
| `rsync` de 1.3GB (largo) | eMMC (`mmcblk2`) | Sí | 4 Cores (Max Freq) | **FALLO (1%)** | Saturación de corriente/temperatura combinando Wi-Fi + CPU + eMMC. |
| `rsync` de 1.3GB (largo) | eMMC (`mmcblk2`) | No | 1 Core (480 MHz) | **FALLO** | La inestabilidad persiste incluso reduciendo el consumo de CPU y quitando periféricos. |
| `rsync` de 1.3GB (largo) | USB (`sda`) | Sí | 1 Core (480 MHz) | **FALLO** | **Se descarta la eMMC.** El congelamiento es sistémico del bus I/O o de la fuente de poder principal. |
