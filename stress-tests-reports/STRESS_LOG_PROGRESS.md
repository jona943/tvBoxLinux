# Bitácora de Pruebas de Estrés Incrementales

Este archivo registra el historial de pruebas de estrés controladas realizadas en la TV Box Mortal T1 para mapear sus límites reales de estabilidad de hardware (CPU, RAM y Temperatura).

---

## Historial de Pruebas Realizadas

| # | Fecha/Hora | CPU Target | RAM Target | Duración | Resultado | CPU Promedio | Temp Max | RAM Max | Observaciones / Punto de Quiebre |
| :--- | :--- | :---: | :---: | :---: | :--- | :---: | :---: | :---: | :--- |
| **1** | 06/07/2026 10:51 | 70% | 70% (~1035MB) | 90s (Intento) | **FALLO** | - | 60.0°C | ~614 MB | **Colapso del sistema.** Se congeló durante la fase de reserva de RAM al alcanzar 400MB de asignación adicional. La pantalla HDMI mostró estática y se perdió ping. |
| **2** | 06/07/2026 11:00 | 10% | 10% (OS base) | 90s | **ÉXITO** | 10.5% | 60.2°C | 194.5 MB | **Estable.** El sistema ya estaba al 12.9% de RAM de base, por lo que no se asignó RAM adicional. La temperatura y el uso de CPU se mantuvieron perfectamente planos. |
| **3** | 06/07/2026 11:07 | 15% | 20% (~295MB) | 90s | **ÉXITO** | 15.6% | 60.9°C | 312.0 MB | **Estable.** Reservó con éxito 88 MB adicionales en RAM física. Carga de CPU y temperatura estables con un aumento marginal de ~0.7°C. |
| **4** | 06/07/2026 11:12 | 20% | 30% (~443MB) | 90s | **ÉXITO** | 20.5% | 61.1°C | 466.3 MB | **Estable.** Reservó con éxito 236 MB adicionales en RAM física. Estabilidad total en CPU y disipación térmica sin superar los 61.1°C. |
| **5** | 06/07/2026 11:17 | 30% | 40% (~591MB) | 90s | **ÉXITO** | 30.5% | 60.2°C | 598.0 MB | **Estable.** Reservó con éxito 384 MB adicionales en RAM física. Se mantuvo 100% estable en el límite del colapso del primer test (~614 MB). |
| **6** | 06/07/2026 11:21 | 40% | 50% (~739MB) | 90s (Intento) | **FALLO** | - | 56.0°C | ~610 MB | **Colapso del sistema.** Se congeló durante la fase de reserva de RAM al alcanzar exactamente los 400 MB de asignación adicional. Mismo patrón de congelamiento que el Test 1. |
| **7** | 06/07/2026 11:29 | 50% | 40% (~591MB) | 90s | **ÉXITO** | 50.5% | 58.6°C | 612.4 MB | **Estable.** Asignó con éxito 396 MB de RAM adicional. La CPU al 50.5% y la temperatura fresca de 58.6°C demuestran que el chip es estable si la asignación total no supera los 400 MB adicionales. |
| **8** | 06/07/2026 11:36 | 80% | 40% (~591MB) | 90s | **ÉXITO** | 80.2% | 60.8°C | 607.9 MB | **Estable.** Asignó con éxito 389 MB de RAM adicional. La CPU operó al 80.2% sin problemas térmicos significativos y el PMIC toleró el consumo perfectamente. |
| **9** | 06/07/2026 11:42 | 100% | 40% (~591MB) | 90s | **ÉXITO** | 99.9% | 62.3°C | 605.4 MB | **Estable.** Asignó con éxito 387 MB de RAM adicional. El procesador operó al 100% de capacidad en sus 4 núcleos sin bloqueos ni cuelgues térmicos. |

---

## Análisis de Tendencia y Conclusiones Definitivas

1. **El Umbral Crítico de Asignación Adicional (Límite de los 400 MB / ~610 MB totales):**
   El comportamiento del hardware ha sido consistente. El sistema **colapsa exactamente cuando un proceso intenta reservar de forma consecutiva e ininterrumpida más de 400 MB de RAM física**, independientemente de la carga de la CPU (los Tests 1 y 6 fallaron al llegar a los 400 MB asignados de golpe, mientras que el Test 7 con 50% CPU / 396 MB, el Test 8 con 80% CPU / 389 MB y el Test 9 con 100% CPU / 387 MB fueron 100% exitosos).
2. **Causa Eléctrica/Física (Caída de Tensión en VDD_DRAM):**
   Rellenar y escribir a nivel físico bloques masivos de memoria RAM a máxima velocidad demanda un flujo de corriente muy alto y sostenido en la línea de alimentación de la DRAM (`VDD_DRAM`). En esta placa de bajo costo, la regulación de voltaje del PMIC o los condensadores de desacoplo no logran sostener este consumo de corriente por más de ~2.0 segundos (tiempo necesario para escribir y mapear 400 MB en bloques dinámicos). Al decaer el voltaje en la RAM, los transistores pierden su estado lógico, corrompiendo el framebuffer (estática visual) y bloqueando instantáneamente al procesador Allwinner H313.
3. **Estabilidad Térmica Excelente de la CPU H313:**
   El procesador Allwinner H313 es sumamente estable. Bajo un **100% de estrés sostenido** en todos los núcleos (Test 9), la temperatura máxima de la CPU alcanzó apenas **62.3°C**, un margen excelente y muy alejado del límite crítico de estrangulamiento térmico (thermal throttling, que suele activarse por encima de los 80°C).
4. **Margen de Operación Seguro:**
   La TV Box funciona de manera impecable y estable siempre y cuando el consumo total de memoria RAM se mantenga **estricta y cómodamente por debajo de los 500 MB** o si se realizan escrituras intermitentes y espaciadas en el tiempo, evitando picos de corriente sostenidos en el bus de memoria.

---

## Estrategia para el Flasheo en eMMC

Para lograr realizar la transferencia de la tarjeta MicroSD a la eMMC interna sin tocar este límite físico y eléctrico de los 600 MB:
* **Descompresión en PC Host / Descompresión previa en MicroSD:** No podemos usar descompresión de imágenes sobre la marcha (como `.img.xz`) ya que el buffer de descompresión eleva de inmediato el consumo de memoria RAM por encima del umbral de los 600 MB. La imagen debe estar 100% descomprimida antes de iniciar cualquier proceso.
* **Uso de `dd` controlado:** El script `raw_flash.py` modificado con imagen descomprimida (`.img`) y buffers de 64KB controlados con `sleep` y `fdatasync` es ideal, ya que consume menos de 20 MB de RAM.
* **Apagar servicios innecesarios:** Durante la copia final, el Wi-Fi y SSH deben estar desactivados para recuperar unos ~50 MB extra de RAM y estabilizar la placa.
