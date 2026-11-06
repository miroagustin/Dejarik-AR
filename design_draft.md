# Interacción con la mano: apuntar con el índice, confirmar con dos dedos y "atravesar" el holograma

*   **Author:** miroagustin
*   **Status:** Draft
*   **Date:** 2026-11-06

--------------------------------------------------------------------------------

## Overview

Hoy la mano sirve poco como entrada en Dejarik-AR por dos motivos. La casilla
que se elige con el pinch pulgar-índice queda corrida, y la criatura 3D siempre
se dibuja encima del video de la mano. Este diseño cambia tres cosas:

1.  **Cómo se elige la casilla.** La punta del índice (landmark 8) se apoya en
    el papel y se proyecta con la homografía que ya existe.
2.  **Cómo se confirma.** Se junta el dedo medio con el índice y se sostiene
    1 s sobre la misma casilla. Mientras tanto se ve un anillo de carga y
    suenan avisos.
3.  **Cómo se ven las criaturas bajo la mano.** Las que caen dentro de la caja
    de la mano bajan la opacidad y parpadean, así la mano del video se ve a
    través y se lee como que "las atraviesa". No se toca el depth buffer.

El flujo de juego no cambia: el toque de la mano sigue entrando por el mismo
camino que el clic del mouse (`on_host_tap → tap → game.apply`). La oclusión
real (una máscara de la mano escrita en el depth buffer) queda como etapa
opcional (E4), apagada por defecto y con fecha límite.

Fechas: el congelamiento es el **20/11/2026** y la demo el **26/11/2026**. El
mouse (`--input mouse` / `--input both`) es la entrada segura si la mano no
llega a los criterios.

## The Problem

**Problema 1: el 3D siempre tapa la mano.** El renderer dibuja las criaturas
encima del video sin importar dónde esté la mano. Si un jugador acerca la mano
a una criatura desde arriba, en pantalla parece que la agarra desde abajo. La
escena contradice lo que el jugador está viendo con sus propios ojos.

**Problema 2: la casilla elegida queda corrida.** El pinch pulgar-índice se
mide con la punta del dedo en el aire, a 3-4 cm del papel. La cámara mira a
unos 45°, así que al proyectar ese punto sobre el plano del tablero cae
"altura × tan(45°)" ≈ 3-4 cm más lejos. Eso es más o menos una casilla interior
entera (~4 cm), así que el jugador apunta a una casilla y el juego marca otra.

**Por qué importa para la demo.** La mano es lo que hace que la demo se parezca
al dejarik de la película: los jugadores eligen y ordenan, y la mano pasa a
través del holograma sin efecto. Si la casilla queda corrida, el público ve
errores. Si el 3D tapa la mano, el efecto se ve falso. Hoy, en cualquiera de
los dos casos, la alternativa práctica es el mouse.

**La solución en una frase.** Se apunta con el índice apoyado en el papel (con
el dedo en el papel no hay error de altura), se confirma juntando dos dedos y
sosteniendo 1 s, y las criaturas bajo la mano se vuelven translúcidas para que
la mano se vea a través.

## Goals

Cada goal tiene un criterio que se mide en el control (antes del 16-18/11),
**por separado desde cada lado de la mesa**, contra la línea base E0 (el gesto
actual medido con el overlay de debug).

*   **G1: elegir la casilla correcta.** La casilla sale de la punta del índice
    apoyada en el papel, con tolerancia en el borde para que no parpadee entre
    casillas vecinas.
    *   Criterio: 9 de 10 casillas correctas en cada anillo (interior y
        exterior), desde cada lado.
*   **G2: confirmar sin falsos positivos.** Se junta el medio con el índice
    (ratio 3D `d(8,12)/d(0,9)` sobre `hand_world_landmarks`, con el medio
    estirado) y se sostiene 1 s. La casilla queda fijada al empezar, y el gesto
    se cancela si el dedo se aleja más de un radio de su centro.
    *   Criterio: ninguna confirmación falsa en 2 min de juego normal, desde
        cada lado.
    *   Criterio: el gesto dispara una sola vez por intento.
*   **G3: el jugador sabe en qué estado está el gesto sin mirar la pantalla.**
    Hay un anillo de carga corrido al costado de la casilla, para que la mano no
    lo tape. Suenan avisos con `web/audio.js`: uno al empezar y otro al
    cancelar. Al confirmar suenan los sonidos que el juego ya tiene (`select`,
    los eventos, `denied`).
    *   Criterio: en el control, quien prueba por primera vez puede decir si el
        gesto se confirmó o se canceló sin que se lo expliquen.
*   **G4: las criaturas bajo la mano "se dejan atravesar".** Las criaturas
    cuya base proyectada cae dentro de la caja de la mano (`hand.box`, ver
    OQ1) bajan a una opacidad de ~0,35 y parpadean más, con un fundido de
    ~150 ms. El antebrazo no está cubierto. El efecto tiene que verse claramente distinto del
    fundido de "Tracking perdido".
    *   Criterio: en el control, la mano sobre una criatura se lee como "la
        atraviesa" y no como "está debajo".
*   **G5: los umbrales se definen en un solo lugar.** Viven en la sección
    `[hands]` de `config.toml` con claves nuevas, y hay un aviso si aparecen las
    claves viejas (`pinch_on/off`). El README y los briefs citan las claves sin
    copiar los números.
*   **G6: siempre hay una salida.** El mouse sigue andando como plan B
    (`--input mouse` / `--input both`), y el gesto viejo (pulgar-índice) se
    puede elegir por config.
*   **G7: el gesto tiene un solo nombre.** Se elige una frase que se pueda decir
    en voz alta (por ejemplo, "apuntá y juntá dos dedos") y se usa en el HUD, en
    el README y al explicarle al público.

## Non-Goals

*   **Estimar la altura de la mano** (por ejemplo, con solvePnP de la mano). Con
    el dedo apoyado en el papel no hace falta.
*   **Máscara de la mano por segmentación de píxeles.** Suma otro modelo y un
    payload binario que rompe el formato `[uint32][header][JPEG]` y los `.dj`.
*   **Oclusión con profundidad dentro del alcance obligatorio.** Solo entra como
    E4 opcional, y la variante "por lado en el punto del índice" requiere
    enmendar `concepts_brief.md:328`, que hoy la pone como Non-Goal.
*   **Gestos con dos manos o seguir dos manos a la vez.** Se queda
    `num_hands=1`, porque en la demo las manos en reposo quedan fuera del
    cuadro.
*   **Que la mano tape las criaturas en el visor remoto.** El remoto no recibe
    máscara.
*   **Volver a usar el pinch pulgar-índice como gesto principal.** Queda solo
    como opción por config.
*   **Tracking dentro del replay en esta entrega.** Que el replay corra
    `hands_loop` sobre el JPEG es útil pero no bloquea.

## Open Questions

*   **OQ1 (resuelta: opción B).** Se vuelven translúcidas las criaturas cuya
    base proyectada cae dentro de la caja de la mano (`hand.box`), no solo la de
    `hand.cell`. Se acepta que la caja no cubre el antebrazo y que llega 1-2
    cuadros tarde.
*   **OQ2: los valores por defecto de "medio estirado".** El Technical Plan
    propone la fórmula `|w12-w0| / |w10-w0|` sobre world landmarks, con
    `extended_on = 1.15` y `extended_off = 1.05`. Los números salen de
    proporciones típicas de la mano (palma ~9 cm, dedo medio ~8 cm), no de
    mediciones. Se confirman con los histogramas de E1.
*   **OQ3: el formato de la config** (propuesto en el Technical Plan:
    subtablas `[hands.touch]` y `[hands.pinch]`). Falta confirmar.
*   **OQ4: el radio de cancelación** (propuesto: un radio único de 20 mm). En
    el tablero real (`board_spec.json` escalado), la casilla interior mide
    ~37 mm en dirección radial y ~28 mm de arco en el medio. La exterior mide
    ~38 mm radial y ~47 mm de arco. El "~4 cm / ~7,8 cm" del brief está
    corrido respecto de esto. Con 20 mm se absorbe el temblor de ~10 mm en las
    dos.
*   **OQ5: el plan B (propuesto: `gesture = "dwell"`, implementado en E1).**
    Cuesta una línea y un caso de test, así que el cambio de plan el día del
    control es editar `config.toml` y no programar.

## Technical Plan (Architecture)

### Dónde vive cada cosa

La lógica del gesto vive **entera en Python**, en el hilo de manos. El
navegador solo dibuja lo que recibe en `hand`. Hay tres motivos:

*   el toque ya entra al juego desde Python (`on_tap → tap → game.apply`);
*   el test de la máquina de estados no necesita navegador;
*   el visor remoto recibe el mismo estado sin lógica duplicada.

```text
 cámara ─► vision_loop ──(bgr, pose, frame_id)──► frame_bus
                ▲                                      │
                │ get_hand()                           ▼
           hands_box ◄── publish_hand ◄── hands_loop (hilo de manos)
                                            │  HandTracker.landmarks()
                                            │    -> lm2d (21×2 px), lmw (21×3 m, world)
                                            │  métrica según gesture:
                                            │    touch: d3(8,12)/d3(0,9) si medio estirado
                                            │    pinch: d2(4,8)/d2(0,9)   (gesto viejo)
                                            │    dwell: 0 (siempre "cerrado")
                                            │  casilla: image_to_board(lm2d[8]) -> (x, y) -> cell_at
                                            │  Confirm.update(métrica, cell, (x, y), t)
                                            │    -> casilla confirmada o None
                                            ├─► on_tap(casilla_fijada)  ──► juego
                                            └─► hand = {cell, pinch, px, hold, box}
                                                       + dbg (solo para el overlay)
 vision_loop: encode_frame(..., hand)  ──► host
              encode_remote(..., hand escalado) ──► remoto
 navegador (main.js, cada cuadro de render):
   hand.cell  -> resaltado (ya existe)
   hand.hold  -> anillo + sonidos (tic al empezar, sonido al cancelar)
   hand.box   -> criaturas dentro de la caja: setPass(1), con fundido de ~150 ms
   hand.px    -> pista del gesto en el HUD (aparece cuando hay mano en cuadro)
```

### 1. Landmarks 3D

`HandTracker.landmarks()` devuelve también `hand_world_landmarks[0]` como un
array (21, 3) en metros. MediaPipe ya lo calcula en la misma llamada a
`detect_for_video`, así que no suma costo de inferencia. La escala de esos
metros la estima el modelo, y por eso **solo se usan ratios**, nunca distancias
absolutas.

### 2. La métrica del gesto (`gesture` en `[hands]`)

| `gesture` | Métrica que se pasa a `Confirm` | Umbrales |
|---|---|---|
| `"touch"` (por defecto) | `d3(w8,w12) / d3(w0,w9)` si el medio está estirado; si no, `inf` (cuenta como "abierto") | `[hands.touch] on, off` |
| `"pinch"` | `d2(lm4,lm8) / d2(lm0,lm9)`, el cálculo de hoy (`hands.py:92`) | `[hands.pinch] on, off` |
| `"dwell"` | `0.0` siempre: se confirma con solo quedarse quieto | ninguno; vale `hold_ms` |

**"Medio estirado"** se calcula como `|w12-w0| / |w10-w0|`: la distancia de la
muñeca a la punta del medio dividida por la distancia de la muñeca a la
articulación media (PIP) del medio. Con el dedo estirado da ~1,25, y con el
dedo doblado da menos de 1. Para empezar el gesto el ratio tiene que superar
`extended_on`. Una vez empezado, alcanza con que supere `extended_off`, que es
más bajo, para que el temblor cerca del umbral no cancele el gesto.

Que el medio no esté estirado se trata como "mano abierta" (`inf`), no como
"sin mano" (`None`). Así el motivo de la cancelación en el debug distingue
"soltaste" de "se perdió la mano".

### 3. `Confirm`: la máquina de estados

Es una clase nueva en `hands.py` que **envuelve a `Pinch`** sin cambiarlo.
`Pinch` sigue aplicando la histéresis, el tiempo mínimo y el disparo único.
`Confirm` le agrega la casilla fijada y la cancelación por distancia. No sabe
nada de MediaPipe, así que se testea con secuencias sintéticas.

```text
Confirm(on, off, hold_ms, cancel_radius_m, spec)
  update(metric, cell, xy, t) -> casilla confirmada | None
  estado expuesto: lock_cell, hold (0..1), reason ("" | "suelta" | "salió" | "sin mano" | "afuera")

  metric None (sin mano)         -> pinch.update(None); lock = None; reason = "sin mano"
  pinch pasa de inactivo a activo:
      cell None                  -> pinch.update(None); reason = "afuera"
      si no                      -> lock_cell = cell
  activo y |xy - centro(lock)| > radio -> pinch.update(None); lock = None; reason = "salió"
  pinch pasa de activo a inactivo sin disparar -> reason = "suelta"
  pinch.update(...) devuelve True -> devuelve lock_cell (hold queda en 1 hasta soltar)
  hold = min(1, (t - closed_since) / min_s) mientras está activo, 0 si no
```

`hands_loop` llama a `on_tap(lock_cell)` con lo que devuelve `Confirm`, y no
con la casilla del cuadro actual. Si la pose no está ok, `cell` y `xy` son
`None`: la métrica se pasa igual, pero `Confirm` trata `cell None` al empezar
como "afuera" y `xy None` durante el gesto como "salió". El efecto es el mismo
que hoy, donde `on_tap` solo se llama con la pose ok.

### 4. Resaltado estable (tolerancia del borde)

La casilla que se publica en `hand.cell` es:

*   durante el gesto, `lock_cell`, que no se mueve aunque el dedo tiemble;
*   fuera del gesto, la casilla cruda, pero solo cambia cuando la casilla nueva
    se repite `cell_frames` cuadros seguidos (3 por defecto, ~100 ms a
    30 fps). Este debounce no depende del tamaño de la casilla, así que sirve
    igual para los dos anillos.

### 5. Campos de `hand` (protocolo v1, solo se agregan campos)

```json
"hand": {"cell": 7, "pinch": true, "px": [u, v], "hold": 0.62, "box": [u0, v0, u1, v1]}
```

*   `hold`: progreso del gesto entre 0 y 1. Vale 1 desde que se confirma hasta
    que se suelta. Si baja de un valor menor que 1 a 0, el gesto se canceló.
    Con eso el navegador detecta "empezó", "se confirmó" y "se canceló" sin un
    campo de evento.
*   `box`: la caja de los 21 `lm2d`, agrandada `box_margin` (0,15 por defecto)
    de su ancho y alto por lado, en píxeles del cuadro. Es `null` sin mano.
*   `pinch` sigue existiendo y significa "gesto cerrado". El debug lo usa para
    el color del punto.
*   `NO_HAND` queda **en un solo lugar** (`hands.py`): `vision.py` lo importa y
    se borra la copia de `vision.py:183`. Importar `hands.py` no carga
    MediaPipe, porque MediaPipe se importa adentro de `HandTracker`.
*   `encode_remote` escala `px` y `box` con `sx, sy`, como ya hace con `K`.
    Esto arregla de paso el bug de `hand.px` sin escalar en el remoto. El
    replay re-codifica el remoto con la misma función, así que queda arreglado
    también.
*   El dict publicado lleva una clave `"dbg"` con `{metric, extended, hold,
    lock_cell, reason}`. `vision_loop` la saca del dict (como hoy saca
    `pinch_ratio`) y la manda en `debug.hand` solo cuando el overlay está
    activo.

### 6. Config: `[hands]` y sus subtablas

```toml
[hands]
gesture = "touch"        # "touch" | "pinch" | "dwell"
hold_ms = 1000
cancel_radius_mm = 20
cell_frames = 3
box_margin = 0.15
input_width = 640

[hands.touch]
on = 0.35                # se calibra con histogramas (E1)
off = 0.45
extended_on = 1.15
extended_off = 1.05

[hands.pinch]
on = 0.25
off = 0.35
```

Si aparecen las claves viejas (`pinch_on`, `pinch_off` o `pinch_ms`) en
`[hands]`, `hands_loop` escribe una advertencia en el log que dice a qué clave
nueva se movió cada una y las ignora. No se migran solas, porque la unidad del
gesto nuevo es distinta. Los `on/off` de `touch` arrancan como suposición: el
valor real sale de E1.

### 7. Navegador

*   **"Se deja atravesar".** Hoy la opacidad de una criatura la escriben dos
    caminos que se pisan: el fundido por pérdida de tracking (`main.js:102`) y
    la muerte (`events.js:51`). `Creature` pasa a guardar dos factores:
    `baseOpacity`, que es lo que escribe `setOpacity` hoy, y `pass` (0..1). La
    opacidad final es `baseOpacity × (1 − 0,65·pass)`, que con `pass = 1` da
    ~0,35. `pass` también va a un uniform nuevo por material, `uPass`, que
    agranda el parpadeo del shader. El look es "parpadeo rápido sin bajar el
    brillo", distinto del fundido parejo a 0,2 de "Tracking perdido", que
    además muestra el aviso en el HUD. El destello de golpe (`uFlash`) no se
    toca.
*   **Qué criaturas entran.** En cada cuadro de render, `main.js` proyecta la
    posición de la raíz de cada criatura a píxeles del cuadro, con la misma
    cuenta que `project` (`main.js:88`), y la compara con `hand.box`. Las que
    caen adentro van hacia `pass = 1` y las demás hacia 0, con la misma
    suavización exponencial que usa `poseAlpha`, con τ ≈ 0,05 s (~150 ms
    hasta llegar casi al objetivo). Se usa la posición actual de la raíz, no la
    casilla, así una criatura caminando también entra.
*   **Anillo.** Es un `<div>` con `conic-gradient` de CSS, sin canvas ni
    Three.js. Se ubica en el centro proyectado de `hand.cell` más un
    corrimiento fijo en pantalla (arriba a la derecha, ~60 px del cuadro)
    para que el dedo no lo tape. Se ve mientras `hold > 0`.
*   **Sonidos.** Se agregan dos sonidos a `web/audio.js`: `holdStart` (tic) y
    `holdCancel` (descendente corto). La confirmación **no tiene sonido
    propio**, porque el toque ya dispara los sonidos del juego: `select` al
    elegir, los eventos al mover o atacar y `denied` si no es tu turno. Un
    acorde extra se pisaría con esos. Esto se aparta del brief, que pedía un
    acorde al confirmar.
*   **Pista del gesto en el HUD.** `hud.js` muestra el texto "Apuntá con el
    índice y juntá dos dedos" mientras `hand.px` no es null. El texto sale del
    HUD, no de la config, y es la frase que también se usa en el README.
*   **Debug.** `debug.js` reemplaza la línea `pinch` por `métrica · medio
    estirado sí/no · hold · fijada N · motivo`, leyendo de `debug.hand`, y
    dibuja `hand.box` como un rectángulo.

### 8. E4: oclusión real (opcional, fuera de este plan)

No se diseña acá. Si E1-E3 cierran antes del 18/11, se escribe un design
corto aparte. Ese design parte de lo que ya dice el brief: medir el desfase,
agregar `frame_id` a `hand`, usar el hull dilatado de 21 puntos, el patrón de
oclusor de `scene.js:54-58` y cuidar el `flipY`. La caja que se agrega en este
plan (`hand.box`) sirve para medir el desfase sin agregar nada más.

## Alternatives Considered

Las alternativas A a J salen de la tabla "Alternatives Weighed" del brief. De
la K a la N se descartaron mientras se escribía este draft.

### Elegir la casilla

#### A: Estimar la altura de la mano (solvePnP de la mano)

*   **Pros**: funcionaría con el dedo en el aire, sin tocar el papel.
*   **Cons**: mucho trabajo, y depende de un tamaño de mano que el modelo
    estima. Una mano más chica o más grande corre el resultado.
*   **Reason for Rejection**: Rechazado por el autor: el dedo apoyado en el
    papel elimina el error de altura sin código nuevo
    (`image_to_board(lm[8])` ya existe), y el costo es solo una regla de uso.

### El gesto de confirmación

#### B: Medio junto al índice medido en centímetros (`hand_world_landmarks`)

*   **Pros**: se explica fácil ("juntá dos dedos") y el umbral se lee en
    unidades físicas.
*   **Cons**: los centímetros los estima el modelo, así que un umbral fijo de
    1,5 cm cambia según la mano y según el ángulo.
*   **Reason for Rejection**: Rechazado por el autor: el ratio 3D (alternativa
    elegida) mide lo mismo sin depender de la escala estimada.

#### C: Medio junto al índice con ratio 2D `d(8,12)/d(0,9)` en píxeles

*   **Pros**: reusa el cálculo de `hands.py:92` y es un cambio de una línea.
*   **Cons**: desde el lado cercano, las puntas del índice y del medio se
    alinean con la línea de visión y en 2D parecen juntas aunque no lo estén.
*   **Reason for Rejection**: Rechazado por el autor: pidió medirlo en 3D para
    que la perspectiva no lo engañe.

#### D: Exigir además anular y meñique doblados

*   **Pros**: filtra la mano relajada, que ya tiene el índice y el medio juntos.
*   **Cons**: agrega otra condición que el modelo tiene que acertar, y a 45° el
    anular y el meñique también quedan tapados.
*   **Reason for Rejection**: Rechazado por el autor: en la demo las manos en
    reposo quedan fuera del cuadro. El riesgo que queda (una mano apoyada sobre
    un destino válido mueve la pieza en 1 s) se mide en el control.

#### E: Solo quedarse quieto 1-1,2 s, sin segundo gesto (dwell)

*   **Pros**: es lo más simple y no depende del dedo medio.
*   **Cons**: un apoyo distraído sobre un destino válido mueve la pieza.
*   **Reason for Rejection**: No se descarta. Queda como plan B, implementado
    como `gesture = "dwell"` desde E1 (OQ5), para cambiarlo por config si el
    gesto de dos dedos da confirmaciones falsas en el control.

### Problema 1: el 3D tapa la mano

#### F: Oclusión con un hull dilatado que siempre tapa (depth cerca de la cámara)

*   **Pros**: oclusión de verdad, sin lógica por lado, y reusa el patrón de
    oclusor de `scene.js:54-58`.
*   **Cons**: la máscara llega 1-2 cuadros tarde (`hands.py:76`,
    `vision.py:206`), así que al mover la mano la criatura se desliza sobre el
    borde. Hay que sincronizar el `frame_id`, y el brief general pone la
    oclusión como Non-Goal (`concepts_brief.md:328`).
*   **Reason for Rejection**: Rechazado por el autor para el alcance
    obligatorio. Queda como E4 opcional, apagada por defecto, solo si E1-E3
    cierran antes del 18/11.

#### G: Hull a la profundidad del punto del índice, por lado

*   **Pros**: es lo que se pidió primero: la mano tapa o no según de qué lado
    está.
*   **Cons**: una sola profundidad está mal para los nudillos y el brazo, que a
    45° quedan mucho más cerca de la cámara. Además la profundidad salta cuando
    el dedo se levanta.
*   **Reason for Rejection**: Rechazado por el autor: solo se considera si F se
    ve mal, y requiere enmendar `concepts_brief.md:328`.

#### H: Máscara por segmentación de píxeles

*   **Pros**: la silueta real, brazo incluido.
*   **Cons**: otro modelo (+10-20 ms por cuadro) y un segundo payload binario
    que rompe el formato `[uint32][header][JPEG]`, los `.dj` y
    `fixtures/session_01.dj`.
*   **Reason for Rejection**: Rechazado por el autor: el costo en latencia y en
    protocolo no entra antes del 20/11.

#### I: "Se deja atravesar" solo para la criatura de `hand.cell` (OQ1 A)

*   **Pros**: no agrega campos al protocolo.
*   **Cons**: mientras la mano se acerca, el brazo y los nudillos pasan sobre
    otras criaturas, que se siguen dibujando encima.
*   **Reason for Rejection**: Rechazado por el autor: con `hand.box` (un campo
    de 4 números) se cubre la mano entera.

#### J: Caja de la mano estirada hasta el borde por el antebrazo (OQ1 C)

*   **Pros**: cubre también el antebrazo.
*   **Cons**: depende de la dirección `lm9→lm0`, que falla con la muñeca
    doblada, y la caja puede abarcar medio tablero y volver translúcidas
    criaturas lejanas.
*   **Reason for Rejection**: Rechazado por el autor: tiene más casos que fallan
    que el antebrazo sin cubrir.

### Decisiones del Technical Plan

#### K: Máquina de estados del gesto en el navegador

*   **Pros**: el anillo y los sonidos reaccionan sin esperar el cuadro siguiente.
*   **Cons**: el toque tendría que volver del navegador a Python, el remoto
    necesitaría la misma lógica y el test necesitaría un navegador.
*   **Reason for Rejection**: Rechazado por el autor (aprobó el Technical Plan):
    `on_tap` ya vive en Python, y `hold` alcanza para que el navegador dibuje.

#### L: Cambiar `Pinch` en vez de envolverlo con `Confirm`

*   **Pros**: una clase menos.
*   **Cons**: mezcla la histéresis (que hoy está testeada,
    `tests/test_hands.py:9-19`) con la casilla y el radio, y el gesto viejo
    (`gesture = "pinch"`) usa el mismo `Pinch`.
*   **Reason for Rejection**: Rechazado por el autor (aprobó el Technical Plan):
    envolverlo deja `Pinch` y su test sin tocar.

#### M: Reusar `pinch_on/off/ms` con la unidad nueva

*   **Pros**: no hay claves nuevas.
*   **Cons**: una config vieja carga sin error con valores de otra unidad, y
    volver al gesto viejo obliga a cambiar los números a mano.
*   **Reason for Rejection**: Rechazado por el autor (aprobó el Technical Plan):
    con las subtablas `[hands.touch]` y `[hands.pinch]`, cada gesto tiene sus
    umbrales y las claves viejas solo generan un aviso.

#### N: Acorde propio al confirmar

*   **Pros**: avisa de la confirmación aunque el toque no cambie nada en el
    juego (por ejemplo, un toque en una casilla no válida, que deselecciona sin
    sonido).
*   **Cons**: se pisa con `select`, con los sonidos de los eventos y con
    `denied`, que ya suenan al confirmar.
*   **Reason for Rejection**: Rechazado por el autor (aprobó el Technical Plan):
    se acepta que la deselección quede sin sonido. Esto se aparta del brief,
    que pedía un acorde.

--------------------------------------------------------------------------------

### Additional Resources

*   `hand_interaction_brief.md`: el brief de este design (2026-11-06).
*   `concepts_brief.md`: el brief general (Non-Goal de oclusión en la línea
    328, plan de 20 días).
*   `docs/designs/dejarik_ar.md`: el design general (sección "Mano y pinch").

### Cambios respecto del brief (decididos por el autor)

1.  **Criaturas translúcidas.** Las elige `hand.box` (OQ1 B), no solo
    `hand.cell`.
2.  **Sonido al confirmar.** No hay acorde propio; suenan los sonidos del juego
    (alternativa N).
3.  **Campos de `hand`.** Son `hold` y `box`. `lock_cell` va solo en
    `debug.hand`, porque durante el gesto `hand.cell` ya vale `lock_cell`.
4.  **Claves de config.** Son `gesture = "touch"|"pinch"|"dwell"` y `hold_ms`,
    con las subtablas `[hands.touch]` y `[hands.pinch]`, en lugar de
    `confirm_on/off/ms`.
5.  **Tiempo del plan B.** `dwell` usa el mismo `hold_ms`. Para ir a 1,2 s hay
    que poner `hold_ms = 1200`.

--------------------------------------------------------------------------------

## Detailed Implementation Plan

Los archivos están ordenados por etapa. Cada etapa se entrega y se prueba por
separado: E1 (gesto en Python), E2 (anillo, sonido, HUD y docs) y E3 ("se
deja atravesar"). E0 no toca código: es la medición de base con el gesto
actual. E4 no está en este plan.

**Compatibilidad.** El navegador trata los campos nuevos de `hand` como
opcionales (`hand.hold ?? 0`, `hand.box ?? null`). Así siguen andando los
`.dj` viejos, `fixtures/session_01.dj` y `tools/fake_session.py`, que mandan
`hand` con solo `{cell, pinch, px}`, sin cambiarlos.

### Target Files to Create/Modify

#### E1: gesto en Python

##### 1. `dejarik/hands.py` (Modify)

*   **Type / Scope**: módulo Python (hilo de manos).
*   **Proposed Changes**:
    *   `NO_HAND = {"cell": None, "pinch": False, "px": None, "hold": 0, "box":
        None}`. Pasa a ser la única definición.
    *   Docstring del módulo: describe "apuntá con el índice apoyado y juntá
        dos dedos (o el gesto de `gesture`)" en vez de "pinch".
    *   `HandTracker.landmarks(bgr, t) -> (lm2d, lmw) | None`:
        *   `lm2d` es lo de hoy, un array (21, 2) en píxeles de la imagen
            completa;
        *   `lmw` es un array (21, 3) armado con
            `res.hand_world_landmarks[0]` (`p.x, p.y, p.z`).
    *   `def middle_extended(lmw, thresh) -> bool`: devuelve
        `|w12-w0| / max(1e-6, |w10-w0|) > thresh`.
    *   `def gesture_metric(gesture, lm2d, lmw, ext_thresh) -> float`:
        *   `"touch"`: `|w8-w12| / max(1e-6, |w0-w9|)` si
            `middle_extended(lmw, ext_thresh)`; si no, `math.inf`;
        *   `"pinch"`: `|l4-l8| / max(1e-6, |l0-l9|)` en 2D, el cálculo de hoy;
        *   `"dwell"`: `0.0`;
        *   otro valor: `ValueError` con el nombre recibido.
    *   `def gesture_params(cfg) -> dict`: lee `[hands]` y la subtabla del
        gesto elegido, y devuelve `{gesture, on, off, ext_on, ext_off, hold_ms,
        cancel_radius_m, cell_frames, box_margin}`.
        *   Si en `cfg` aparece alguna de `pinch_on`, `pinch_off` o `pinch_ms`,
            hace `print("AVISO: [hands] pinch_on/pinch_off/pinch_ms ya no se
            usan; ver [hands.pinch] on/off y [hands] hold_ms")` una sola vez y
            las ignora. Es el mismo estilo de aviso que `__main__.py:42`.
        *   Para `"dwell"`, `on`/`off` valen `0.5`/`0.5`, así la métrica `0.0`
            queda siempre "cerrada".
        *   Para `"pinch"`, `ext_on`/`ext_off` no se usan.
    *   `class Confirm` (`Pinch` no se toca):
        *   `__init__(on, off, hold_ms, cancel_radius_m, cell_frames, spec)`:
            crea un `Pinch(on, off, hold_ms)` interno. El estado arranca en
            `lock_cell=None`, `reason=""`, `shown=None`, `cand=None`, `cand_n=0`.
        *   `update(metric, cell, xy, t) -> int | None`, con este orden:
            1.  `was = pinch.active`.
            2.  Si `metric is None`: `pinch.update(None, t)`; si `was`,
                `reason = "sin mano"`; `lock_cell = None`; actualiza `shown`
                (paso 7) con `None`; devuelve `None`.
            3.  Si `was` y (`xy is None` o `dist(xy, cell_center(lock_cell))
                > cancel_radius_m`): `pinch.update(None, t)`; `reason =
                "salió"`; `lock_cell = None`.
            4.  `fired = pinch.update(metric, t)`.
            5.  Si `not was and pinch.active`:
                *   si `cell is None`: `pinch.update(None, t)` y `reason =
                    "afuera"`;
                *   si no: `lock_cell = cell` y `reason = ""`.
                *   Si `hold_ms` es 0, `Pinch` puede disparar en el mismo
                    cuadro en que se activa. En ese caso, `fired` con `cell is
                    None` se descarta.
            6.  Si `was and not pinch.active` y `reason == ""`: `reason =
                "suelta"`; `lock_cell = None`.
            7.  `shown`: si `pinch.active`, vale `lock_cell`. Si no, aplica el
                debounce: si `cell == shown`, resetea el candidato; si no, cuenta
                cuántos cuadros seguidos se repite `cell` como candidato, y
                cuando llega a `cell_frames` pasa a `shown = cell`. `None`
                también es un candidato (el dedo salió del tablero).
            8.  Devuelve `lock_cell if fired and lock_cell is not None else
                None`.
        *   La propiedad `hold` vale `0` si no está activo; si está activo,
            `1` si ya disparó y `min(1, (t_last - closed_since) / min_s)` si
            no. `t_last` es el `t` del último `update`.
        *   La propiedad `active` vale `pinch.active`.
    *   `hands_loop(get_packet, publish_hand, on_tap, stop, K, dist, spec,
        cfg)`, misma firma:
        *   `p = gesture_params(cfg)` y `conf = Confirm(...)`.
        *   Por cuadro:
            *   sin `lm`: `conf.update(None, None, None, t)` y publica
                `dict(NO_HAND, cell=conf.shown, dbg={...})`;
            *   con `lm`: `ext_thresh = p.ext_off if conf.active else
                p.ext_on`; `metric = gesture_metric(...)`; si `pose.ok`, `xy =
                image_to_board(*lm2d[8], ...)` y `cell = cell_at(*xy, spec)`;
                si no, `xy = cell = None`.
        *   `tap = conf.update(metric, cell, xy, t)`; si `tap is not None`,
            llama a `on_tap(tap)`.
        *   `box`: el mínimo y el máximo de `lm2d`, agrandados `box_margin ×
            (ancho, alto)` por lado, redondeados a 0,1 px.
        *   Publica `{"cell": conf.shown, "pinch": conf.active, "px": [...],
            "hold": round(conf.hold, 2), "box": [u0, v0, u1, v1], "dbg":
            {"metric": round(metric, 3) or None si es inf, "extended":
            bool, "hold": ..., "lock_cell": conf.lock_cell, "reason":
            conf.reason}}`.
    *   **Por qué**: es G1, G2, G5, G6 y OQ5. `Confirm` es la máquina de
        estados y se puede testear, `gesture_metric` implementa el gesto 3D y
        el plan B, y `gesture_params` arma la config de una sola fuente con el
        aviso para las claves viejas.

##### 2. `dejarik/vision.py` (Modify)

*   **Type / Scope**: módulo Python (hilo de visión).
*   **Proposed Changes**:
    *   Borrar `NO_HAND` (línea 183) y agregar `from dejarik.hands import
        NO_HAND` arriba. `hands.py` solo importa `cv2`, `numpy` y
        `dejarik.board` a nivel de módulo, así que no se carga MediaPipe.
    *   En `vision_loop`: `hand_dbg = hand.pop("dbg", None)` reemplaza a
        `ratio = hand.pop("pinch_ratio", None)`. En el dict `debug`, la clave
        `"pinch_ratio": ratio` pasa a ser `"hand": hand_dbg`.
    *   En `encode_remote`: antes de codificar, `hand = scale_hand(hand, sx,
        sy)`. `scale_hand` es una función nueva en `vision.py` que devuelve una
        copia con `px` y `box` multiplicados por `(sx, sy)` cuando no son
        `None`, y el resto igual.
    *   **Por qué**: deja `NO_HAND` en un solo lugar (el brief, `hands.py:14` y
        `vision.py:183`), lleva el debug nuevo al overlay y arregla `px` sin
        escalar en el remoto (`vision.py:171-180`), que ahora también le pasaría
        a `box`.

##### 3. `config.toml` (Modify)

*   **Type / Scope**: configuración.
*   **Proposed Changes**: reemplazar las claves `pinch_on`, `pinch_off` y
    `pinch_ms` de `[hands]` (líneas 36-40) por el bloque del Technical Plan,
    sección 6: `[hands]` con `gesture`, `hold_ms`, `cancel_radius_mm`,
    `cell_frames`, `box_margin` e `input_width`, y las subtablas
    `[hands.touch]` y `[hands.pinch]`. Las subtablas van justo después de
    `[hands]` y antes de `[net]`, para que TOML no las mezcle con otra sección.
*   **Por qué**: G5, una sola fuente para los umbrales.

##### 4. `tests/test_hands.py` (Modify)

*   **Type / Scope**: tests unitarios (pytest).
*   **Proposed Changes**: el test de `Pinch` y el de `image_to_board` quedan
    como están. Se agregan:
    *   `test_confirm_fires_once_at_hold_ms`: con `cell=5` y `xy=cell_center(5)`
        fijos, la métrica cerrada dispara una sola vez a los 1000 ms y devuelve
        `5`. `hold` sube de 0 a 1 y queda en 1 hasta soltar.
    *   `test_confirm_uses_locked_cell`: empieza en la casilla 5. A los 500 ms
        el dedo se mueve 10 mm, todavía adentro del radio de 20 mm, y
        `cell_at` da 6. Dispara con `5`, no con `6`, y `shown` queda en `5`
        durante todo el gesto.
    *   `test_confirm_cancels_outside_radius`: un movimiento de 30 mm a los
        500 ms cancela con `reason == "salió"` y `hold == 0`, y no dispara
        aunque la métrica siga cerrada después. Hace falta abrir y volver a
        cerrar.
    *   `test_confirm_cancels_on_lost_hand`: `metric None` a mitad del gesto da
        `reason == "sin mano"`.
    *   `test_confirm_ignores_start_off_board`: empezar con `cell None` no
        activa nada y da `reason == "afuera"`.
    *   `test_confirm_debounce`: fuera del gesto, `shown` cambia de casilla
        recién en el 3er cuadro seguido con la casilla nueva, y un cuadro
        suelto con otra casilla no lo cambia.
    *   `test_gesture_metric`: con un `lmw` sintético de la mano abierta y el
        medio estirado, más el índice y el medio juntos, `"touch"` da un valor
        menor que `on`. Con el medio doblado (w12 cerca de w9) da `inf`.
        `"dwell"` da `0.0` y un nombre desconocido levanta `ValueError`.
    *   `test_gesture_params_warns_old_keys` (con `capsys`): un cfg con
        `pinch_on` imprime el aviso una vez y devuelve los valores de
        `[hands.touch]`.
*   **Por qué**: cubre el test que pide E1 en el brief (dispara a 1 s, se
    cancela al salir, dispara una sola vez, se cancela si se pierde la mano),
    además de la casilla fijada, el debounce y la config. Se usa el mismo
    estilo de secuencias `(métrica, casilla, t)` que `test_hands.py:9-19`.

##### 5. `tests/test_vision.py` (Modify)

*   **Type / Scope**: test unitario.
*   **Proposed Changes**: agregar `test_encode_remote_scales_hand`. Con un
    cuadro de 1280×720, `remote_width=640` y `hand = {"px": [100, 50], "box":
    [10, 20, 30, 40], ...}`, el header decodificado tiene `px == [50, 25]` y
    `box == [5, 10, 15, 20]`, y el dict original no cambió.
*   **Por qué**: deja fijo el arreglo del bug de `hand.px` en el remoto.

#### E2: anillo, sonido, HUD y docs

##### 6. `tests/test_protocol.py` (Modify)

*   **Type / Scope**: test unitario.
*   **Proposed Changes**: `HAND` (línea 8) pasa a ser `{"cell": 7, "pinch":
    False, "px": [10, 20], "hold": 0.5, "box": [1, 2, 3, 4]}`. Los tests que
    ya existen verifican que los campos nuevos van y vuelven sin cambios, y
    que `v` sigue en 1.
*   **Por qué**: el protocolo suma campos, y el test tiene que verlos.

##### 7. `docs/protocol.md` (Modify)

*   **Type / Scope**: documentación del protocolo.
*   **Proposed Changes**:
    *   El ejemplo de `hand` (línea 60) pasa a ser `{"cell":null,"pinch":false,
        "px":null,"hold":0,"box":null}`.
    *   Se agregan viñetas para `hold` (0..1; 1 desde que se confirma hasta
        que se suelta; bajar de menos de 1 a 0 significa que se canceló) y
        para `box` (`[u0,v0,u1,v1]` en píxeles del cuadro, o `null`), y la
        nota de que en el remoto `px` y `box` van escalados como `K`.
    *   En `debug`, `"pinch_ratio":0.4` pasa a ser `"hand":{"metric":0.4,
        "extended":true,"hold":0.6,"lock_cell":7,"reason":""}`, con los
        valores posibles de `reason`.
    *   Una línea que dice que los campos nuevos son opcionales para quien
        lee, para no tener que subir `VERSION`.
*   **Por qué**: el brief, E2.

##### 8. `web/audio.js` (Modify)

*   **Type / Scope**: módulo JS (Web Audio).
*   **Proposed Changes**: dos entradas nuevas en `sounds`, con el mismo
    `tone()` que ya existe:
    *   `holdStart`: un tic corto, seno de ~1200 Hz, `dur ≈ 0.04`, `gain ≈ 0.15`;
    *   `holdCancel`: descendente corto, de ~500 a ~300 Hz, `dur ≈ 0.15`, tipo
        `"triangle"`, `gain ≈ 0.2`.
    *   Los dos tienen que sonar claramente distinto de `denied` (140 Hz,
        cuadrada).
*   **Por qué**: G3. El jugador mira su dedo, no la pantalla.

##### 9. `web/index.html` (Modify)

*   **Type / Scope**: markup.
*   **Proposed Changes**: agregar `<div id="hold-ring"></div>` adentro de
    `#stage`, después de `#debug`, para que se ubique en coordenadas del
    cuadro, y `<div id="hint"></div>` adentro de `#hud`.
*   **Por qué**: el anillo y la pista necesitan un elemento cada uno.

##### 10. `web/style.css` (Modify)

*   **Type / Scope**: estilos.
*   **Proposed Changes**:
    *   `#hold-ring`: `position:absolute`, 44×44 px, `border-radius:50%`,
        `pointer-events:none`, `display:none`, y un fondo `conic-gradient(var(--ring)
        calc(var(--p) * 1turn), transparent 0)` con una máscara radial para que
        quede como aro. `--ring` vale `var(--blue)`, la variable que ya existe en
        `style.css:2`.
    *   `#hint`: centrado abajo, con el mismo estilo de caja que los demás
        `#hud > div`.
*   **Por qué**: G3. Es un anillo hecho con CSS, sin canvas.

##### 11. `web/hud.js` (Modify)

*   **Type / Scope**: módulo JS (HUD).
*   **Proposed Changes**: agregar `hint(show)`, que pone en `#hint` el texto
    `"Apuntá con el índice y juntá dos dedos"` si `show` es verdadero, o lo
    vacía (y como `#hud > div:empty` se oculta, desaparece). El texto es una
    constante `HINT` al principio del archivo.
*   **Por qué**: G7, un solo nombre para el gesto, visible en pantalla.

##### 12. `web/main.js` (Modify)

*   **Type / Scope**: módulo JS (loop principal).
*   **Proposed Changes**:
    *   Agregar `let prevHold = 0` al estado. En el loop de render, con `h =
        lastHeader?.hand`, `hold = h?.hold ?? 0`:
        *   si `prevHold === 0 && hold > 0`: `audio.play("holdStart")`;
        *   si `prevHold > 0 && prevHold < 1 && hold === 0`:
            `audio.play("holdCancel")`;
        *   `prevHold = hold`.
    *   **Anillo:** si `hold > 0` y `h.cell != null` y hay pose, se proyecta el
        centro de la casilla con `project(...cellCenter(spec, h.cell), 0)`. Ese
        punto está en píxeles del cuadro y se pasa a píxeles de `#stage`
        multiplicando por `stage.clientWidth / header.size[0]`. El `<div>` se
        ubica ahí más `(+40, −40)` px, con `--p = hold`. Si no, se oculta.
    *   **Pista:** `hud.hint(h?.px != null)`, solo cuando el valor cambia.
    *   **Solo en el remoto:** si `you === 1`, el anillo y los sonidos de hold
        no se muestran, porque los produce la mano del anfitrión. La pista
        tampoco se muestra.
    *   **E3 ("se deja atravesar"):** después del bloque de `poseAlpha`, si
        `h?.box` y `lastHeader.pose.ok`, para cada criatura de `army.byId` se
        toma la posición de mundo de `c.root` y se pasa a píxeles del cuadro
        (la misma cuenta que `project`, pero partiendo de la posición de mundo
        con `projectionMatrix`). Se fija `target = 1` si cae dentro de
        `h.box` y `0` si no, o si no hay caja. Después, `c.pass += (target -
        c.pass) * Math.min(1, dt / 0.05)` y `c.setPass(c.pass)`. Corre también
        en el remoto, porque el video del remoto muestra la misma mano y `box`
        ya llega escalado.
    *   `import { cellCenter } from "./scene.js"`, si no está importado ya.
*   **Por qué**: G3 y G4. Todo depende de `hand`, sin lógica de gesto en el
    navegador (alternativa K descartada).

##### 13. `web/debug.js` (Modify)

*   **Type / Scope**: overlay de debug.
*   **Proposed Changes**:
    *   La línea 65 pasa a ser: `if (dbg?.hand) line(\`mano ${métrica o "—"} ·
        medio ${extended ? "estirado" : "doblado"} · hold
        ${hold.toFixed(2)} · fijada ${lock_cell ?? "—"} · ${reason ||
        "ok"}\`, y)`.
    *   Si `hand.box`, se dibuja un `strokeRect` blanco semitransparente con
        esa caja.
*   **Por qué**: lo que pide el brief para calibrar el día de la demo
    (distancia, si el medio está estirado, progreso, casilla fijada y motivo),
    más ver la caja para medir el desfase y para E4.

##### 14. `README.md` (Modify)

*   **Type / Scope**: documentación.
*   **Proposed Changes**:
    *   La línea 73 pasa a ser: "**Turno:** clic, o apuntá con el índice
        apoyado en el papel y juntá dos dedos (se sostiene `hold_ms`, con un
        anillo de carga) sobre una pieza propia…", y el resto igual.
    *   La línea 80 agrega: "gesto en `[hands] gesture` (`touch`, `pinch` o
        `dwell`)".
    *   Sin números copiados de la config.
*   **Por qué**: G5 y G7. Hoy dice "pulgar e índice 0,3 s".

##### 15. `docs/rules.md` (Modify)

*   **Type / Scope**: documentación de reglas.
*   **Proposed Changes**: el título de la línea 47 pasa a ser "Cómo se elige
    con clic, toque o gesto de la mano", más una oración debajo: "Con la mano:
    apuntá con el índice y juntá dos dedos; ver `[hands]` en `config.toml`".
*   **Por qué**: G7, un solo nombre para el gesto.

##### 16. `docs/demo_script.md` (Modify)

*   **Type / Scope**: guion de la demo.
*   **Proposed Changes**:
    *   La primera vez que el anfitrión usa la mano en el guion, agregar la
        frase para el público: "Apuntá con el índice y juntá dos dedos".
    *   En la tabla de fallas (línea 42), agregar una fila: "El gesto da
        confirmaciones falsas → `gesture = "dwell"` en `config.toml` y
        reiniciar".
*   **Por qué**: G7 y el plan B listo para usar (OQ5).

##### 17. `docs/designs/dejarik_ar.md` (Modify)

*   **Type / Scope**: design general.
*   **Proposed Changes**:
    *   Debajo del título "### Mano y pinch" (línea 380), una línea: "El gesto
        y su config se reemplazan por `docs/designs/hand_interaction.md`".
    *   El mismo aviso en la lista de config (línea 843).
    *   No se reescribe el resto.
*   **Por qué**: evita que haya dos fuentes que se contradicen sobre el gesto.

##### 18. `concepts_brief.md` (Modify)

*   **Type / Scope**: brief general.
*   **Proposed Changes**:
    *   En la línea 164, cambiar "empieza por debajo de 0,25 y termina por
        encima de 0,35" por "con histéresis (`[hands.pinch]` en
        `config.toml`)".
    *   Las líneas 160-164 suman una nota: "reemplazado por
        `docs/designs/hand_interaction.md`".
    *   La línea 328 (oclusión como Non-Goal) **no se toca**: se enmienda solo
        si se hace E4.
*   **Por qué**: G5 pide que los briefs no copien números.

#### E3: "se deja atravesar"

##### 19. `web/hologram.js` (Modify)

*   **Type / Scope**: shader del holograma.
*   **Proposed Changes**:
    *   En `makeHologramMaterial`, agregar `mat.userData.pass = { value: 0 }`
        junto a `flash`, y pasarlo como uniform `uPass`.
    *   En el fragment, declarar `uPass` y cambiar la línea del flicker a
        `float flicker = 1.0 - (uFlicker + 0.35 * uPass) * (0.5 + 0.5 *
        sin(uTime * (37.0 + 40.0 * uPass)) * sin(uTime * 13.0));`.
        `uPass` sube la amplitud y la frecuencia del parpadeo.
    *   El brillo base y el alfa del borde no cambian.
*   **Por qué**: G4. Parpadeo rápido sin bajar el brillo, distinto del fundido
    parejo de "Tracking perdido".

##### 20. `web/creatures.js` (Modify)

*   **Type / Scope**: módulo JS (criaturas).
*   **Proposed Changes**:
    *   En `Creature`, agregar los campos `baseOpacity = 1` y `pass = 0`.
    *   `setOpacity(o)` guarda `baseOpacity = o` y llama a `applyOpacity()`.
    *   `setPass(p)` guarda `pass = p`, pone `m.userData.pass.value = p` en cada
        material y llama a `applyOpacity()`.
    *   `applyOpacity()` pone `m.opacity = baseOpacity * (1 - 0.65 * pass)` en
        cada material.
    *   No hace falta un caso aparte para el placeholder (cápsula): el
        constructor de `Creature` ya reemplaza todos los materiales por
        `makeHologramMaterial`, así que todos tienen `userData.pass`.
*   **Por qué**: la opacidad de "se deja atravesar" se compone con la del
    tracking (`main.js:102`) y con la de la muerte (`events.js:51`), en vez de
    pisarse.

### Verification Plan

*   **Compilation/Build**: no hay build. `python -c "import dejarik.hands,
    dejarik.vision"` tiene que importar sin MediaPipe cargado (se verifica con
    `"mediapipe" not in sys.modules`).
*   **Unit Tests**: `python -m pytest tests` tiene que pasar entero, incluidos
    los tests nuevos de `test_hands.py`, `test_vision.py` y
    `test_protocol.py`.
*   **Static Analysis & Linting**: el repo no tiene linter configurado y no se
    agrega ninguno.
*   **Test Coverage Requirement**: no hay un porcentaje. Cada rama de
    `Confirm.update` (pasos 2, 3, 5, 6 y 7) tiene al menos un test que falla si
    se rompe.
*   **E2E / Manual (control, antes del 16-18/11)**, desde **cada lado** de la
    mesa, con el overlay de debug (tecla D):
    1.  **E0 (antes de tocar código):** 10 toques por anillo con el gesto
        actual. Se anota cuántos caen en la casilla correcta.
    2.  **G1:** 10 toques por anillo con `gesture = "touch"`; tienen que dar
        ≥ 9/10 correctas.
    3.  **G2:** 2 min de juego normal sin confirmaciones falsas. Se calibran
        `[hands.touch] on/off` y `extended_on/off` mirando la línea de debug
        de los 5 estudiantes.
    4.  **G3:** una persona que no conoce el gesto prueba sin explicación y
        tiene que poder decir si se confirmó o se canceló.
    5.  **G4:** la mano sobre una criatura se lee como "la atraviesa", y el
        efecto no se confunde con "Tracking perdido" (se tapa la cámara para
        compararlos).
    6.  **Remoto:** con `--mode remote`, el punto de debug y la caja del
        remoto quedan sobre la mano del video, lo que muestra que el escalado
        funciona.
    7.  **Plan B:** con `gesture = "dwell"` se repite el paso 2. Con
        `--input mouse` se verifica que el mouse sigue andando.
    *   Si el paso 3 falla, se pasa a `dwell`. Si el paso 2 falla con
        cualquier gesto, se decide entre la mano y el puntero ArUco, como ya
        prevé `concepts_brief.md`.

--------------------------------------------------------------------------------

*Drafted with EGM*
