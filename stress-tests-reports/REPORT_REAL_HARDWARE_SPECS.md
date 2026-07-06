# Reporte de Especificaciones Reales de Hardware (Auditoría Mortal T1)

Este documento contiene la conclusión definitiva sobre los componentes reales de hardware (almacenamiento, memoria RAM y GPU) de la TV Box Mortal T1 (X96Q Clone, SoC Allwinner H313), desenmascarando el firmware y las etiquetas comerciales falsas.

---

## 1. Almacenamiento (eMMC)

* **Especificación Comercial (Etiqueta/Caja):** **16 GB**
* **Capacidad Física Real (Soldada en placa):** **8 GB** (detectada como `/dev/mmcblk2`).
* **Espacio Útil para el Sistema Operativo:** **7.3 GiB** (el espacio restante se pierde en la conversión binaria de bloques y en la estructura de metadatos del sistema de archivos ext4).
* **Rendimiento Físico Directo:**
  * **Lectura Directa:** **84.0 MB/s** (Excelente velocidad para este bus).
  * **Escritura Directa:** **45.2 MB/s** (Muy buen rendimiento para ráfagas cortas).
* **Salud del Silicio:** El controlador reporta un consumo de vida útil del **70% - 80%** (común en dispositivos Android usados por el flujo constante de logs y caché). El estado de salud es normal y operativo para varios años, pero no tolera picos sostenidos de corriente de escritura sin control.

---

## 2. Memoria RAM (DRAM)

* **Especificación Comercial (Etiqueta/Caja):** **2 GB**
* **Especificación Reportada por Software (Kernel/htop):** **1.44 GB** (1478.8 MB).
* **Capacidad Física Real Estimada:** **1 GB físicos** (o en su defecto, **768 MB** configurados con chips asimétricos).
* **Explicación del Colapso (El "Engaño" del Firmware - Fake RAM):**
  1. El fabricante configuró el U-Boot (cargador de arranque) para reportar virtualmente **1.5 GB** al Kernel de Linux para maquillar las especificaciones.
  2. Físicamente, la placa de circuito integrado solo cuenta con **1 GB** (o menos) de chips DRAM soldados.
  3. Adicionalmente, el sistema reserva una parte de la RAM física para la GPU y el motor de video (Display Engine), reduciendo aún más el espacio direccionable real del sistema operativo.
  4. **El Límite de los ~600 MB:** El Kernel de Linux maps secuencialmente la memoria. Mientras operamos por debajo de los **598 MB**, todo el direccionamiento de memoria ocurre dentro de los chips de silicio físicos reales. En el instante en que el sistema operativo intenta cruzar la barrera de los **610 MB - 614 MB**, el Kernel intenta escribir en direcciones de memoria que **físicamente no existen en la placa**. Esto provoca un error de bus crítico inmediato (Data Abort) o un wrap-around (sobreescritura de sectores bajos), congelando instantáneamente el SoC y corrompiendo el framebuffer (estática visual en pantalla).

---

## 3. Procesador Gráfico (GPU)

* **Especificación Física:** **ARM Mali-G31 MP2** (de arquitectura Bifrost, integrada en el SoC Allwinner H313).
* **Memoria de Video (VRAM):** **0 MB dedicados**.
* **Funcionamiento:** Es una GPU de memoria compartida (Shared Memory Architecture). Utiliza la memoria RAM principal del sistema para almacenar texturas y framebuffers.
* **Reserva de Memoria (Carveout):** El Device Tree (DTB) y el Kernel reservan automáticamente una porción fija de la RAM del sistema (usualmente entre **64 MB y 256 MB** como memoria reservada DMA) para la GPU y el Display Engine. Esta porción queda completamente fuera del control de las aplicaciones del usuario.
* **Aceleración Gráfica bajo Linux:** La GPU Mali-G31 es compatible con OpenGL ES 3.2 y Vulkan 1.1 mediante el controlador de código abierto **Panfrost** en kernels modernos (como el 6.12.64 que estamos usando). Sin embargo, el entorno gráfico de escritorio (MATE) intentó usar aceleración de software o llamadas no optimizadas durante las primeras instalaciones, lo que sumado a la inestabilidad de la RAM provocó las pantallas negras iniciales.

---

## 4. Resumen Ejecutivo de Capacidades Reales

| Componente | Anunciado (Caja) | Reportado por OS | Capacidad Real Física | Límite Seguro de Operación |
| :--- | :---: | :---: | :---: | :--- |
| **CPU** | 4 Cores 1.5 GHz | 4 Cores 1.0 GHz | 4 Cores Cortex-A53 | **100% de uso estable** (máx. 62.3°C) |
| **RAM** | 2 GB | 1.44 GB | 1 GB (o 768 MB) | **Menos de 500 MB** de uso total |
| **eMMC (Disco)** | 16 GB | 7.3 GB | 8 GB | **Flasheo secuencial controlado (2MB/s)** |
| **GPU** | Mali-G31 | Compartida | Mali-G31 MP2 (Shared) | **Modo Consola (sin interfaz gráfica)** |
