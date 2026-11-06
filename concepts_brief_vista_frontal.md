# Vista de jugador (tecla V)

* **Author:** miroagustin
* **Date:** 2026-11-06

## Overview

La webcam de la notebook mira al jugador desde el otro lado del tablero, con un ángulo bajo. El jugador rojo se sienta en la celda 19. En pantalla pasan tres cosas:

- su lado (celdas 17–20) aparece arriba;
- si mueve la mano hacia la notebook, en pantalla la mano baja;
- sus celdas, que son las más lejanas a la cámara, se ven aplastadas.

Por eso se confunde al elegir celdas con la mano mirando la pantalla. La tecla F (espejo) solo invierte izquierda y derecha.

La propuesta: una tecla V en el navegador que cambia a una **vista de jugador**. Una cámara virtual inclinada se ubica detrás del lado del jugador y mira el tablero:

- el video de fondo se corrige con la homografía del plano del tablero, que sale de la pose y la K que ya existen;
- las criaturas, el click, el anillo de carga y el debug se dibujan con esa misma cámara virtual.

Es solo un cambio visual. La selección de celda con la mano la hace Python en píxeles de la cámara real ([dejarik/hands.py:174-180](dejarik/hands.py#L174-L180)), así que no cambia. Tampoco cambian el protocolo ni `config.toml`.

## Analysis

### Lo que no se sostiene

**Girar la imagen 180° con CSS no alcanza.** Corrige las direcciones (adelante pasa a ser arriba y derecha queda a la derecha). Pero `#stage` también contiene el canvas WebGL, así que las criaturas quedan cabeza abajo. Girar solo el video desalinea el video del 3D. Mostrar el lado rojo abajo con las criaturas paradas exige otro punto de vista: render nuevo más warp. Sirve como experimento de 30 minutos para ver si con direcciones coherentes ya alcanza. No sirve para la demo.

**"El color de quien está en pantalla" no tiene una fuente confiable.** En modo `local`, el host siempre recibe `you = 0` (azul) ([dejarik/transport.py:145](dejarik/transport.py#L145)), aunque quien está sentado en la 19 sea rojo. Además P reenvía `hello`, y la vista se daría vuelta en plena demo. `you` solo es correcto en modo cpu.

**Alternativa más simple: usar la geometría.** Quien mira la pantalla está sentado frente a la cámara de la notebook, juegue con el color que juegue. La posición de la cámara real en el tablero sale de la pose (`C = -Rᵀt`). La cámara virtual va del lado opuesto, con azimut igual al de la cámara real + 180°. Así se eliminan las listas de colores y la regla de "no girar cada turno". Rojo (celdas a 120–210°) y azul (300–30°) están exactamente enfrentados.

**CSS `matrix3d` no sirve para el warp.** Deformaría las criaturas como si fueran planas. Hay que hacerlo en WebGL: un disco dentro de `board` cuyo shader toma, para cada punto del tablero, el píxel correspondiente del video real.

### Riesgos

- **La mano se ve "derretida".** La punta del dedo está apoyada en el papel, o sea en el plano, así que queda exactamente sobre la celda que elige Python. La confusión no vuelve. Pero el brazo y la mano están por encima del plano y se estiran a lo largo de los rayos de la cámara real. Con la cámara a unos 20° de elevación, una mano a 10 cm de altura se estira unos 27 cm, más que el radio del tablero, y justo hacia el jugador. Se puede probar antes de escribir código: grabar un clip y deformarlo offline con `cv2.warpPerspective`.
- **Se ve borroso justo donde mira el jugador.** Las celdas 17–20 son las más aplastadas en la imagen original, así que el warp las amplía más que al resto. El warp agranda píxeles pero no agrega información. El lado cercano a la cámara puede quedar fuera de cuadro (negro).
- **El temblor de la pose sacude todo el video**, no solo las criaturas. Conviene usar la pose bloqueada (L). Falta definir qué pasa antes de la primera pose y cuando se pierde el tracking.
- **Al apagar V no se restaura la proyección.** `setProjection` solo se vuelve a ejecutar cuando cambian K o el tamaño ([web/scene.js:113](web/scene.js#L113)).
- **Hay código que tiene que seguir usando la cámara real.** `passThrough` ([web/main.js:121-133](web/main.js#L121-L133)) compara `hand.box`, que está en píxeles reales, con `toPx`. Si usa la cámara virtual, desvanece las criaturas equivocadas sin dar ningún error. Los esquinas y la mano del debug también están en píxeles reales. Hacen falta dos proyecciones con nombre: `real` y `display`.
- **F y V juntos no están definidos.** Un F guardado en `localStorage` invertiría izquierda y derecha sin que nadie lo note.
- **Los documentos contradicen el problema.** El diseño supone una webcam externa en trípode ([docs/designs/dejarik_ar.md](docs/designs/dejarik_ar.md)). [docs/demo_script.md](docs/demo_script.md) describe una demo por Teams con el host jugando azul. La meta G3 de [docs/designs/hand_interaction.md](docs/designs/hand_interaction.md) dice "el jugador mira su dedo, no la pantalla", que es lo opuesto a lo que plantea esta función.
- **Costo:** 1–2 días con debug, `passThrough` y pruebas. Después, cada cambio de render hay que verificarlo con las dos cámaras.

### Opciones, de más barata a más cara

1. **Cambio físico, sin código.** Poner la webcam del trípode del lado del jugador, por encima del hombro a unos 45°, o subir la cámara. Corrige dirección, aplastamiento y borroso en el origen, y además mejora la precisión del dedo. Riesgo: MediaPipe ve el dorso de la mano. Se prueba junto con la prueba G1 "desde cada lado de la mesa".
2. **CSS 180°**, solo como experimento.
3. **Minimapa 2D visto desde el lado del jugador** (60–80 líneas de canvas). `hand.cell`, las jugadas legales y las piezas ya están en el cliente. No hay borroso ni mano derretida, y la vista RA queda igual. Duda: si cuenta como RA para la cátedra.
4. **Cámara virtual cenital** en lugar de inclinada: menos estiramiento y más fácil de encuadrar, pero las criaturas se ven desde arriba.
5. **Vista de jugador V con homografía**, solo si la prueba offline del warp se ve aceptable.

## Goals vs. Non-Goals

* **In-Scope Goals:**
  * Con V activa, las celdas 17–20 quedan en la mitad de abajo de la pantalla, y mover la mano hacia la notebook mueve el resaltado hacia arriba.
  * Las criaturas se ven paradas, alineadas con los anillos impresos (±5 px).
  * El click en el centro de cada celda elige esa celda.
  * Al apagar V se vuelve exactamente a la vista de hoy. El estado se guarda en `localStorage`.
  * P no cambia el lado de la vista.
  * Los fps no bajan más de 10%.
* **Out-of-Scope Non-Goals:**
  * Cambios en Python, el protocolo o `config.toml`.
  * El cliente remoto.
  * El video fuera del tablero (se pinta de negro).
  * Inclinación configurable desde la interfaz.
  * Animación de transición.
  * Corregir la distorsión de lente en el warp (Python sí la corrige; esa diferencia ya existe hoy).

## Alternatives Weighed

* **Girar la imagen 180° con CSS como solución final.** Descartada en la revisión: deja las criaturas cabeza abajo. Queda solo como experimento para ver si las direcciones coherentes alcanzan.
* **Deformar `#stage` con CSS `matrix3d`.** Descartada en la revisión: deforma las criaturas 3D como si fueran planas.
* **Tomar el lado de la vista de `hello.you`.** Descartada en la revisión: en modo `local` el host siempre es azul, y P lo cambia en plena demo.
* **Que la vista siga al turno.** Descartada por el autor: contra la IA giraría la pantalla en cada turno.
* **Vista cenital.** No se eligió (el autor prefirió una vista inclinada): las criaturas pierden impacto. Sigue como opción si el estiramiento de la mano es muy grande.

## Key Decisions & Staging for Next Steps

Ya decidido:

- Es solo visual, una tecla en el navegador como F y M, sin tocar Python.
- La vista es inclinada, desde el lado de quien está frente a la pantalla, y no gira con el turno.
- El remoto y el fondo fuera del tablero no importan.

Pendiente, en este orden:

1. **Antes de escribir código:**
   - Definir el montaje real de la demo: ¿webcam de la notebook proyectada en vivo, o trípode por Teams? ¿Qué modo se usa (cpu, local o remoto)?
   - Probar la cámara del trípode detrás del jugador. Si así se resuelve, la función no hace falta.
2. **Prueba offline del warp** sobre un clip grabado, para ver cuánto se estira la mano.
3. **Si V sigue haciendo falta:**
   - Lado por geometría (azimut de la cámara real + 180°).
   - V apaga F.
   - Usar la pose bloqueada; sin pose, V no hace nada y muestra un aviso.
   - Dos proyecciones: `real` para `passThrough` y los datos de la mano, `display` para el click, el anillo y el debug.
   - Inclinación y FOV como constantes en [web/scene.js](web/scene.js), al lado de `BACKGROUND_DIM`. Distancia aproximada: 0,37 m con FOV de 40°.
4. **Prueba:** una página `?viewcheck` al estilo de `?soundcheck`, corrida sobre `--replay fixtures/session_01.dj`. Verifica que `boardPointFromClick(project(cellCenter(c))) ≈ cellCenter(c)` con un error menor a 2 mm para las 25 celdas y las dos vistas.
5. **Documentos:**
   - Agregar V a [README.md](README.md) y a [docs/designs/dejarik_ar.md](docs/designs/dejarik_ar.md).
   - Actualizar la meta G3.
   - Corregir las contradicciones de [docs/demo_script.md](docs/demo_script.md).
