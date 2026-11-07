# Concept brief: criaturas fieles al canon (clips + etiqueta de vida flotante)

**Author:** miroagustin
**Date:** 2026-11-06

---

## Overview

La idea es que las criaturas del tablero se comporten como en el dejarik de las películas, y nada más que eso. Son dos cambios:

1. **Clips.** Recuperar los 14 clips que traen los modelos originales de Quaternius (`assets_src/originals/*.glb`) y asignar cada uno a un momento del juego. Hoy usamos 5: idle, walk, attack, hit, die.
2. **Etiqueta de vida.** Sacar el `#roster` de arriba a la izquierda (`web/hud.js:24-26`, `web/style.css:44`), que queda tapado por el canvas de debug, y poner sobre cada modelo un cartelito flotante con nombre y vida.

La regla del autor no se negocia: **el canon de Star Wars es la única fuente de verdad**. El canon muestra esto: los jugadores dan órdenes, las piezas pelean, la que gana le pega a la que pierde y levanta los brazos, la que pierde desaparece, el movimiento es duro (stop-motion) y el holograma es translúcido y parpadea. Ninguna fuente canon muestra piezas que se quejan, que reaccionan a un jugador inactivo o que reaccionan directamente a los jugadores.

Se consultaron seis lentes: diseño, detalle de código, alcance, comprensión, preparación para implementar y estructura. Todas llegaron a la misma conclusión central: **"usar los 14 clips" choca con "solo canon"**. Conviene cambiar el objetivo a "cada momento del canon tiene su clip" y documentar los clips que quedan sin usar a propósito.

---

## Analysis

### 1. Varias filas del mapa de momentos no tienen evento que las dispare (bloqueante)

Lo confirmaron las seis lentes, con referencias al código:

- **"Movimiento ilegal → No".** Ese evento no existe. En la fase `target`, tocar una casilla ilegal deselecciona en silencio y no emite nada (`dejarik/game.py:127-129`). `denied` solo cubre `not_your_turn` y `animating` (`docs/protocol.md:138`). Además, con la mano no se puede hacer un movimiento ilegal: el anillo de espera solo arranca en una pieza propia o en un destino legal (`hand_cell_ok`, `dejarik/transport.py:256-268`). Para el cliente, "ilegal" y "cancelar" son el mismo cambio de estado (`selected` pasa a null).
- **"Selección cancelada".** Tampoco hay evento. El cliente solo ve el diff de `msg.selected` (`web/main.js:61-63`). Con la mano no se cancela: tocar otra pieza propia la re-selecciona (`game.py:98-100`), y ese caso de re-selección falta en el mapa.
- **"Gana el defensor → Duck"** contradice al motor. El resultado `counter` significa que el defensor *pega* y el atacante pierde vida (`game.py:117-123`). Si el defensor esquiva y después el atacante recibe daño, el espectador ve un golpe que no dio nadie. Según el canon ("el ganador le pega al perdedor"), en `counter` el defensor tiene que pegar. Duck solo encajaría en `tie`, que hoy no tiene reacción. Igual sería una licencia, no canon.
- **"Margen grande → Weapon".** El browser no puede calcularlo. El resultado `attack` trae `atk_roll`, `def_roll` y `outcome` (`game.py:119`), pero ATK/DEF quedan en el servidor a propósito (`web/hud.js:53`). Habría que agregar `margin` al protocolo. Encima el daño siempre es 1 (`game.py:122`), así que un golpe "más fuerte" que hace el mismo daño le enseña algo falso al público.
- **"Victoria → Wave/Yes"** es ambiguo. En el código, `win` (`game.py:135`) significa fin de partida. En el canon, levantar los brazos pasa **después de cada pelea ganada**. Para el `win` final, el handler no puede elegir a los ganadores porque `Creature` no guarda `owner` (`creatures.js:47-58`). Se arregla con `c.owner = p.owner` en `Army.sync` (`creatures.js:151`).

### 2. Qué está anclado en el canon y qué no

| Momento | Clip propuesto | Fundamento | Veredicto |
|---|---|---|---|
| Moverse por orden | Walk (Run para 2 casillas del acechador) | Canon: las piezas se mueven cuando se les ordena | Ya está; Run es opcional y barato |
| Atacar | Punch (o Weapon fijo por tipo) | Canon: pelean | Ya está |
| Recibir golpe | HitReact | Canon: el ganador le pega al perdedor | Ya está |
| Morir y desaparecer | Death + fade | Canon | Ya está (`events.js:46-54`) |
| **Ganador levanta los brazos tras cada pelea** | Wave **o** Yes (uno solo) | **Canon (ANH)** | **Agregar**; es el único momento canon que hoy no tiene clip |
| Contraataque (`counter`) | Punch del defensor + HitReact del atacante | Canon | Corregir el orden actual |
| Pieza seleccionada | Jump → Jump_Idle | Ayuda de interfaz, no ficción | Opcional, o cortar: el resaltado de casilla (`main.js:166`) ya hace este trabajo |
| Girar hacia el dedo | (código) | **Inventado**: la pieza reacciona al jugador | Cortar |
| Movimiento ilegal | No | **Inventado** y sin evento | Cortar; `hud.notice` alcanza |
| Defensor gana | Duck | **Inventado**, contradice `counter` | Cortar (como mucho en `tie`, marcado como licencia) |
| Margen grande | Weapon | Neutro, pero necesita cambiar el protocolo | Cortar; opcional: Weapon como ataque fijo del soldado |

Una lente (detalle de código) sostuvo que Duck entra en "las piezas pelean". Las otras cinco lo marcaron como inventado o contradictorio. Este brief adopta la mayoría.

Sobre el clip de victoria, dos lentes advierten que **Wave se lee como "hola/chau"**, y en el gesto argentino como "no". **Yes es un cabeceo.** Ninguno de los dos es exactamente brazos arriba. Hay que mirarlos en el visor (`?viewer=<kind>`) a escala real antes de elegir.

### 3. Lo que más se acerca al canon no es un clip (hallazgo de cuatro lentes)

El canon dice "stop-motion duro". Si el mixer avanza de a pasos a unos 12 fps en `Army.update` (`creatures.js:174`), acumulando `dt`, son unas 3 líneas y **todas** las criaturas en **todos** los clips se ven más canon. Ojo: `FADE=0.2` suaviza las transiciones y va en contra de ese efecto.

### 4. Estado contra eventos: hay dos dueños para un solo clip (mayor)

La selección llega por `state`. El combate llega por la cola de eventos, y los eventos se mandan antes que el `state` (`transport.py:291-293`). Si se pone Jump_Idle al seleccionar:

- Los handlers que terminan en `c.play("idle")` (`events.js:31,43`) pisan el loop.
- Cuando `selected` pasa a null durante un commit, eso no puede disparar un "aterrizaje de cancelación". Se distingue porque en un commit `events.busy` es true.
- `army.sync` reconstruye las criaturas al reconectar, así que se pierde cualquier postura que solo viva en la criatura.

Si se mantiene la selección animada, la propuesta es una postura (`stance`: `idle` o `selected`) por criatura, que sale del `state`, más clips de evento que terminan en `c.rest()`. La regla: mientras la cola está ocupada, la cola manda.

### 5. Tiempos (mayor)

El servidor espera 5 s por evento (`config.toml:67`, `transport.py:226`) y el cliente se rinde a los 8 s (`events.js:68`). Una pelea con muerte más la victoria da unos 5 s. Los clips Wave, Yes, No y Duck duran 1.7 s, el doble que Punch. Además, mientras dura la animación `anim_done` bloquea la entrada ("Esperá…"). Conviene no hacer `await` del clip de victoria, o cortarlo.

### 6. Pipeline de assets (mayor)

- Los nombres de clip están repetidos en tres lugares: `creatures.js:9` (y la cápsula de reemplazo en `:20-28`), `tools/check_glb.py:16` y `tools/adapt_glb.py:23-45`. `tests/test_check_glb.py` arma sus fixtures desde `CLIPS`, y `docs/assets_checklist.md` documenta el contrato de 5 clips.
- Propuesta (diseño): como los 4 modelos ahora salen del mismo pack, `adapt_glb.py` debería **conservar todos los clips**, sacarles el prefijo `Armature|` y pasarlos a minúscula, sin decidir qué significa cada uno. `check_glb` mantiene los 5 como mínimo. El mapeo momento → clip vive en un único objeto en `creatures.js`, y `events.js` pide momentos, no nombres de clip.
- `play()` ya resuelve sin error si falta un clip (`creatures.js:75`), así que la cápsula sigue andando. Sumar un `console.warn` de una sola vez ayuda a verlo en el ensayo.
- Hay que volver a correr adapt en los 4 modelos y chequear que sigan bajo 5 MB (`check_glb.py:17`).
- `assets_src/originals/` está sin trackear (`??` en git). Sin eso el pipeline no se puede reproducir.

### 7. Etiqueta de vida (mayor)

- La proyección ya existe: `toPx`/`project` (`main.js:104-110`) y la colocación del anillo (`main.js:122-126`). No hace falta CSS2DRenderer, que efectivamente no está: Three.js r169 viene solo con GLTFLoader, SkeletonUtils y BufferGeometryUtils.
- **Riesgo que no estaba listado:** `#stage.mirror` aplica `scaleX(-1)` (`style.css:19`). Un div dentro de `#stage` muestra el texto al revés. Hay que poner las etiquetas en `#hud` y espejar la x a mano, como hace el click (`main.js:88`).
- Más riesgos: etiquetas encimadas por el ángulo de la cámara, choque con el anillo de espera (±40 px, `main.js:125`), etiquetas visibles cuando se pierde el tracking (hay que ocultarlas con `pose.ok`, igual que el anillo), qué pasa durante el fade de muerte, y que se pierde el resumen de piezas muertas (`events.js:52` las borra).
- Las etiquetas tampoco son canon: el tablero de la película no muestra vida. Son una ayuda de interfaz igual que el roster, y tienen que estar justificadas como tal.

---

## Goals vs. Non-Goals

**Goals**
- Que cada momento del canon tenga su animación: moverse, atacar, recibir el golpe, morir y desaparecer, **y el ganador levantando los brazos después de cada pelea**.
- Movimiento con sensación de stop-motion (mixer a pasos).
- La vida de cada pieza se puede leer sin que la tape el debug.
- Criterio para la demo, propuesto por la lente de estructura: 2 de cada 3 personas que lo ven por primera vez saben quién ganó el intercambio solo mirando la animación, y no queda ninguna animación trabada en 5 partidas completas.
- Rollback barato: cada etapa en su propio commit y un flag `?clips=basic`.

**Non-Goals**
- Usar los 14 clips como cuota. Duck, No, Jump, Jump_Idle y Jump_Land (y el que pierda entre Wave y Yes) quedan **sin usar a propósito**, con una línea en `assets_src/SOURCES.md` que explique el motivo canon.
- Cualquier reacción de la pieza al jugador: girar hacia el dedo, quejarse por inactividad, decir "no".
- Acoplar las criaturas a `hold`. `hold` maneja solo el anillo.
- Cambiar las reglas o el protocolo para justificar clips (por ejemplo `margin` para Weapon).
- Modelos nuevos o diseños de criaturas de las películas. Siguen los modelos CC0 de Quaternius.

---

## Alternatives Weighed

**Clips**
- **A. Mapa completo de 14 clips (borrador original).** Descartado: inventa comportamientos, necesita eventos y campos de protocolo que no existen y suma una máquina de estados atada al ruido de la mano. Con un dwell nervioso, las criaturas saltarían. Es el peor tipo de falla para una demo en vivo.
- **B. Solo momentos canon (recomendado).** Victoria tras cada pelea, `counter` corregido y mixer a pasos. Opcionales: Run para 2 casillas (sale de `spec.adjacency` más `from`/`to`; ojo que `walkTo` va en línea recta, `creatures.js:104`) y Weapon como ataque fijo del soldado. Cuesta alrededor de un día.
- **C. B más salto al seleccionar, como ayuda de interfaz.** Se puede defender si se presenta explícitamente como UI. Pero duplica el resaltado, necesita la capa de postura (sección 4) y Jump_Idle deja a la criatura colgada en el aire con las piernas recogidas durante segundos. Va al final, solo si sobra tiempo.

**Etiqueta**
- **a. Solo CSS:** mover `#roster` para que no quede bajo el debug (`style.css:44`). Costo casi nulo.
- **b. Etiqueta solo en las dos piezas que pelean, mientras pelean.** Pocas etiquetas, así que no se enciman, y se apoya en `hud.combat`.
- **c. Etiquetas siempre visibles en las 8 piezas.** Nombre corto, vida en pips, color por bando (clases `p0`/`p1`), fade con `1 - c.pass` y ocultas sin tracking.
- **Roster:** una lente propone reemplazarlo por un contador chico de piezas muertas. Otra propone ocultarlo por defecto y mostrarlo con debug, así el rollback es una línea de CSS. Las dos conservan el resumen de piezas muertas.

---

## Key Decisions & Staging for Next Steps

**Aceptado por el autor (2026-11-06):** todos los recortes y el alcance de abajo. La única fuente de verdad es el canon; lo que no aparece ahí no se inventa (sin queja por inactividad, sin No, Duck, giro hacia el dedo ni Weapon por margen). El salto al seleccionar queda como opcional y se presenta como UI, no como ficción.

**Decisiones a tomar antes de codear**
1. Cambiar el objetivo de "14 clips" a "cada momento canon tiene clip". Cortar No, Duck, el giro hacia el dedo y Weapon por margen.
2. "Victoria" = brazos arriba del sobreviviente **dentro del handler `death`**, sin `await` o recortado. En `win`, repetirlo en los sobrevivientes (requiere guardar `owner`).
3. Elegir **un** clip de victoria entre Wave y Yes, después de verlos en el visor a escala.
4. `counter` = Punch del defensor + HitReact del atacante. Para `tie`: nada, o licencia documentada.
5. Separar clips y etiquetas en **dos diseños o etapas independientes**. No comparten código, riesgos ni prueba, y un problema con la etiqueta no tiene por qué frenar los clips.
6. Etiqueta: elegir entre a, b o c y decidir qué pasa con el resumen de piezas muertas antes de borrar `#roster`.

**Etapas (cada una es un commit que se puede revertir)**
1. **Assets:** `adapt_glb.py` conserva todos los clips, se commitea `assets_src/originals/`, se agrega un test de que adapt conserva los clips nuevos, se chequea el tamaño y se agregan botones por clip en el visor (`main.js:193`). Visualmente no cambia nada.
2. **Canon:** mixer a pasos de unos 12 fps, victoria tras cada pelea, `counter` corregido y mapa momento → clip en un solo objeto en `creatures.js`.
3. **Etiqueta** (opción elegida), en `#hud` con x espejada.
4. **Opcional:** Run en 2 casillas, Weapon fijo para el soldado y, si sobra tiempo, salto al seleccionar como UI con la capa de postura.
5. **Congelar** cambios bastante antes del 2026-11-26. Se puede probar sin el tablero con click del mouse, `--replay fixtures/session_01.dj` y `?viewer=<kind>`.
