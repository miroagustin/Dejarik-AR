# Interacción con la mano: apuntar con el índice, confirmar con dos dedos y "atravesar" el holograma

*   **Author:** miroagustin
*   **Status:** Implemented (E1-E3). Después de la primera prueba con cámara el gesto por defecto pasó a `dwell` con `hold_ms = 1500` (ver "Cambios después de la prueba").
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

Etapas y fechas:

*   **E0:** medir el gesto actual con el overlay de debug, sin tocar código.
*   **E1:** el gesto nuevo en Python.
*   **E2:** el anillo, los sonidos, el HUD y los docs.
*   **E3:** "se deja atravesar".
*   **E4:** oclusión real, opcional.
*   **El control** es el control 2 del plan general (días 14-16,
    [concepts_brief.md](../briefs/concepts_brief.md)), entre el 16 y el 18/11.
    Ahí los 5 integrantes del equipo miden E1-E3 contra E0.
*   E4 solo entra si E1-E3 cierran antes del **18/11**. El congelamiento es el
    **20/11/2026** y la demo el **26/11/2026**.

El mouse (`--input mouse` / `--input both`) es la entrada de respaldo si la
mano no llega a los criterios.

## The Problem

**Problema 1: el 3D siempre tapa la mano.** El renderer dibuja las criaturas
encima del video sin importar dónde esté la mano. Si un jugador acerca la mano
a una criatura desde arriba, en pantalla parece que la agarra desde abajo. La
escena contradice lo que el jugador está viendo con sus propios ojos.

**Problema 2: la casilla elegida queda corrida.** El pinch pulgar-índice se
mide con la punta del dedo en el aire, a unos 3-4 cm del papel (estimado). La
cámara mira a unos 45°, así que al proyectar ese punto sobre el plano del
tablero cae "altura × tan(45°)" ≈ 3-4 cm más lejos. Eso es una casilla interior
entera o más (~37 mm en dirección radial y ~28 mm de arco, OQ4), así que el
jugador apunta a una casilla y el juego marca otra.

**Por qué importa para la demo.** La mano es lo que hace que la demo se parezca
al dejarik de la película: los jugadores eligen y ordenan, y la mano pasa a
través del holograma sin efecto. Si la casilla queda corrida, el público ve
errores. Si el 3D tapa la mano, el efecto se ve falso. Hoy, en cualquiera de
los dos casos, la alternativa práctica es el mouse.

**La solución en una frase.** Se apunta con el índice apoyado en el papel (con
el dedo en el papel el error de altura baja a lo que hay entre la uña y la
yema, ~5-8 mm), se confirma juntando dos dedos y
sosteniendo 1 s, y las criaturas bajo la mano se vuelven translúcidas para que
la mano se vea a través.

## Goals

Cada goal tiene un criterio que se mide en el control (antes del 16-18/11),
**por separado desde cada lado de la mesa**, contra la línea base E0 (el gesto
actual medido con el overlay de debug).

*   **G1: elegir la casilla correcta.** La casilla sale de la punta del índice
    apoyada en el papel, con tolerancia en el borde para que no parpadee entre
    casillas vecinas.
    *   Criterio: 9 de 10 casillas correctas en cada aro del tablero (interior
        y exterior), desde cada lado.
*   **G2: confirmar sin falsos positivos.** Se junta el medio con el índice
    (ratio 3D `d(8,12)/d(0,9)` sobre `hand_world_landmarks`, con el medio
    estirado) y se sostiene 1 s. La casilla queda fijada al empezar, y el gesto
    se cancela si la punta del índice se aleja más de `cancel_radius_mm`
    (20 mm) del punto donde se fijó.
    *   Criterio: ninguna confirmación falsa en 2 min de juego normal, desde
        cada lado.
    *   Criterio: el gesto dispara una sola vez por intento.
*   **G3: el jugador sabe en qué estado está el gesto.**
    Hay un anillo de carga desplazado al costado de la casilla, para que la mano
    no lo tape. Suenan avisos con `web/audio.js`: uno al empezar y otro al
    cancelar. Al confirmar suenan los sonidos que el juego ya tiene (`select`,
    los eventos, `denied`).
    *   Criterio: en el control, 2 de 3 personas que prueban por primera vez
        dicen, sin explicación, si el gesto se confirmó o se canceló.
*   **G4: las criaturas bajo la mano "se dejan atravesar".** Las criaturas
    cuya base proyectada cae dentro de la caja de la mano (`hand.box`, ver
    OQ1) bajan a una opacidad de ~0,35 y parpadean más, con un fundido de
    ~150 ms. El antebrazo no está cubierto. El efecto tiene que verse distinto
    del fundido de "Tracking perdido".
    *   Criterio: en el control, 2 de 3 personas sin contexto describen la mano
        sobre una criatura como que "la atraviesa", y ninguna la confunde con
        "Tracking perdido".
*   **G5: los umbrales se definen en un solo lugar.** Viven en la sección
    `[hands]` de `config.toml` con claves nuevas. El README y los briefs citan
    las claves sin copiar los números.
*   **G6: siempre hay una salida.** El mouse sigue andando como plan B
    (`--input mouse` / `--input both`), y `gesture = "dwell"` queda listo por
    config.
*   **G7: el gesto tiene un solo nombre.** Se usa una sola frase, **"Apuntá con
    el índice y juntá dos dedos"**: es la constante `HINT` de `hud.js` y se
    copia igual en el README, `docs/rules.md` y el guion.

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
*   **Volver al pinch pulgar-índice.** Queda en el historial de git.
*   **Tracking dentro del replay en esta entrega.** Que el replay corra
    `hands_loop` sobre el JPEG es útil pero no bloquea.

## Open Questions y decisiones

*   **OQ1 (resuelta: opción B).** Se vuelven translúcidas las criaturas cuya
    base proyectada cae dentro de la caja de la mano (`hand.box`), no solo la de
    `hand.cell`. Se acepta que la caja no cubre el antebrazo y que llega 1-2
    cuadros tarde.
*   **OQ2 (abierta: la cierra E1): los valores por defecto de "medio
    estirado".** El Technical Plan
    propone la fórmula `|w12-w0| / |w8-w0|` sobre world landmarks, con
    `extended_on = 0.85` y `extended_off = 0.75`. Los números salen de
    proporciones típicas de la mano (el medio estirado mide como el índice; doblado,
    ~la mitad), no de mediciones. Se confirman en E1 con el valor `medio` de la
    línea de debug. La fórmula anterior, `|w12-w0| / |w10-w0|`, falló en la
    primera prueba desde el lado rojo: con los dedos apuntando a la cámara,
    MediaPipe acorta el medio y lo daba por doblado.
*   **OQ4 (resuelta): el radio de cancelación es 20 mm, medido desde el punto
    donde se fijó el dedo** (sección 3). En el tablero real (`board_spec.json`
    escalado), la casilla interior mide ~37 mm en dirección radial y ~28 mm de
    arco en el medio. La exterior mide ~38 mm radial y ~47 mm de arco. El
    "~4 cm / ~7,8 cm" del brief no coincide con esto. Con 20 mm se absorbe el
    temblor de ~10 mm, y como se mide desde `lock_xy` no depende del tamaño de
    la casilla.
*   **OQ5 (resuelta): el plan B es `gesture = "dwell"`, implementado en E1.**
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
| `"touch"` (por defecto) | `d3(w8,w12) / d3(w0,w9)` si el medio está estirado; si no, `inf` (cuenta como "abierto") | `[hands] on, off` |
| `"dwell"` | `0.0` siempre: se confirma con solo quedarse quieto | ninguno; vale `hold_ms`, y re-arma al moverse (`rearm_on_move`) |

**"Medio estirado"** se calcula como `|w12-w0| / |w8-w0|`: la distancia de la
muñeca a la punta del medio dividida por la distancia de la muñeca a la punta del
índice, que es el dedo que apunta. Con el medio estirado se estima ~1, y doblado
~0,5. Se compara con el índice y no con la propia falange porque, desde el lado
de enfrente, los dos dedos se ven acortados por igual y el ratio no cambia. Para empezar el gesto el ratio tiene que superar
`extended_on`. Una vez empezado, alcanza con que supere `extended_off`, que es
más bajo, para que el temblor cerca del umbral no cancele el gesto.

Que el medio no esté estirado se trata como "mano abierta" (`inf`), no como
"sin mano" (`None`). Así el motivo de la cancelación en el debug distingue
"soltaste" de "se perdió la mano".

### 3. `Confirm`: la máquina de estados

Es una clase nueva en `hands.py` que reemplaza a `Pinch`. Tiene su propia
histéresis, el tiempo de sostén, la casilla fijada y la cancelación por
distancia. No sabe nada de MediaPipe, así que se testea con secuencias
sintéticas. `Pinch` y su test (`tests/test_hands.py:9-19`) se borran:
`hands_loop` era su único uso.

```text
Confirm(on, off, hold_ms, cancel_radius_m, cell_frames, rearm_on_move)
  update(metric, cell, xy, t) -> casilla confirmada | None
  estado: armed, lock_cell, lock_xy, t0, fired, reason, shown
  "Cerrado" para empezar: metric < on. "Abierto" estando fijado: metric > off.
```

En cada cuadro, primero se actualiza `shown` (sección 4) y después se aplica
la primera fila que corresponda:

| Estado | Condición | Pasa a |
|---|---|---|
| cualquiera | `metric None` (sin mano) | libre y armado; si estaba fijado y no había disparado, `reason = "sin mano"` |
| libre, sin armar | `metric > off` | armado |
| libre, armado | cerrado y (`cell None` o `xy None`) | libre; `reason = "afuera"`; queda armado solo si `rearm_on_move` |
| libre, armado | cerrado y `cell != shown` | libre y armado, sin cambiar `reason`: espera a que el resaltado alcance al dedo |
| libre, armado | cerrado | fijado: `lock_cell = shown`, `lock_xy = xy`, `t0 = t`, `fired = False`, `reason = ""` |
| fijado | abierto durante `cell_frames` cuadros seguidos | libre y armado; `reason = "suelta"` si no había disparado |
| fijado | `xy None` o `math.dist(xy, lock_xy) > cancel_radius_m`, durante `cell_frames` cuadros seguidos (mientras tanto no dispara) | libre; `reason = "salió"` si no había disparado; queda armado solo si `rearm_on_move` |
| fijado, sin disparar | `t - t0 >= hold_ms / 1000` | disparado: `update` devuelve `lock_cell`, una sola vez |

*   **La casilla fijada es la resaltada.** `lock_cell` sale de `shown`, la
    casilla que el jugador está viendo, no de la casilla cruda del cuadro.
    Solo se fija cuando el dedo está en la casilla resaltada (`cell ==
    shown`), así no se fija la casilla anterior mientras el debounce alcanza al
    dedo. En `dwell`, después de salir del radio se espera `cell_frames`
    cuadros y se fija la casilla nueva.
*   **El radio se mide desde `lock_xy`**, el punto donde se apoyó el dedo, no
    desde el centro de la casilla. La casilla 0 tiene ~35 mm de radio, así que
    medir desde el centro cancelaría por sí solo un toque cerca del borde. `xy` está
    en metros (`board.py`), y `cancel_radius_m = cancel_radius_mm / 1000`.
*   **Un cuadro suelto no cancela.** Abrir o salir del radio tiene que durar
    `cell_frames` cuadros seguidos. En la primera prueba desde el lado rojo, un
    salto de un cuadro del landmark 8 cancelaba el gesto apenas se fijaba. La
    distancia a `lock_xy` va en `dbg.dist_mm` para calibrar `cancel_radius_mm`.
*   **Un intento** es un ciclo armado → fijado → libre. Después de cancelar o de
    disparar hay que abrir los dedos (o sacar la mano) para volver a armar.
*   **En `dwell`** la métrica nunca abre, así que `rearm_on_move = True`: salir
    del radio ya arma de nuevo. Se elige la pieza, se mueve el dedo al destino y
    se sostiene otra vez, sin sacar la mano.
*   `hold` vale 0 si está libre, 1 si ya disparó o si `hold_ms == 0` (sin
    dividir), y `min(1, (t - t0) / (hold_ms / 1000))` si no.

`hands_loop` llama a `on_tap(...)` con lo que devuelve `Confirm`, nunca con la
casilla del cuadro actual. Si la pose no está ok, `cell` y `xy` son `None`, así
que no se puede empezar ("afuera") y un gesto en curso se cancela ("salió"). El
efecto es el mismo que hoy, donde `on_tap` solo se llama con la pose ok.

### 4. Resaltado estable (tolerancia del borde)

La casilla que se publica en `hand.cell` es:

*   durante el gesto, `lock_cell`, que no se mueve aunque el dedo tiemble;
*   fuera del gesto, la casilla cruda, pero solo cambia cuando la casilla nueva
    se repite `cell_frames` cuadros seguidos (3 por defecto, ~100 ms a
    30 fps). Este debounce no depende del tamaño de la casilla, así que sirve
    igual para los dos anillos.

### 5. Campos de `hand` (protocolo v1, solo se agregan campos)

```text
"hand": {"cell": 7, "pinch": true, "px": [u, v], "hold": 0.62, "box": [u0, v0, u1, v1]}
```

*   `px`: la punta del índice (`lm2d[8]`) en píxeles del cuadro, o `null` sin
    mano.
*   `hold`: progreso del gesto entre 0 y 1. Vale 1 desde que se confirma hasta
    que se suelta. Si baja de un valor menor que 1 a 0, el gesto se canceló.
    Con eso el navegador detecta "empezó", "se confirmó" y "se canceló" sin un
    campo de evento.
*   `box`: la caja de los 21 `lm2d`, agrandada `box_margin` (0,15 por defecto)
    de su ancho y alto por lado, en píxeles del cuadro. Es `null` sin mano.
*   `pinch` sigue existiendo y significa "gesto cerrado". El debug lo usa para
    el color del punto. El nombre queda por compatibilidad con el protocolo v1.
*   `NO_HAND` queda **en un solo lugar** (`hands.py`): `vision.py` lo importa y
    se borra la copia de `vision.py:183`. Importar `hands.py` no carga
    MediaPipe, porque MediaPipe se importa adentro de `HandTracker`.
*   `encode_remote` escala `px` y `box` con `sx, sy`, como ya hace con `K`.
    Esto arregla de paso el bug de `hand.px` sin escalar en el remoto. El
    replay re-codifica el remoto con la misma función, así que queda arreglado
    también.
*   El dict publicado lleva una clave `"dbg"` con `{metric, metric2d,
    extended, hold, lock_cell, reason}`. `metric2d` es `d2(lm8,lm12) /
    d2(lm0,lm9)`, para comparar en E1 el ratio 2D con el 3D. `vision_loop`
    la saca del dict (como hoy saca `pinch_ratio`) y la manda en `debug.hand` solo cuando el overlay está
    activo.

### 6. Config: `[hands]`

```toml
[hands]
gesture = "touch"        # "touch" | "dwell"
on = 0.35                # se calibra con histogramas (E1)
off = 0.45
extended_on = 0.85
extended_off = 0.75
hold_ms = 1000
cancel_radius_mm = 20
cell_frames = 3
box_margin = 0.15
input_width = 640
```

Los `on/off` arrancan como suposición: el valor real sale de E1.

### 7. Navegador

*   **"Se deja atravesar".** Hoy la opacidad de una criatura la escriben dos
    caminos (que entre sí se pisan, y eso no cambia acá): el fundido por
    pérdida de tracking (`main.js:102`) y la muerte (`events.js:51`). `Creature` pasa a guardar dos factores:
    `baseOpacity`, que es lo que escribe `setOpacity` hoy, y `pass` (0..1). La
    opacidad final es `baseOpacity × (1 − 0,65·pass)`, que con `pass = 1` da
    ~0,35. `pass` también va a un uniform nuevo por material, `uPass`, que
    agranda el parpadeo del shader. El look es "parpadeo fuerte y translúcido":
    la opacidad baja a ~0,35 y el parpadeo crece (el brillo promedio baja un
    poco). Se distingue de "Tracking perdido" porque aquel es un fundido parejo
    a 0,2, sin parpadeo extra, con el aviso en el HUD. El destello de golpe (`uFlash`) no se
    toca.
*   **Qué criaturas entran.** En cada cuadro de render, `main.js` proyecta la
    posición de la raíz de cada criatura a píxeles del cuadro, con la
    proyección de `project` (`main.js:84-89`) partiendo de la posición de
    mundo, y la compara con `hand.box`. Las que caen adentro van hacia
    `pass = 1` y las demás hacia 0, con una suavización exponencial como la de
    `poseAlpha` pero más rápida, τ ≈ 0,05 s (~150 ms
    hasta llegar casi al objetivo). Se usa la posición actual de la raíz, no la
    casilla, así una criatura caminando también entra.
*   **Anillo.** Es un `<div>` con `conic-gradient` de CSS, sin canvas ni
    Three.js. Se ubica en el centro proyectado de `hand.cell` más un
    corrimiento fijo arriba a la derecha (ítem 12) para que el dedo no lo
    tape. Se ve mientras `hold > 0`.
*   **Sonidos.** Se agregan dos sonidos a `web/audio.js`: `holdStart` (tic) y
    `holdCancel` (descendente corto). La confirmación **no tiene sonido
    propio**, porque el toque ya dispara los sonidos del juego: `select` al
    elegir, los eventos al mover o atacar y `denied` si no es tu turno. Un
    acorde extra se pisaría con esos. Esto se aparta del brief, que pedía un
    acorde al confirmar.
*   **Pista del gesto en el HUD.** `hud.js` muestra el texto "Apuntá con el
    índice y juntá dos dedos" mientras `hand.px` no es null. El texto sale de
    la constante `HINT` del HUD, no de la config, y es la frase de G7.
*   **Debug.** `debug.js` reemplaza la línea `pinch` por `métrica · medio
    estirado sí/no · hold · fijada N · motivo`, leyendo de `debug.hand`, y
    dibuja `hand.box` como un rectángulo.

### 8. E4: oclusión real (opcional, fuera de este plan)

No se diseña acá. Si E1-E3 cierran antes del 18/11, se escribe un design
corto aparte. Ese design parte de lo que ya dice el brief: medir el desfase,
agregar `frame_id` a `hand`, usar el hull dilatado de 21 puntos, el patrón de
oclusor de `scene.js:54-58` y cuidar el `flipY`. La caja que se agrega en este
plan (`hand.box`) sirve para medir el desfase sin agregar nada más.

## Risks & Mitigations

| Riesgo | Mitigación |
|---|---|
| Una mano abierta o relajada con el medio estirado cuenta como "cerrada" (`on = 0,35` son ~3 cm entre puntas) y empieza el gesto sobre un destino válido. | El paso G2 del control incluye "mano abierta quieta sobre un destino válido". Los histogramas de E1 tienen que separar apuntar, dos dedos juntos y mano abierta. Si no separan: `gesture = "dwell"`. |
| La profundidad de `hand_world_landmarks` la estima el mismo modelo con la misma imagen, así que el ratio 3D puede no ser mejor que el 2D justo con las puntas alineadas a la cámara. | `dbg` registra los dos ratios (`metric` y `metric2d`). Si en E1 el 2D separa mejor, se cambia la métrica antes del 20/11 (una línea). |
| `dwell` confirma cualquier pausa de 1 s sobre una casilla, y al mover la mano suena tic/cancelación. | Es solo el plan B. Los sonidos tienen umbral (`hold` ≥ 0,15, ítem 12), y el paso 7 del control lo prueba. |
| E1 no llega a 9/10 desde algún lado. | `dwell`, después el mouse o el puntero ArUco, como prevé `concepts_brief.md`. |
| La caja no cubre el antebrazo ni el cuerpo de una criatura alta cuya base queda fuera de la caja. | Aceptado (OQ1). |

## Alternatives Considered

Las alternativas A a J salen de la tabla "Alternatives Weighed" del brief. De
la K a la N se descartaron mientras se escribía este draft. Todas las
decisiones son del autor y están registradas en
[hand_interaction_brief.md](../briefs/hand_interaction_brief.md). Abajo va el motivo
técnico de cada una.

### Elegir la casilla

#### A: Estimar la altura de la mano (solvePnP de la mano)

*   **Pros**: funcionaría con el dedo en el aire, sin tocar el papel.
*   **Cons**: mucho trabajo, y depende de un tamaño de mano que el modelo
    estima. Una mano más chica o más grande corre el resultado.
*   **Reason for Rejection**: el dedo apoyado en el
    papel elimina el error de altura sin código nuevo
    (`image_to_board(lm[8])` ya existe), y el costo es solo una regla de uso.

### El gesto de confirmación

#### B: Medio junto al índice medido en centímetros (`hand_world_landmarks`)

*   **Pros**: se explica fácil ("juntá dos dedos") y el umbral se lee en
    unidades físicas.
*   **Cons**: los centímetros los estima el modelo, así que un umbral fijo de
    1,5 cm cambia según la mano y según el ángulo.
*   **Reason for Rejection**: el ratio 3D (alternativa
    elegida) mide lo mismo sin depender de la escala estimada.

#### C: Medio junto al índice con ratio 2D `d(8,12)/d(0,9)` en píxeles

*   **Pros**: reusa el cálculo de `hands.py:92` y es un cambio de una línea.
*   **Cons**: desde el lado cercano, las puntas del índice y del medio se
    alinean con la línea de visión y en 2D parecen juntas aunque no lo estén.
*   **Reason for Rejection**: en 2D, desde el lado cercano, las puntas
    alineadas con la cámara parecen juntas. El ratio 3D no depende de esa
    dirección si el modelo estima bien la profundidad, y E1 lo verifica
    comparando con el 2D (`metric2d`).

#### D: Exigir además anular y meñique doblados

*   **Pros**: filtra la mano relajada, que ya tiene el índice y el medio juntos.
*   **Cons**: agrega otra condición que el modelo tiene que acertar, y a 45° el
    anular y el meñique también quedan tapados.
*   **Reason for Rejection**: en la demo las manos en
    reposo quedan fuera del cuadro. El riesgo que queda (una mano apoyada sobre
    un destino válido mueve la pieza en 1 s) se mide en el control.

#### E: Solo quedarse quieto 1-1,2 s, sin segundo gesto (dwell)

*   **Pros**: es lo más simple y no depende del dedo medio.
*   **Cons**: un apoyo distraído sobre un destino válido mueve la pieza.
*   **Estado**: plan B, no se descarta. Queda implementado
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
*   **Reason for Rejection**: el desfase de 1-2 cuadros y la sincronización del
    `frame_id` no entran en el alcance obligatorio antes del 20/11. Queda como
    E4 opcional, apagada por defecto, solo si E1-E3 cierran antes del 18/11.

#### G: Hull a la profundidad del punto del índice, por lado

*   **Pros**: es lo que se pidió primero: la mano tapa o no según de qué lado
    está.
*   **Cons**: una sola profundidad está mal para los nudillos y el brazo, que a
    45° quedan mucho más cerca de la cámara. Además la profundidad salta cuando
    el dedo se levanta.
*   **Reason for Rejection**: una sola profundidad está mal para los nudillos y
    el brazo, y además requiere enmendar `concepts_brief.md:328`. F, que no
    tiene esos problemas, ya está fuera del alcance obligatorio.

#### H: Máscara por segmentación de píxeles

*   **Pros**: la silueta real, brazo incluido.
*   **Cons**: otro modelo (estimado +10-20 ms por cuadro) y un segundo payload binario
    que rompe el formato `[uint32][header][JPEG]`, los `.dj` y
    `fixtures/session_01.dj`.
*   **Reason for Rejection**: el costo en latencia y en
    protocolo no entra antes del 20/11.

#### I: "Se deja atravesar" solo para la criatura de `hand.cell` (OQ1 A)

*   **Pros**: no agrega campos al protocolo.
*   **Cons**: mientras la mano se acerca, el brazo y los nudillos pasan sobre
    otras criaturas, que se siguen dibujando encima.
*   **Reason for Rejection**: con `hand.box` (un campo
    de 4 números) se cubre la mano entera.

#### J: Caja de la mano estirada hasta el borde por el antebrazo (OQ1 C)

*   **Pros**: cubre también el antebrazo.
*   **Cons**: depende de la dirección `lm9→lm0`, que falla con la muñeca
    doblada, y la caja puede abarcar medio tablero y volver translúcidas
    criaturas lejanas.
*   **Reason for Rejection**: tiene más casos que fallan
    que el antebrazo sin cubrir.

### Decisiones del Technical Plan

#### K: Máquina de estados del gesto en el navegador

*   **Pros**: el anillo y los sonidos reaccionan sin esperar el cuadro siguiente.
*   **Cons**: el toque tendría que volver del navegador a Python, el remoto
    necesitaría la misma lógica y el test necesitaría un navegador.
*   **Reason for Rejection**: `on_tap` ya vive en Python, y `hold` alcanza
    para que el navegador dibuje.

#### L: Envolver `Pinch` con `Confirm` sin cambiarlo

*   **Pros**: deja `Pinch` y su test sin tocar.
*   **Cons**: para cancelar hay que llamar `pinch.update(None)`, y con los dedos
    todavía juntos `Pinch` se vuelve a activar en el mismo cuadro. Re-armar,
    medir el radio desde el punto fijado y el `dwell` necesitarían un caso
    aparte cada uno. `hold` tendría que leer `closed_since` y `min_s`.
*   **Reason for Rejection**: una sola tabla de estados en `Confirm` es más
    corta que esos parches, y `Pinch` no tiene otro uso (`hands.py:79`).

#### M: Reusar `pinch_on/off/ms` con la unidad nueva

*   **Pros**: no hay claves nuevas.
*   **Cons**: una config vieja carga sin error con valores de otra unidad, y
    volver al gesto viejo obliga a cambiar los números a mano.
*   **Reason for Rejection**: claves nuevas con nombres planos en `[hands]`
    (`on`, `off`) evitan que una config vieja cargue con valores de otra unidad.
    Hay un solo `config.toml` y este cambio lo reescribe, así que no hace falta
    un aviso para claves viejas.

#### N: Acorde propio al confirmar

*   **Pros**: avisa de la confirmación aunque el toque no cambie nada en el
    juego (por ejemplo, un toque en una casilla no válida, que deselecciona sin
    sonido).
*   **Cons**: se pisa con `select`, con los sonidos de los eventos y con
    `denied`, que ya suenan al confirmar.
*   **Reason for Rejection**: un acorde se pisaría con los sonidos que ya
    suenan, y se acepta que la deselección quede sin sonido. Esto se aparta
    del brief, que pedía un acorde.

## Additional Resources

*   [hand_interaction_brief.md](../briefs/hand_interaction_brief.md): el brief de
    este design (2026-11-06).
*   [concepts_brief.md](../briefs/concepts_brief.md): el brief general (Non-Goal de
    oclusión en la línea 328, plan de 20 días).
*   [dejarik_ar.md](dejarik_ar.md): el design general (sección "Mano y
    pinch").

## Cambios respecto del brief (decididos por el autor)

1.  **Criaturas translúcidas.** Las elige `hand.box` (OQ1 B), no solo
    `hand.cell`.
2.  **Sonido al confirmar.** No hay acorde propio; suenan los sonidos del juego
    (alternativa N).
3.  **Campos de `hand`.** Son `hold` y `box`. `lock_cell` va solo en
    `debug.hand`, porque durante el gesto `hand.cell` ya vale `lock_cell`.
4.  **Claves de config.** Son `gesture = "touch"|"dwell"` y claves planas en
    `[hands]` (`on`, `off`, `hold_ms`…), en lugar de `confirm_on/off/ms`. El
    pinch pulgar-índice ya no se puede elegir.
5.  **Tiempo del plan B.** `dwell` usa el mismo `hold_ms`. Para ir a 1,2 s hay
    que poner `hold_ms = 1200`.

--------------------------------------------------------------------------------

## Cambios después de la prueba (2026-11-06)

1.  **El gesto por defecto es `dwell`**: se apoya el índice en una casilla y se
    sostiene 1,5 s (`hold_ms = 1500`; primero se probó con 3 s y era mucho). Con `touch` (juntar índice y medio), desde el
    lado rojo el gesto no llegaba a confirmar. `touch` sigue disponible por config.
2.  **La frase del gesto (G7)** pasa a ser "Apoyá el índice en una casilla y
    sostené" (`HINT` en `hud.js`, README, `docs/rules.md` y el guion).
3.  **"Medio estirado"** se mide relativo al índice (`|w12-w0| / |w8-w0|`), y abrir
    o salir del radio tiene que durar `cell_frames` cuadros para cancelar.
4.  **Modo cpu:** el anfitrión juega `[game] cpu_human_side` (por defecto los
    rojos) y la PC abre con los azules.
5.  **El anillo solo arranca sobre una casilla válida** (`Server.hand_cell_ok`, que
    `hands_loop` recibe como `cell_ok`): tu turno, sin animaciones en curso y, en
    `select`, una pieza tuya; en `target`, un destino o ataque legal o una pieza tuya.
6.  **El dibujo no se traba después de una muerte:** la criatura muerta la saca el
    evento `death` al terminar su animación (antes la sacaba el `state`, a veces en
    medio de un clip que entonces no terminaba nunca), `play()` tiene un respaldo
    por tiempo y la cola de eventos sigue si un evento no termina en 8 s.

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
    *   `import math` arriba.
    *   Docstring del módulo: describe "Apuntá con el índice y juntá dos dedos"
        (la frase de G7) en vez de "pinch".
    *   `HandTracker.landmarks(bgr, t) -> (lm2d, lmw) | None`:
        *   `lm2d` es lo de hoy, un array (21, 2) en píxeles de la imagen
            completa;
        *   `lmw` es un array (21, 3) armado con
            `res.hand_world_landmarks[0]` (`p.x, p.y, p.z`).
    *   `def middle_extended(lmw, thresh) -> bool`: devuelve
        `bool(middle_ratio(lmw) > thresh)`, con `middle_ratio = |w12-w0| /
        max(1e-6, |w8-w0|)`, un `bool` de Python y no `np.bool_`, para que
        `json.dumps` lo acepte. `middle_ratio` también va en `dbg.ext`.
    *   `def gesture_metric(gesture, lm2d, lmw, ext_thresh) -> float`:
        *   `"touch"`: `|w8-w12| / max(1e-6, |w0-w9|)` si
            `middle_extended(lmw, ext_thresh)`; si no, `math.inf`;
        *   `"dwell"`: `0.0`;
        *   otro valor: `ValueError` con el nombre recibido.
    *   `def metric_2d(lm2d) -> float`: `|l8-l12| / max(1e-6, |l0-l9|)`, solo
        para el debug (`metric2d`).
    *   `def gesture_params(cfg) -> dict`: `cfg` es la tabla `[hands]`, como hoy
        (`__main__.py:110`). Devuelve `{gesture, on, off, ext_on, ext_off,
        hold_ms, cancel_radius_m, cell_frames, box_margin, rearm_on_move}`.
        *   La config usa `extended_on/off`; el dict los devuelve como
            `ext_on/ext_off`.
        *   `cancel_radius_m = cancel_radius_mm / 1000` y `rearm_on_move =
            gesture == "dwell"`.
        *   Para `"dwell"`, `on`/`off` valen `0.5`/`0.5` (la métrica `0.0`
            queda siempre "cerrada") y `ext_on`/`ext_off` valen `0.0`.
        *   Si `gesture` no es `"touch"` ni `"dwell"`, levanta `ValueError` con
            el nombre recibido, al arrancar el hilo y no en el primer cuadro con
            mano.
    *   `class Confirm`: implementa la tabla de la sección 3, sin una lista de
        pasos aparte.
        *   `__init__(on, off, hold_ms, cancel_radius_m, cell_frames,
            rearm_on_move)`. Estado inicial: `armed=True`, `lock_cell=None`,
            `lock_xy=None`, `t0=None`, `fired=False`, `reason=""`,
            `shown=None`, `cand=None`, `cand_n=0`, `t_last=0`.
        *   `update(metric, cell, xy, t) -> int | None`: guarda `t_last = t`,
            actualiza `shown` y aplica la primera fila de la tabla que
            corresponda. Las distancias se calculan con `math.dist`. Esta es la
            regla de `shown`; la sección 4 describe el efecto:
            *   si está fijado, `shown = lock_cell`;
            *   si no y `cell == shown`, se resetea el candidato;
            *   si no, `cell` es el candidato: se cuentan los cuadros seguidos,
                y al llegar a `cell_frames`, `shown = cell` (`None` también es
                candidato).
            *   El candidato se resetea al fijar.
        *   Propiedades: `active` (`lock_cell is not None`) y `hold` (sección 3,
            calculado con `t_last`).
    *   Borrar `class Pinch`. `transport.py:252` queda como está (solo dice
        "pinch" en un docstring).
    *   `def hand_msg(conf, lm2d, metric, metric2d, extended, box_margin) ->
        dict`, pura, para que se pueda testear:
        *   sin mano (`lm2d None`): `dict(NO_HAND, cell=conf.shown,
            dbg={"metric": None, "metric2d": None, "extended": False,
            "hold": 0, "lock_cell": None, "reason": conf.reason})`;
        *   con mano: `{"cell": conf.shown, "pinch": conf.active, "px":
            [round(float(u), 1), round(float(v), 1)], "hold": round(conf.hold,
            2), "box": [u0, v0, u1, v1], "dbg": {"metric": ..., "metric2d":
            round(float(metric2d), 3),
            "extended": extended, "hold": round(conf.hold, 2), "lock_cell":
            conf.lock_cell, "reason": conf.reason}}`. `box` es el mínimo y el
            máximo de `lm2d`, agrandados `box_margin × (ancho, alto)` por lado y
            redondeados a 0,1 px. `(u, v)` es `lm2d[8]`. Todos los números van
            como `float` de Python, no de numpy (como `hands.py:99` hoy), porque
            `encode_frame` usa `json.dumps` (`protocol.py:14`). En `dbg`,
            `metric` vale `None if math.isinf(metric) else round(float(metric),
            3)`.
    *   `hands_loop(get_packet, publish_hand, on_tap, stop, K, dist, spec,
        cfg)`, misma firma. En su docstring (`hands.py:76-77`), "pinch_ratio"
        pasa a "dbg" y "pinch" a "gesto":
        *   `p = gesture_params(cfg)` y `conf = Confirm(p["on"], p["off"],
            p["hold_ms"], p["cancel_radius_m"], p["cell_frames"],
            p["rearm_on_move"])`.
        *   Por cuadro, sin `lm`: `conf.update(None, None, None, t)`, se publica
            `hand_msg(conf, None, ...)` y `continue` (como `hands.py:88-91`
            hoy).
        *   Por cuadro, con `lm`:
            *   `ext_thresh = p["ext_off"] if conf.active else p["ext_on"]`;
                `extended = middle_extended(lmw, ext_thresh)`; `metric =
                gesture_metric(p["gesture"], lm2d, lmw, ext_thresh)`.
            *   Si `pose.ok`: `xy = image_to_board(*lm2d[8], ...)` y `cell =
                cell_at(*xy, spec)`. Si no, `xy = cell = None`.
            *   `tap = conf.update(metric, cell, xy, t)`; si `tap is not None`,
                `on_tap(tap)`.
            *   Se publica `hand_msg(conf, lm2d, metric, metric_2d(lm2d),
                extended, p["box_margin"])`.
    *   **Por qué**: es G1, G2, G5, G6 y OQ5. `Confirm` es la máquina de
        estados y se puede testear, `gesture_metric` implementa el gesto 3D y
        el plan B, `gesture_params` arma la config de una sola fuente y
        `hand_msg` deja el mensaje publicado testeable.

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
        copia con `px` y `box` multiplicados por `(sx, sy)` cuando
        `hand.get(...)` no es `None`, y el resto igual. Las claves que no están
        no se agregan (los `.dj` viejos no tienen `box`).
    *   **Por qué**: hoy `NO_HAND` está en tres lugares (el brief, `hands.py:14`
        y `vision.py:183`) y queda solo en `hands.py`. Además lleva el debug
        nuevo al overlay y arregla `px` sin escalar en el remoto
        (`vision.py:171-180`); el mismo bug afectaría a `box`.

##### 3. `config.toml` (Modify)

*   **Type / Scope**: configuración.
*   **Proposed Changes**: reemplazar las claves `pinch_on`, `pinch_off` y
    `pinch_ms` de `[hands]` (líneas 36-40) por el bloque del Technical Plan,
    sección 6: las claves planas de `[hands]`.
*   **Por qué**: G5, una sola fuente para los umbrales.

##### 4. `tests/test_hands.py` (Modify)

*   **Type / Scope**: tests unitarios (pytest).
*   **Proposed Changes**: el test de `Pinch` (`test_hands.py:9-19`) se borra
    junto con la clase. El de `image_to_board` queda. Todos los tests de
    `Confirm` lo construyen con `Confirm(0.35, 0.45, 1000, 0.02, 1, False)`
    (`cell_frames=1`, así `shown` alcanza al dedo en el mismo cuadro), salvo
    `test_confirm_debounce` y `test_confirm_dwell_two_taps`, que usan
    `cell_frames=3`. Los tiempos se miden desde el primer cuadro cerrado, que
    es el que fija. `xy = cell_center(c, spec)` con el `spec` escalado de
    `board_spec.json`. Se agregan:
    *   `test_confirm_fires_once_at_hold_ms`: con `cell=5` y `xy=cell_center(5, spec)`
        fijos, la métrica cerrada dispara una sola vez a los 1000 ms y devuelve
        `5`. `hold` sube de 0 a 1 y queda en 1 hasta soltar.
    *   `test_confirm_uses_locked_cell`: empieza en la casilla 5. A los 500 ms
        se pasa `cell=6` sintético con un `xy` a 10 mm de `lock_xy`, todavía
        adentro del radio de 20 mm. Dispara con `5`, no con `6`, y `shown`
        queda en `5` durante todo el gesto.
    *   `test_confirm_cancels_outside_radius`: un `xy` a 30 mm de `lock_xy`
        cancela con `reason == "salió"` y `hold == 0`. Con la métrica todavía
        cerrada no vuelve a fijar. Después de una métrica `> off` y otra vez
        cerrada, fija de nuevo.
    *   `test_confirm_edge_lock`: fijado en la casilla 0 con `xy` a 30 mm de su
        centro, no se cancela y dispara.
    *   `test_confirm_release_reason`: abrir antes de 1 s da `reason ==
        "suelta"`; abrir después del disparo deja `reason == ""`.
    *   `test_confirm_cancels_on_lost_hand`: `metric None` a mitad del gesto da
        `reason == "sin mano"`. Si la mano vuelve ya cerrada, fija sin tener que
        abrir.
    *   `test_confirm_pose_lost`: fijado, un cuadro con `xy None` da `reason ==
        "salió"` sin levantar error.
    *   `test_confirm_ignores_start_off_board`: empezar con `cell None` no
        activa nada y da `reason == "afuera"`. Lo mismo con `cell=5` y `xy
        None` (pose no ok). Para volver a intentar hay que abrir.
    *   `test_confirm_dwell_two_taps`: con `rearm_on_move=True`,
        `cell_frames=3` y la métrica siempre en 0, dispara en 5; el `xy` se
        mueve 30 mm con `cell=6`, y después de 3 cuadros en 6 dispara con `6`,
        no con `5`. Empezar fuera del tablero (`cell None`) lo deja armado.
    *   `test_confirm_hold_ms_zero`: con `hold_ms=0`, fija en un cuadro y
        dispara en el siguiente; `hold` vale 1 desde que fija, sin dividir por
        cero.
    *   `test_confirm_debounce`: fuera del gesto, `shown` cambia de casilla
        recién en el 3er cuadro seguido con la casilla nueva, y un cuadro
        suelto con otra casilla no lo cambia. Cerrado sobre una casilla que
        todavía no es `shown` no fija hasta que `shown` la alcanza.
    *   `test_gesture_metric`: con un `lmw` sintético de la mano abierta y el
        medio estirado, más el índice y el medio juntos, `"touch"` da un valor
        menor que `on`. Con el medio doblado (`|w12-w0| / |w8-w0|` por debajo
        de `extended_off`) da `inf`. `test_middle_extended_from_far_side`: con
        las dos puntas acortadas por igual, el medio sigue estirado. `"dwell"` da `0.0` y un nombre
        desconocido levanta `ValueError`.
    *   `test_gesture_params`: `dwell` da `rearm_on_move` verdadero, y
        `cancel_radius_mm = 20` da `cancel_radius_m == 0.02`.
    *   `test_hand_msg`: `box` con el margen y el redondeo, `metric inf` da
        `None` y `0.0` queda `0.0`. Con `lm2d` y `lmw` de numpy,
        `json.dumps(hand_msg(...))` no levanta error.
*   **Por qué**: cubre el test que pide E1 en el brief (dispara a 1 s, se
    cancela al salir, dispara una sola vez, se cancela si se pierde la mano),
    además de la casilla fijada, el re-armado, el `dwell`, el debounce y la
    config. Se usa el mismo estilo de secuencias `(métrica, casilla, t)` que el
    test de `Pinch` que se borra.

##### 5. `tests/test_vision.py` (Modify)

*   **Type / Scope**: test unitario.
*   **Proposed Changes**: agregar `test_encode_remote_scales_hand`. Con un
    cuadro de 1280×720, `remote_width=640` y `hand = {"px": [100, 50], "box":
    [10, 20, 30, 40], ...}`, el header decodificado tiene `px == [50, 25]` y
    `box == [5, 10, 15, 20]`, y el dict original no cambió. Un segundo caso con
    el `hand` viejo `{cell, pinch, px}` (sin `box`) no levanta error y no
    agrega `box`. `net_cfg = {"remote_width": 640, "remote_quality": 60}`,
    `pose_msg = {"ok": False}` y `k4 = [1000, 1000, 640, 360]`.
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
        "metric2d":0.5,"extended":true,"hold":0.6,"lock_cell":7,"reason":""}`,
        con los valores posibles de `reason`.
    *   La línea 3 pasa a ser: "**Se congela el día 2.** Agregar un campo
        opcional no sube `v`, porque cada lado ignora los campos que no conoce.
        Cambiar o quitar un campo sí: se sube `v` y se cambian Python y el
        navegador en el mismo commit."
*   **Por qué**: E2, y deja escrita la regla que permite no subir `v`.

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
        calc(var(--p) * 1turn), transparent 0)` con `mask: radial-gradient(circle,
        transparent 55%, #000 57%)` para que quede como aro. `--ring` vale
        `var(--blue)`, la variable que ya existe en `style.css:2`.
    *   `#hint`: `bottom: 64px; left: 50%; transform: translateX(-50%)`,
        encima de `#combat` (`style.css:33`), con el mismo estilo de caja que
        los demás `#hud > div`.
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
        *   si `prevHold < 0.15 && hold >= 0.15`: `audio.play("holdStart")`;
        *   si `prevHold >= 0.15 && prevHold < 1 && hold === 0`:
            `audio.play("holdCancel")`;
        *   `prevHold = hold`.
        *   El umbral evita sonidos por fijaciones de menos de 150 ms (con
            `hold_ms = 1000`), sobre todo en `dwell`.
    *   **Anillo:** si `hold > 0`, `h.cell != null` y `lastHeader.pose.ok`, se
        proyecta el centro de la casilla con `project(...cellCenter(spec, h.cell), 0)`. Ese
        punto está en píxeles del cuadro y se pasa a píxeles de `#stage`
        multiplicando por `stage.clientWidth / lastHeader.size[0]`. El centro
        del `<div>` va ahí más `(+40, −40)` px de `#stage` (`left = x + 40 -
        22`, `top = y - 40 - 22`), con `style.setProperty("--p", hold)`. Si no,
        se oculta.
    *   **Pista:** `let prevHint = false`; se llama `hud.hint(show)` solo cuando
        `show = h?.px != null` cambia.
    *   **En el remoto (`you === 1`):** el anillo no se muestra y los sonidos
        de hold no suenan, porque los produce la mano del anfitrión. La pista
        tampoco se muestra.
    *   **E3 ("se deja atravesar"):** después del bloque de `poseAlpha`,
        **siempre**, para cada criatura de `army.byId`: `target = 1` si
        `h?.box`, `lastHeader.pose.ok` y la raíz cae dentro de `h.box`; si no,
        `0`. Después, `c.pass += (target - c.pass) * Math.min(1, dt / 0.05)` y
        `c.setPass(c.pass)`. La raíz se pasa a píxeles con
        `toPx(c.root.getWorldPosition(tmp))`, con `const tmp = new
        THREE.Vector3()` declarado arriba del loop, donde `toPx(v)` es la parte de
        `project` que aplica `projectionMatrix` y convierte de NDC a píxeles;
        `project` pasa a usar `toPx`. Corre también en el remoto, porque el
        video del remoto muestra la misma mano y `box` ya llega escalado.
    *   `main.js:3` pasa a `import { createScene, cellCenter } from
        "./scene.js"`.
*   **Por qué**: G3 y G4. Todo depende de `hand`, sin lógica de gesto en el
    navegador (alternativa K descartada).

##### 13. `web/debug.js` (Modify)

*   **Type / Scope**: overlay de debug.
*   **Proposed Changes**:
    *   La línea 65 pasa a mostrar, desde `dbg.hand`: `mano <metric> (2D
        <metric2d>) · medio estirado|doblado · hold <hold> · fijada <lock_cell>
        · <reason o "ok">`. Los números con `toFixed(2)`, y `—` si son `null`.
    *   Si `hand.box`, se dibuja un `strokeRect` con `strokeStyle =
        "rgba(255,255,255,0.5)"` con esa caja.
*   **Por qué**: lo que pide el brief para calibrar el día de la demo
    (distancia, si el medio está estirado, progreso, casilla fijada y motivo),
    más ver la caja para medir el desfase y para E4.

##### 14. `README.md` (Modify)

*   **Type / Scope**: documentación.
*   **Proposed Changes**:
    *   La línea 73 pasa a ser: "**Turno:** clic, o apuntá con el índice y
        juntá dos dedos (con el índice apoyado en el papel; se sostiene, con un
        anillo de carga) sobre una pieza propia…", y el resto igual.
    *   La línea 80 agrega: "gesto en `[hands] gesture` (`touch` o `dwell`)".
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
    *   En la fila 0:20–1:10, después de "el anfitrión mueve", agregar: "con
        la mano; el narrador dice: «Apuntá con el índice y juntá dos dedos»".
    *   En la tabla de respaldos (línea 38), agregar la fila:
        ``| El gesto da confirmaciones falsas | Pasar al plan B y reiniciar | `gesture = "dwell"` en `config.toml` | — |``
*   **Por qué**: G7 y el plan B listo para usar (OQ5).

##### 17. `docs/designs/dejarik_ar.md` (Modify)

*   **Type / Scope**: design general.
*   **Proposed Changes**:
    *   Debajo del título "### Mano y pinch" (línea 380), una línea: "El gesto
        y su config se reemplazan por `docs/designs/hand_interaction.md`".
    *   El mismo aviso en la lista de config (línea 843).
    *   No se reescribe el resto. Las líneas 415 (esquema de `hand`) y 911
        (`debug.pinch_ratio`) quedan viejas a propósito: el aviso de la línea
        380 las cubre.
*   **Por qué**: evita que haya dos fuentes que se contradicen sobre el gesto.

##### 18. `concepts_brief.md` (Modify)

*   **Type / Scope**: brief general.
*   **Proposed Changes**:
    *   En la línea 164, cambiar "empieza por debajo de 0,25 y termina por
        encima de 0,35" por "con histéresis (`[hands] on/off` en
        `config.toml`)".
    *   Las líneas 160-164 suman una nota: "reemplazado por
        `docs/designs/hand_interaction.md`". Las líneas 98 y 296 (`hand` viejo)
        quedan como están, cubiertas por esa nota.
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
        sin(uTime * 37.0) * sin(uTime * 13.0));`. `uPass` sube la amplitud del
        parpadeo. La frecuencia no cambia, porque cambiarla con `uTime` grande
        hace saltar la fase.
    *   El brillo base y el alfa del borde no cambian.
*   **Por qué**: G4. Más parpadeo además de la opacidad baja, para que no se
    confunda con el fundido parejo de "Tracking perdido".

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
*   **Por qué**: `pass` se compone con la opacidad que ya existe en vez de
    pisarla. El tracking (`main.js:102`) y la muerte (`events.js:51`) siguen
    escribiendo los dos en `baseOpacity`, como hoy.

### Verification Plan

*   **Compilation/Build**: no hay build. `python -c "import sys,
    dejarik.hands, dejarik.vision; assert 'mediapipe' not in sys.modules"`
    tiene que pasar.
*   **Unit Tests**: `python -m pytest tests` tiene que pasar entero, incluidos
    los tests nuevos de `test_hands.py`, `test_vision.py` y
    `test_protocol.py`.
*   **Static Analysis & Linting**: el repo no tiene linter configurado y no se
    agrega ninguno.
*   **Test Coverage Requirement**: no hay un porcentaje. Cada fila de la tabla
    de `Confirm` (sección 3) y el debounce tienen al menos un test que falla si
    se rompen.
*   **E2E / Manual (control, antes del 16-18/11)**, desde **cada lado** de la
    mesa, con el overlay de debug (tecla D):
    1.  **E0 (antes de tocar código):** 10 toques por aro del tablero
        (interior y exterior) con el gesto actual. Se anota cuántos caen en
        la casilla correcta.
    2.  **G1:** 10 toques por aro del tablero con `gesture = "touch"`; tienen
        que dar ≥ 9/10 correctas.
    3.  **G2:** 2 min de juego normal sin confirmaciones falsas, incluida una
        mano abierta quieta 3 s sobre un destino válido. Se calibran `[hands]
        on/off` y `extended_on/off` mirando la línea de debug con la mano de
        cada uno de los 5 integrantes. Para calibrar, cada integrante pone 3
        poses (apuntar, dos dedos juntos y mano abierta) desde cada lado, y de
        la línea de debug se anotan en una tabla `metric` y `metric2d` (mínimo
        y máximo de unos segundos). `on`/`off` van entre "dos dedos juntos" y
        las otras dos. Si los rangos se superponen, se prueba `metric2d` y, si
        tampoco separa, se pasa a `dwell`.
    4.  **G3:** 3 personas que no conocen el gesto prueban sin explicación; 2
        de 3 tienen que poder decir si se confirmó o se canceló.
    5.  **G4:** 3 personas sin contexto miran la mano sobre una criatura; 2 de
        3 la describen como que "la atraviesa", y ninguna la confunde con
        "Tracking perdido" (se tapa la cámara para compararlos).
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
