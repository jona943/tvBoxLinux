# Auditoría de Salud y Rendimiento de la Memoria eMMC

Este documento registra las pruebas físicas de lectura, escritura y diagnóstico de salud realizadas sobre el chip de memoria eMMC interna de la TV Box.

---

## 1. Datos Generales de la Prueba
*   **Fecha:** Domingo, 05 de julio de 2026
*   **Hora local:** 14:52 (MST)
*   **Dispositivo analizado:** `/dev/mmcblk2` (eMMC interna de 8 GB)
*   **Partición de pruebas:** `/dev/mmcblk2p1` (formateada en `ext4`)

---

## 2. Resultados de las Pruebas de Rendimiento

Las pruebas se realizaron con el comando `dd` utilizando las banderas `direct` para saltarse la caché de la memoria RAM del sistema y medir la velocidad directa sobre los buses físicos:

| Métrica | Comando Ejecutado | Resultado de Velocidad | Tiempo de Copiado | Estado |
| :--- | :--- | :--- | :--- | :--- |
| **Escritura Directa** | `dd if=/dev/zero of=/mnt/emmc/testfile bs=1M count=100 oflag=direct` | **45.2 MB/s** | 2.31908 s | **Excelente** |
| **Lectura Directa** | `dd if=/mnt/emmc/testfile of=/dev/null bs=1M count=100 iflag=direct` | **84.0 MB/s** | 1.24774 s | **Excelente** |

*Nota: Una velocidad de escritura de ~45 MB/s y lectura de ~84 MB/s es un rendimiento muy alto y saludable para un controlador de bus SDIO/MMC en un procesador Allwinner H313.*

---

## 3. Diagnóstico de Salud de Silicio (Reporte de Controladora)

Se leyeron los registros internos del bus MMC expuestos por el kernel de Linux:

1.  **Estado Pre-EOL (Fin de Vida Útil):**
    *   *Comando:* `cat /sys/class/block/mmcblk2/device/pre_eol_info`
    *   *Resultado:* **`0x01` (Normal / Saludable)**
    *   *Significado:* El controlador tiene bloques de reserva íntegros y no reporta fallos de sectores dañados inminentes.
2.  **Estimación de Vida Útil Consumida (SLC/MLC Life Time):**
    *   *Comando:* `cat /sys/class/block/mmcblk2/device/life_time`
    *   *Resultado:* **`0x08 0x08`**
    *   *Significado:* El chip de memoria interna ha consumido entre el **70% y el 80%** de su ciclo de vida estimado de fábrica.
    *   *Conclusión:* El desgaste es medio-alto (común en TV Boxes usadas debido a la escritura constante de logs y caché del sistema Android original), pero el chip aún se encuentra operativo, estable y con excelente rendimiento.
