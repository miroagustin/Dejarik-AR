# Interacción con la mano: apuntar, confirmar y "atravesar" el holograma

* **Author:** miroagustin
* **Date:** 2026-11-06

## Overview

Hoy hay dos problemas con la mano:

1. **El 3D siempre se dibuja arriba del video.** Si agarrás una criatura desde arriba, en pantalla parece que la agarrás desde abajo.
2. **El pinch pulgar-índice se mide con la punta del dedo a 3-4 cm del papel.** Al proyectarla sobre el tablero cae 3-4 cm corrida, o sea en otra casilla.

En la película nadie toca los hologramas del dejarik: se elige y se ordena, y la mano pasa a través sin efecto. La hipótesis que propuso el usuario tiene cuatro partes:

1. La casilla es la punta del índice (landmark 8) apoyada en el papel, proyectada con la homografía que ya existe.
2. Para confirmar, se junta el dedo medio con el índice y se sostiene 1 s, con un anillo de carga en pantalla.
3. La mano tapa a las criaturas: una máscara de la mano escrita en el depth buffer.
4. Opcional: un parpadeo del holograma cuando la mano lo atraviesa.

Este brief junta lo que dijeron seis revisores (diseño, código, alcance, comprensión, preparación para implementar y estructura). La conclusión: **las partes 1 y 2 alcanzan para el problema 2. El problema 1 se resuelve más barato y más fiel a la película haciendo que la criatura "se deje atravesar"** (se pone transparente o parpadea), sin tocar el depth buffer. La oclusión real queda como mejora opcional para después, con fecha límite.

Faltan 20 días para la demo (26/11) y el congelamiento es el 20/11 (día 18 del plan en `concepts_brief.md`).

## Analysis

### Lo que ya está hecho (no hay que escribirlo)

- **La proyección del índice ya existe.** `hands_loop` proyecta `lm[8]` con `image_to_board` y `undistortPoints` (`dejarik/hands.py:41-47`, `:96`). Hay un test de ida y vuelta. Con el dedo apoyado en el papel desaparece el error "altura × tan(45°)" que describe `concepts_brief.md:157`. Lo único que cambia es la regla de uso: el dedo toca el papel.
- **`Pinch` sirve tal cual.** Recibe cualquier número y aplica histéresis y tiempo mínimo, y dispara una sola vez por gesto (`hands.py:17-38`). Llamar a `pinch.update(None, t)` ya lo resetea (`hands.py:31`), así que fijar la casilla y cancelar si el dedo se va de ella entra en `hands_loop` en unas 3 líneas:
  - guardar la casilla cuando `pinch.active` pasa de falso a verdadero;
  - resetear si cambia la casilla;
  - llamar a `on_tap(casilla_guardada)` en vez de `on_tap(cell)` (`hands.py:97-98`).
- **El progreso del anillo ya está calculado:** `(t - pinch.closed_since) / pinch.min_s`.
- **El flujo de juego no cambia.** El toque de la mano va por `on_host_tap → tap → game.apply(("tap", cell))`, el mismo camino que el clic del mouse (`dejarik/transport.py:251-264`). Si tocás una casilla no válida, se cancela la selección y no se juega nada raro (`dejarik/game.py:127-129`).
- **El resaltado de la casilla bajo el dedo ya existe** (`web/main.js:107`, `web/scene.js:135`). El overlay de debug ya dibuja un punto en `hand.px` (`web/debug.js:54-57`), así que el anillo se copia de ahí.
- **El holograma ya es transparente** (`web/hologram.js:18`, alfa 0,7-1) y tiene `uFlicker` (global) y `uFlash` (por material).
- **Ya existe un patrón de oclusor que solo escribe profundidad:** `colorWrite:false` y `renderOrder=-1` en `scene.js:54-58`, dibujado después de `clearDepth()` (`scene.js:159-160`). Si algún día se hace la oclusión, se reutiliza eso.

### Riesgos del gesto de confirmación (parte 2)

- **Confirmaciones sin querer.** Una mano relajada y apoyada ya tiene el índice y el medio juntos y estirados. **Decisión del autor:** se acepta el riesgo, porque en la demo las manos en reposo quedan fuera del cuadro. Lo que queda: si un jugador deja la mano apoyada sobre una casilla válida, la pieza se mueve en 1 s. El tiempo de 1 s y la casilla fijada lo hacen poco probable, pero no lo impiden. Se mide en el control.
- **A 45° la cámara no ve bien el dedo medio.** Desde el lado de enfrente, la punta del medio queda detrás del índice y MediaPipe adivina su posición. Desde el lado cercano, las dos puntas se alinean con la línea de visión y en 2D parecen juntas aunque no lo estén. Por eso conviene probarlo **por separado para cada lado**.
- **Los "centímetros" de `hand_world_landmarks` no son centímetros de verdad.** La escala la estima el modelo, así que un umbral fijo de 1,5 cm no significa mucho. Hay dos salidas: usar el ratio sin escala que ya se usa (`dist(8,12) / dist(0,9)`, como en `hands.py:92`), o tratar el 1,5 cm como una perilla a calibrar en el aula, no como una constante.
- **Rompe la config sin avisar.** `pinch_on/off` (`config.toml:37-38`) hoy son ratios sin unidad. Si se reusan las mismas claves con otra unidad, una config vieja carga sin error y da valores incorrectos.
- **Hoy `num_hands=1` y hay dos jugadores.** Como las manos en reposo quedan fuera del cuadro, se mantiene `num_hands=1`. Si en las pruebas aparecen dos manos a la vez, se revisa.

### Riesgos de "fijar la casilla y cancelar si te vas"

- **"Fijada" y "se cancela si salís" se contradicen** para quien juega por primera vez: si está fijada, ¿por qué se cancela? La frase correcta es: el objetivo queda fijo al empezar, y se cancela solo si el dedo se aleja más de X mm del centro de esa casilla.
- **El borde entre casillas va a parpadear.** Las casillas interiores miden unos 4 cm y las exteriores unos 7,8 cm, y la punta tiembla alrededor de 1 cm. Con comparar solo "¿es la misma casilla?", el gesto se cancela una y otra vez sin motivo visible. Hace falta una tolerancia (un radio o unos N cuadros), y lo mismo para el resaltado.

### Riesgos de la oclusión con depth buffer (parte 3)

- **La máscara va desfasada respecto del video.** El hilo de manos publica "para el próximo cuadro" (`hands.py:76`). El vision loop agarra el último resultado (`dejarik/vision.py:206`, `dejarik/__main__.py:99-110`), así que la máscara llega 1-2 cuadros tarde. Si movés la mano, ves la criatura deslizándose sobre el borde de la mano, que es justo el efecto que se quiere arreglar. Además rompe el principio de que la pose y el cuadro tengan el mismo `frame_id` (Bloqueante 1 del brief general).
- **Una sola profundidad (la del punto del índice) está mal a propósito.** A 45° los nudillos y el brazo están mucho más cerca de la cámara que la punta, y el hull de los 21 landmarks no incluye el brazo. Además el hull queda corto: los landmarks son centros de articulación, así que le faltan unos 8 mm por lado.
- **La segmentación no entra en el protocolo.** Una máscara de píxeles necesita un segundo payload binario. Eso rompe el formato `[uint32][header][JPEG]` (`dejarik/protocol.py:8-22`), los `.dj` y el fixture `fixtures/session_01.dj`. Un hull de 21 puntos sí entra en el header JSON.
- **En el modo remoto, `hand.px` ya está mal.** `encode_remote` escala K pero manda `hand` sin escalar (`vision.py:171-180`), y a una máscara le pasaría lo mismo.
- **Contradice el brief general.** `concepts_brief.md:328` pone "oclusión de los hologramas por la mano" como Non-Goal explícito, y la mano es lo primero que se recorta (decisión 6: el mouse es la entrada principal).

### Riesgos de experiencia de uso

- **El jugador mira su dedo, no la pantalla.** El anillo de 1 s y el resaltado están en el proyector. Si la mano tapa el 3D, además tapa la casilla resaltada. La solución: sonidos con el `web/audio.js` que ya existe (un tic al empezar, un acorde al confirmar, otro sonido al cancelar) y un anillo corrido hacia un costado.
- **El gesto tiene seis nombres.** Se le dice "pinch", "tap", "clic", "confirmar", "dos dedos" y "fijar" a la misma acción, y el `README.md:73` todavía dice pulgar e índice 0,3 s. Hay que elegir una frase que se pueda decir en voz alta, por ejemplo "apuntá y juntá dos dedos", y usarla en el HUD, el README y la explicación al público. Hoy `web/hud.js` no muestra ninguna pista.
- **El parpadeo se puede confundir con "Tracking perdido",** que ya tiene su propio fundido. Tiene que verse claramente distinto.
- **Al tocar el papel se tapan marcadores.** Con la cámara fija en el trípode y la pose congelada no pasa nada, pero hay que decirlo explícitamente.

### Huecos para probar sin cámara

- **El replay no tiene hilo de manos** (`dejarik/recording.py:37`, `:59` mandan `bgr: None`), así que hoy no se puede probar el gesto con grabaciones. Tampoco hay un `.dj` con una mano tocando casillas conocidas.
- **El overlay de debug muestra `pinch_ratio`** (`vision.py:207-210`, `web/debug.js:65`). Para calibrar el día de la demo tiene que mostrar:
  - la distancia 8-12;
  - si el medio está estirado;
  - el progreso del gesto;
  - la casilla fijada;
  - el motivo de la cancelación.
- **`NO_HAND` está duplicado** en `hands.py:14` y `vision.py:183`. Cada campo nuevo va en los dos lugares.

## Goals vs. Non-Goals

**Goals (para la demo)**

- Elegir la casilla con la punta del índice apoyada en el papel, con tolerancia en el borde. Criterio: 9 de 10 correctas por anillo, medido **por separado desde cada lado**.
- Confirmar sosteniendo 1 s, con anillo de carga y sonido. Criterio: ninguna confirmación falsa en 2 min de juego normal, desde cada lado.
- La criatura bajo el dedo "se deja atravesar": baja la opacidad a ~0,35 y parpadea más, con un fundido de ~150 ms. Así la mano del video se ve a través y se lee como "atraviesa", no como "está abajo". Esto cubre el problema 1 y las partes 4 y 3 de la hipótesis de la forma más barata.
- Una sola fuente para los umbrales: la sección `[hands]` de `config.toml`, con claves nuevas. El README y el brief la citan sin copiar números.
- El mouse queda como plan B (`--input both` / `--input mouse`) y el gesto viejo se puede elegir por config.

**Non-Goals**

- Estimar la altura de la mano (no hay solvePnP de la mano).
- Máscara por segmentación de píxeles.
- Oclusión con profundidad por lado en el punto del índice, salvo que se enmiende `concepts_brief.md:328` y se cumpla la Etapa 4 a tiempo.
- Gestos con dos manos.
- Que la mano tape en el remoto (el remoto no recibe máscara).
- Volver a usar el pinch pulgar-índice como gesto principal.

## Alternatives Weighed

| Tema | Opción | A favor | En contra | Veredicto |
|---|---|---|---|---|
| Casilla | Índice apoyado (lm 8) | Ya implementado y sin error de altura | Tapa marcadores (sin problema con pose congelada) | **Sí** |
| Casilla | Estimar la altura de la mano | Funcionaría con el dedo en el aire | Mucho trabajo, frágil | No |
| Confirmar | Medio junto al índice, en world landmarks (cm) | Intuitivo, "dos dedos" | Escala estimada, medio tapado a 45°, mano relajada lo dispara, hay que agregar código | Solo si los datos lo justifican |
| Confirmar | Medio junto al índice con ratio 2D `d(8,12)/d(0,9)` | Reusa `hands.py:92`, cambio de una línea, sin escala | Puede alinearse en 2D desde un lado | No: el autor pide 3D |
| Confirmar | Medio junto al índice con ratio **3D** `d(8,12)/d(0,9)` sobre `hand_world_landmarks`, más medio estirado | 3D (no se engaña por la perspectiva) y sin escala (no depende de los cm estimados) | El medio tapado a 45° sigue siendo una estimación del modelo | **Sí** |
| Confirmar | Exigir además anular y meñique doblados | Filtra la mano relajada | Rechazado por el autor: en la demo no hay manos en reposo en cuadro, y agrega otra condición que puede fallar | No |
| Confirmar | Solo quedarse quieto 1-1,2 s en la casilla, con anillo | Lo más simple, no hay segundo gesto | Un apoyo distraído sobre un destino válido mueve la pieza | **Plan B** si el gesto falla en los datos |
| Problema 1 | Criatura transparente o que parpadea bajo el dedo | Pocas líneas, sin cambiar el protocolo, fiel a la película | No es oclusión "de verdad" | **Sí (aceptado por el autor)** |
| Problema 1 | Hull dilatado que siempre tapa (profundidad cerca de la cámara) | Sin lógica por lado, usa el patrón de `scene.js:54-58` | Desfase de 1-2 cuadros, hay que sincronizar `frame_id` | Opcional (Etapa 4) |
| Problema 1 | Hull a la profundidad del punto del índice, por lado | Lo que pidió el usuario | Una sola profundidad está mal para nudillos y brazo, la depth salta cuando el dedo está en el aire | Solo si la Etapa 4 se ve mal |
| Problema 1 | Segmentación | Silueta real con el brazo | Otro modelo (+10-20 ms), payload binario, rompe los `.dj` | No |

## Key Decisions & Staging for Next Steps

**Decisiones abiertas (antes de programar)**

1. **Qué número mide el gesto. Decidido:** el ratio `d(8,12)/d(0,9)` calculado en 3D con `hand_world_landmarks`. No se exige anular ni meñique doblados. El umbral se calibra con histogramas de los 5 estudiantes, desde los dos lados.
2. **La fórmula de "medio estirado"** (por ejemplo, `|lm12-lm0| > k·|lm10-lm0|`), con un `k` por defecto y el umbral de soltar (histéresis).
3. **La regla de cancelación. Decidido:** un radio en mm desde el centro de la casilla fijada, no el borde de la casilla. Se suma un sonido al empezar, al confirmar y al cancelar.
4. **Qué mano cuenta con dos jugadores. Decidido:** `num_hands=1`; las manos en reposo quedan fuera del cuadro.
5. **Dónde está la cámara respecto de los dos jugadores.** Solo importa si se hace la Etapa 4.
6. **Claves nuevas en `[hands]`** (`gesture = "pinch"|"touch"`, `confirm_on`, `confirm_off`, `confirm_ms`, tolerancia), con un aviso si aparecen las claves viejas.

**Etapas (cada una se entrega y se prueba sola)**

- **E0 – Línea base, sin código.** Medir "9/10 por anillo" con el gesto actual y el overlay de debug, desde cada lado. Es la vara con la que se compara todo lo demás.
- **E1 – Gesto en Python.**
  - Pedir `hand_world_landmarks` además de `hand_landmarks`, calcular el ratio 3D `d(8,12)/d(0,9)` y agregar el chequeo de medio estirado.
  - `pinch_ms=1000`.
  - Fijar la casilla, resetear con tolerancia y llamar a `on_tap(casilla_fijada)`.
  - Mostrar en el debug la distancia, el progreso, la casilla fijada y el motivo de cancelación.
  - **Test:** una prueba de la máquina de estados con secuencias sintéticas `(ratio, casilla, t)`: dispara a 1 s, se cancela al salir, dispara una sola vez, se cancela si se pierde la mano. Mismo estilo que `tests/test_hands.py:9-19`.
- **E2 – Anillo y sonido.**
  - Campos que se agregan en `hand`: `hold` (0..1) y `lock_cell`. Se queda en VERSION=1. Hay que actualizar `NO_HAND` en los dos lugares, `docs/protocol.md` y `tests/test_protocol.py`.
  - Dibujar el anillo corrido de la casilla y sumar sonidos con `web/audio.js`: un tic al empezar, un acorde al confirmar y otro sonido al cancelar.
  - Agregar la pista del gesto en el HUD y corregir `README.md:73`.
- **E3 – "Se deja atravesar".** Opacidad y `uFlash` por criatura cuando su casilla es `hand.cell`, con fundido de ~150 ms y un look distinto al de "Tracking perdido".
- **Control (antes del 16-18/11, control 2 del plan general).** Medir E1-E3 contra E0. Si el gesto da confirmaciones falsas, pasar a quedarse quieto 1,2 s (plan B). Si no llega a 9/10, decidir mano contra puntero ArUco, como ya prevé el brief general.
- **E4 – Oclusión real (opcional, detrás de una tecla, apagada por defecto, solo si E1-E3 están cerradas antes del 18/11).**
  - Primero medir el desfase.
  - Agregar `frame_id` al dict de la mano.
  - Hull de 21 puntos en coordenadas normalizadas [0..1], dilatado, que siempre tapa.
  - Usar el patrón de `scene.js:54-58` con cuidado con el `flipY` (`scene.js:33`).
  - La profundidad por lado en el punto del índice solo si el hull que siempre tapa se ve mal. Requiere enmendar `concepts_brief.md:328`.
- **Congelamiento 20/11.** Lo que no esté medido para esa fecha queda afuera. El mouse sigue siendo la entrada segura.

**Pendiente de infraestructura (útil pero no bloquea):** hacer que el replay decodifique el JPEG y corra `hands_loop` (`recording.py:54` ya lo decodifica para el remoto), y grabar un `.dj` con una mano tocando casillas conocidas para calibrar sin cámara.
