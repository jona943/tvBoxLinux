# Bitácora Experimental: Límite Máximo de Capacidad de RAM (Allwinner H313 - Mortal T1)

Este documento registra las pruebas incrementales de capacidad de memoria RAM (`mem=`) realizadas en vivo para determinar el punto exacto de quiebre y la capacidad máxima estable en el hardware real del dispositivo.

---

## 📋 Registro Incremental de Experimentos

| # | Configuración `mem=` | `MemTotal` Útil | Asignación Pico (MB) | Uso % Máximo | Duración | Temp. CPU | Resultado | Notas |
|:-:|:--------------------:|:---------------:|:--------------------:|:------------:|:--------:|:---------:|:---------:|:------|
| 1 | `mem=512M` | 476 MB | 440 MB | 92.4% | 180s | 65 °C | **ÉXITO (100% Estable)** | Límite base ultra seguro. Sin colapsos. |
| 2 | `mem=520M` | 482 MB | 420 MB | 87.1% | 40s | 61 °C | **ÉXITO (100% Estable)** | Funciona perfecto. 0 Panics. |
| 3 | `mem=550M` | 512 MB | 439 MB | 85.7% | 40s | 55 °C | **ÉXITO (100% Estable)** | Excelente temperatura. Operación fluida. |
| 4 | `mem=580M` | 541 MB | 479 MB | 88.5% | 40s | 55 °C | **ÉXITO (100% Estable)** | 541 MB útiles de RAM. Cero errores. |
| 5 | `mem=600M` | 561 MB | 509 MB | 90.7% | 40s | 56 °C | **ÉXITO (100% Estable)** | 561 MB útiles logrados. Operación limpia. |
| 6 | `mem=605M` | 566 MB | 529 MB | 93.5% | 40s | 55.5 °C | **ÉXITO (100% Estable)** | 566 MB útiles logrados. Operación perfecta. |
| 7 | `mem=610M` | 571 MB | 541 MB | 94.7% | 40s | 55.5 °C | **ÉXITO (100% Estable)** | 571 MB útiles logrados. 94.7% sostenido. |
| 8 | `mem=615M` | 576 MB | 514 MB | 89.2% | 40s | 56.5 °C | **ÉXITO (100% Estable)** | 576 MB útiles logrados. Operación fluida. |
| 9 | `mem=630M` | 591 MB | 545 MB | 92.2% | 40s | 57.0 °C | **ÉXITO (100% Estable)** | 591 MB útiles logrados. Estabilidad total. |
| 10 | `mem=650M` | 609 MB | 574 MB | 94.3% | 40s | 57.3 °C | **ÉXITO (100% Estable)** | 609 MB de RAM Útil superados. |
| 11 | `mem=675M` | 634 MB | 575 MB | 90.7% | 40s | 56.5 °C | **ÉXITO (100% Estable)** | 634 MB de RAM Útil superados. |
| 12 | `mem=700M` | 658 MB | 627 MB | 95.3% | 40s | 57.4 °C | **ÉXITO (100% Estable)** | 658 MB de RAM Útil superados. |
| 13 | `mem=750M` | 708 MB | 663 MB | 93.6% | 40s | 58.2 °C | **ÉXITO (100% Estable)** | 708 MB de RAM Útil superados. |
| 14 | `mem=760M` | 718 MB | 670 MB | 93.3% | 40s | 56.8 °C | **🏆 ÉXITO (CONFIGURACIÓN PRODUCCIÓN)** | **718 MB Útiles de RAM.** Súper fluido y estable para Mini Servidor. |
| 15 | `mem=768M` | 726 MB | 672 MB | 92.6% | 40s | 52.1 °C | **ÉXITO (Límite Físico Teórico)** | Máxima capacidad utilizable del chip. |
| 16 | `mem=800M` | N/A | N/A | N/A | 0s | N/A | **🔴 COLAPSO (Punto de Quiebre)** | Fallo de arranque. Inestabilidad de bus DRAM. |

---

## 🏆 Conclusión Final y Configuración Recomendada de Producción

1. **Configuración Selección de Producción:** **`mem=760M`**
   * **Memoria Utilizable:** **718 MB libres para el sistema operativo**.
   * **Consumo Base (Servidor CLI):** **~130 MB** (Dejando casi **~590 MB libres** para contenedores Docker, microservicios, bases de datos o servicios web).
   * **Estabilidad Térmica:** **55 °C - 58 °C** operando de forma continua.
2. **Arranque Autónomo:** Instalación 100% nativa en la eMMC interna (`/dev/mmcblk2p1`) sin requerir tarjeta MicroSD externa.
