# Criaturas fieles al canon: clips y roster legible

*   **Author:** miroagustin
*   **Status:** Proposed
*   **Date:** 2026-11-06

--------------------------------------------------------------------------------

## Overview

Dejarik AR es el ajedrez holográfico de Star Wars proyectado sobre un tablero
real, para una demo por Teams: un servidor Python con el motor, un cliente en
el navegador con las criaturas en 3D y entrada por mano o mouse (ver
[el diseño base](dejarik_ar.md)).

Las criaturas del tablero tienen que comportarse como las piezas del dejarik de
las películas, y nada más. Este diseño cubre dos cambios que van en partes
separadas, cada una con su propio plan y sus propios commits:

*   **Parte A, clips.** Los modelos de Quaternius (`assets_src/originals/*.glb`)
    traen 14 clips y hoy usamos 5 (idle, walk, attack, hit, die). La parte A
    recupera los clips y le asigna uno a cada momento que el canon muestra. Los
    que no corresponden a ningún momento del canon quedan sin usar a propósito.
    También hace que el mixer avance de a pasos (unos 12 fps) para que el
    movimiento se vea como stop-motion. Son los commits 1 y 2.
*   **Parte B, roster legible.** Saca el `#roster` de arriba a la izquierda
    (`web/hud.js:24-26`, `web/style.css:44`) de la esquina donde lo pisa el
    texto del canvas de debug. Es un cambio solo de CSS. Es el commit 3.

Las dos partes no comparten código. La parte B no espera a la parte A: si el
roster se complica, los clips se entregan igual.

Regla del autor: **el canon de Star Wars es la única fuente de verdad.** El
canon muestra que los jugadores dan órdenes, las piezas pelean, la que gana le
pega a la que pierde y levanta los brazos, la que pierde desaparece, el
movimiento es duro (stop-motion) y el holograma es translúcido y parpadea.
Ninguna fuente canon muestra piezas que reaccionan a los jugadores.

## The Problem

**Clips.** El público tiene que entender quién ganó un intercambio mirando las
piezas. Hoy eso falla en dos lugares:

1.  **Falta el gesto del ganador.** Es el único momento del canon que no tiene
    animación. Después de una pelea, el sobreviviente vuelve a idle y no hace
    nada que marque que ganó.
2.  **El contraataque se ve al revés.** Con el resultado `counter`, el motor
    resta vida al atacante (`dejarik/game.py:117-123`), o sea que el defensor
    pegó. La animación tiene que mostrar al defensor pegando y al atacante
    recibiendo el golpe. Si no, el espectador ve un golpe que no dio nadie.

Además, el movimiento suave del mixer a 60 fps no se parece al stop-motion de la
película. Esto afecta a todas las criaturas en todos los clips.

El borrador original buscaba usar los 14 clips. Eso choca con la regla del
canon: obliga a inventar reacciones (decir "no", agacharse, girar hacia el dedo)
y a crear eventos y campos de protocolo que no existen. Por eso el objetivo pasa
a ser **"cada momento del canon tiene su clip"**, no "usar los 14".

**Roster.** La vida de cada pieza solo se ve en `#roster`, y el canvas de
debug la tapa. Durante la demo, ni el operador ni el público pueden leer cuánta
vida le queda a cada pieza. Mostrar la vida no es canon (el tablero de la
película no la muestra). Es una ayuda de interfaz, igual que el roster, y se
justifica como tal.

## Goals

*   **G1. Cada momento del canon tiene clip:** moverse, atacar, recibir el
    golpe, morir y desaparecer. Además, cuando una pelea termina con una
    muerte, el sobreviviente hace un gesto de victoria (Wave o Yes; ninguno es
    brazos arriba, ver Open Questions). En las peleas sin muerte, el par
    attack/hit ya muestra quién ganó.
*   **G2. `counter` se ve como lo resuelve el motor:** pega el defensor y el
    atacante recibe el golpe.
*   **G3. Movimiento stop-motion:** el mixer avanza de a pasos de unos 12 fps en
    todas las criaturas.
*   **G4. La vida se puede leer sin que la tape el debug,** con el tracking
    funcionando y con la imagen espejada (`#stage.mirror`). Ver el control del
    commit 3.
*   **G5. Los tiempos no cambian para el jugador:** por cada evento, el cliente
    anima y responde `anim_done`; el servidor espera hasta 5 s
    (`config.toml:67`) y mientras tanto la entrada queda bloqueada
    ("Esperá…"). Una pelea con muerte, más el gesto de victoria, entra en esa
    espera sin que se dispare el timeout de 8 s del cliente (`events.js:68`).
*   **G6. Criterio de demo:** 2 de cada 3 personas que lo ven por primera vez
    dicen quién ganó una pelea con muerte solo mirando la animación, y ninguna
    animación queda trabada en 5 partidas completas.
*   **G7. Rollback barato:** cada commit se revierte solo. Como el servidor lee
    `web/` del disco en cada pedido (`dejarik/transport.py:57-70`), `git
    revert` y recargar la página alcanza, sin reiniciar.

## Non-Goals

*   **Usar los 14 clips como cuota.** Duck, No, Jump, Jump_Idle, Jump_Land,
    Run, Weapon y el que pierda entre Wave y Yes quedan sin usar. Cada uno
    lleva una línea en `assets_src/SOURCES.md` con el motivo canon.
*   **Reacciones de la pieza al jugador:** girar hacia el dedo, quejarse por
    inactividad, decir "no".
*   **Atar las criaturas a `hold`.** `hold` maneja solo el anillo de espera.
*   **Cambiar reglas o protocolo para justificar un clip** (por ejemplo,
    agregar `margin` para Weapon).
*   **Modelos nuevos o diseños de criaturas de las películas.** Siguen los
    modelos CC0 de Quaternius.
*   **Reacción en `tie`.** El empate sigue sin animación propia. Agregarla sería
    una licencia, no canon.

## Open Questions

*   **Clip de victoria:** Wave o Yes. Wave se puede leer como "hola/chau" (y en
    el gesto argentino, como "no"). Yes es un cabeceo. Ninguno es exactamente
    brazos arriba. Decide el autor en el ensayo, mirando los dos en el visor
    (`?viewer=<kind>`) a escala real y por Teams. Si ninguno se lee bien,
    `WIN_CLIP = null` y no hay gesto.
*   **Cómo se mide G6:** quién convoca a las personas, cuántas, y si cuenta un
    ensayo con replay (`--replay fixtures/session_01.dj`) o solo partidas en
    vivo.

## Critical User Journeys (CUJs)

En este doc, "resultado" es lo que decide el motor en un ataque (`hit`,
`counter` o `tie`), "evento" es lo que llega a la cola del cliente (`attack`,
`hit`, `death`, `win`) y "clip" es la animación.

### CUJ 1: Golpe que mata

*   **Given**: partida en curso, tracking OK. El soldado azul (2 HP) está al
    lado de la bestia roja (1 HP).
*   **When**: el jugador azul ataca con el soldado y sale el resultado `hit`.
*   **Then**: el soldado hace el clip `attack`, la bestia hace `hit` y después
    `die` con fade. Cuando arranca el fade, el soldado hace el gesto de
    victoria y vuelve a `idle`. El jugador rojo puede jugar sin esperar a que
    termine el gesto.

### CUJ 2: Contraataque

*   **Given**: igual que el CUJ 1.
*   **When**: sale el resultado `counter`.
*   **Then**: la **bestia** (el defensor) hace el clip `attack` y el soldado
    hace `hit`. El soldado no hace `attack`.

### CUJ 3: Fin de partida

*   **Given**: el rojo tiene una sola pieza viva y le queda 1 HP.
*   **When**: el azul la mata.
*   **Then**: el sobreviviente hace el gesto en el handler `death`. Después, en
    el handler `win`, las demás piezas azules vivas hacen el gesto (el
    sobreviviente lo sigue sin reiniciar) y aparece el banner `GANA AZUL`.

## Technical Plan (Architecture)

### Parte A: clips

#### A1. Assets: conservar todos los clips

Los cuatro originales traen los mismos 14 clips con el prefijo
`CharacterArmature|` (medido sobre `assets_src/originals/*.glb`). Hoy
`rename_clips` (`tools/adapt_glb.py:31-44`) se queda con 5 y descarta el resto
de la lista `animations` del JSON.

Cambio: `rename_clips` sigue renombrando los 5 del contrato (`idle`, `walk`,
`attack`, `hit`, `die`) con `CLIP_NAMES` (attack sale de Punch, hit de
HitReact y die de Death) y **conserva los demás**, con el nombre corto en
minúscula (`duck`, `jump`, `jump_idle`, `jump_land`, `no`, `run`, `wave`,
`weapon`, `yes`). El script no decide qué significa cada clip.
`check_glb.CLIPS` sigue siendo el mínimo de 5, sin cambios.

El tamaño no es un riesgo: `adapt` ya copia el buffer binario entero, así que
los datos de los 14 clips ya están en los `.glb` de hoy; conservarlos solo
agrega entradas al JSON. El límite de 5 MB (`check_glb.py:17`) queda lejos.

Los originales ya están en `assets_src/originals/` (CC0), así que el pipeline
se puede reproducir.

#### A2. El clip de victoria

`Creature` crea una acción por **cada** clip del glTF, no solo por los de
`CLIPS`. En `creatures.js` una constante, `WIN_CLIP = "<wave|yes>"`, dice cuál
es el gesto de victoria; cambiar de Wave a Yes es tocar esa línea.
`Creature.celebrate()` reproduce esa acción sin devolver la promesa. Si la
acción no existe (cápsula de reemplazo, que es la figura que se dibuja cuando
falta el `.glb`, o `WIN_CLIP = null`), no hace nada. La primera vez que falta
un clip, `play()` hace un `console.warn`, así se nota en el ensayo si la
cápsula está en uso.

Los clips que no terminan en loop quedan clavados en su último cuadro
(`clampWhenFinished`). El gesto de victoria tiene que volver a `idle` cuando
termina, pero **solo si en el medio no arrancó otro clip** (por ejemplo, si el
jugador ya movió esa pieza). Si no se chequea eso, el `idle` le pisaría el
`walk`.

#### A3. Victoria después de cada muerte

```text
cola de eventos (events.js)
  attack  ──► guarda fight = { atacante, defensor }
  hit     ──► (igual que hoy)
  death   ──► die + fade de la que pierde
              └─► sobreviviente = el de fight que no murió
                  sobreviviente.celebrate()   ← sin await
  win     ──► cada criatura viva con owner == winner: celebrate()
              hud.win(...)
```

*   **Quién ganó la pelea.** El evento `death` trae `piece` y `from`, pero no
    dice quién lo mató. El handler `attack` ya busca al defensor
    (`events.js:28`), así que guarda la pareja en una variable de la cola.
    `death` toma de esa pareja al que no murió y la limpia al terminar. Los
    eventos de una misma pelea llegan siempre juntos y en orden
    (`game.py:119-125`), así que la pareja no queda vieja.
*   **Sin `await`.** El gesto arranca al mismo tiempo que el fade (0.6 s) y
    dura 1.67 s. Como `death` no lo espera, el `anim_done` sale apenas termina
    el fade y la entrada no queda bloqueada más que hoy. Si sí se esperara, el
    handler `death` duraría unos 2.6 s (die 0.75 + crossfade 0.2 + gesto 1.67,
    que tapa al fade de 0.6). Eso entra en los 5 s del servidor, pero suma
    alrededor de 1.1 s de "Esperá…" en cada muerte.
*   **`owner` en la criatura.** El constructor de `Creature` ya recibe
    `owner` (`creatures.js:48`), pero no lo guarda. Se guarda en
    `this.owner`, y así el handler `win` puede elegir a los ganadores.

#### A4. Contraataque corregido

En el handler `attack`, si `e.result.outcome === "counter"`, hace `attack` el
**defensor** en vez del atacante. Los dos se siguen mirando como hoy. El
evento `hit` que viene después ya apunta al atacante (`game.py:121`), así que
no hay que tocar nada más. Con los resultados `hit` y `tie` todo queda igual.

#### A5. Mixer a pasos (stop-motion)

Hay un solo reloj de pasos: `tick = Math.floor(performance.now() / 1000 /
STEP)`, con `STEP = 1/12` s. `Army.update` (`creatures.js:174`) llama a
`mixer.update` de cada criatura solo cuando `tick` cambia, con el tiempo
transcurrido desde el último paso, así todas cambian de pose en el mismo
cuadro. El `tween` de `walkTo` (`creatures.js:107`) calcula `t` con el tiempo
de ese mismo `tick`, así el cuerpo y las patas saltan juntos. Se cuantizan la
posición y el giro de la pieza. El flash del golpe, los fades y la sacudida
siguen suaves: son efectos del holograma, no movimiento de la pieza. El
render y el parpadeo del holograma siguen a 60 fps.

`FADE = 0.2` queda como está: a 12 fps son 2 o 3 cuadros de transición, que
alcanza para que no haya saltos de pose sin perder la sensación de golpe seco.
`STEP` y `FADE` son constantes que se ajustan en el ensayo.

El visor (`?viewer=<kind>`) usa el mismo reloj, para que lo que se elige ahí
se vea igual que en el juego.

#### A6. Visor con todos los clips

El visor (`main.js:193`) arma un botón por cada acción que tiene la criatura
(`Object.keys(creature.actions)`), en vez de la lista fija de 5. Así se
comparan Wave y Yes a escala antes de llenar `WIN_CLIP`.

### Parte B: roster legible con debug

Opción elegida por el autor: **solo CSS**. No hay etiqueta flotante sobre las
piezas.

**Por qué choca hoy.** El debug escribe sus líneas de estado (fps, pose,
tiempos, mano) arriba a la izquierda de la pantalla, con o sin espejo
(`debug.js:15-22`, desde y = 24 px del cuadro y bajando 24 px por línea). En
la misma esquina están `#role` (`top: 12px`) y `#roster` (`top: 64px`,
`style.css:44`). Con el debug encendido, el texto de las dos capas se pisa.

**Cambio.** `#roster` pasa a la esquina de abajo a la izquierda
(`bottom: 18px; left: 12px`). Esa esquina está libre: `#combat` y `#hint`
están centrados abajo y `#remote` está arriba a la derecha. `#roster` está en
`#hud`, que queda fuera de `#stage`, así que el espejo no lo da vuelta y no
hay que tocar nada en JS.

**Qué se conserva.** El roster sigue mostrando las 8 piezas (4 tipos por
lado), la barra de vida y las muertas tachadas (`.dead`). El roster no se
borra, así que las piezas muertas siguen a la vista (tachadas).

La vida sigue en una lista aparte, lejos de las piezas. G4 pide que se pueda
leer sin que la tape el debug, y eso se cumple. No pide que se lea sobre la
pieza. Los demás límites están en Riesgos y mitigaciones.

## Alternatives Considered

### Clips

#### Alternativa A: mapa completo de 14 clips (borrador original)

*   **Pros**: usa todo el material del pack. Cada clip tiene un rol, así que
    no queda nada "desperdiciado".
*   **Cons**: hay que inventar comportamientos que el canon no muestra (No,
    Duck, girar hacia el dedo). Necesita eventos que no existen: "movimiento
    ilegal" y "selección cancelada" no se emiten (`game.py:127-129`), y para
    el cliente son el mismo cambio de `selected` a null. Weapon por margen
    necesita un campo `margin` nuevo en el protocolo, y además el daño
    siempre es 1 (`game.py:122`), así que un golpe "más fuerte" mostraría
    algo falso. Duck en `counter` contradice al motor, porque en `counter` el
    defensor pega. Encima suma una máquina de estados atada al ruido de la
    mano: con un dwell nervioso, las criaturas saltarían en vivo.
*   **Reason for Rejection**: Contradice la regla "solo canon" y necesita
    eventos y campos de protocolo nuevos solo para justificar clips
    ([brief](../briefs/concepts_brief_personajes.md)).

#### Alternativa B (elegida): conservar todos los clips y usar solo los del canon

Ver A1-A5.

#### Alternativa C: salto al seleccionar como ayuda de interfaz

*   **Pros**: se puede defender si se presenta como UI. Da una señal visible
    sobre la pieza elegida.
*   **Cons**: hace lo mismo que el resaltado de casilla que ya existe
    (`main.js:166`). Necesita una capa de postura (`stance`) por criatura,
    porque la selección llega por `state` y el combate por la cola de
    eventos: los handlers que terminan en `idle` (`events.js:31,43`) pisarían
    el loop y `army.sync` lo perdería al reconectar. Además, Jump_Idle deja a
    la criatura colgada en el aire con las piernas recogidas durante
    segundos.
*   **Reason for Rejection**: Duplica el resaltado de casilla que ya existe y
    obliga a una capa de postura por criatura. Pasa a Future Improvements.

#### Alternativa D: agregar solo el clip de victoria a `CLIP_NAMES`

*   **Pros**: el diff más chico. Una entrada más en `CLIP_NAMES` y en `CLIPS`.
*   **Cons**: para elegir entre Wave y Yes hay que regenerar los 4 `.glb` dos
    veces, o abrir los originales con otra herramienta, porque el visor solo
    muestra lo que adapt dejó. Cada clip que se sume después vuelve a tocar
    adapt, check_glb, el contrato de `docs/assets_checklist.md` y los tests.
*   **Reason for Rejection**: Elegir el clip obliga a regenerar los `.glb`;
    conservar todos cuesta lo mismo una sola vez
    ([brief, etapa 1](../briefs/concepts_brief_personajes.md)).

#### Alternativa E: gesto de victoria con `await`

*   **Pros**: el gesto nunca queda cortado por el movimiento siguiente, porque
    la entrada sigue bloqueada mientras dura.
*   **Cons**: suma alrededor de 1.1 s de "Esperá…" en cada muerte (ver A3).
    Entra en los 5 s del servidor (`config.toml:67`), pero el margen es menor
    si el render anda lento.
*   **Reason for Rejection**: Suma alrededor de 1.1 s de "Esperá…" en cada
    muerte a cambio de que el gesto no se corte
    ([brief, decisión 2](../briefs/concepts_brief_personajes.md)).

#### Alternativa F: hornear los pasos en los samplers del glTF (adapt)

*   **Pros**: el stop-motion queda en los datos y no hace falta código en el
    mixer.
*   **Cons**: no cuantiza el `tween` de `walkTo`, así que el cuerpo seguiría
    deslizándose suave. Para ajustar `STEP` en el ensayo hay que regenerar los
    4 modelos.
*   **Reason for Rejection**: No resuelve el desplazamiento y hace lento el
    ajuste en el ensayo.

### Roster

#### Alternativas descartadas: etiquetas sobre las piezas u ocultar el roster

*   **Etiqueta solo en las dos piezas que pelean.** Fuera de la pelea no se ve
    la vida de nadie. Necesita proyección por cuadro en `#hud` con la x
    espejada a mano, porque `#stage.mirror` daría vuelta el texto
    (`style.css:19`), y un momento para ocultarla que hoy no existe como
    evento.
*   **Etiquetas siempre visibles en las 8 piezas.** Con el ángulo de la cámara
    las etiquetas se enciman y chocan con el anillo de espera (±40 px,
    `main.js:125`). Hay que ocultarlas sin tracking y desvanecerlas con la
    muerte. El tablero del canon no muestra vida.
*   **Ocultar `#roster` salvo con el debug, o cambiarlo por un contador de
    muertas.** Sin debug, el público no ve la vida; el contador pierde la vida
    de las piezas vivas.
*   **Reason for Rejection**: La opción elegida (mover `#roster` con CSS)
    cumple G4 con una línea y sin JS nuevo; las etiquetas suman proyección por
    cuadro con espejo a mano, y ocultar el roster no cumple G4.

--------------------------------------------------------------------------------

## Riesgos y mitigaciones

| Riesgo | Mitigación | Respaldo en vivo |
| --- | --- | --- |
| El gesto de victoria no se lee bien a escala | Se elige en el ensayo (checklist) | `WIN_CLIP = null` y recargar |
| Los pasos de 12 fps tiemblan en la captura de Teams (15-30 fps) | Ajustar `STEP` mirando el share desde otra cuenta | Revertir el commit 2 |
| El gesto pisa un `walk` o queda clavado | `celebrate()` vuelve a idle solo si `this.current` sigue siendo el gesto | Revertir el commit 2 |
| `fight` queda viejo | Se limpia al final de `death` | — |
| El roster tapa marcadores del debug, o `#errors` (`style.css:70`, abajo a la izquierda) tapa el roster | Se acepta: el debug es solo del operador y un error de JS es lo más importante | Mover `#roster` en `style.css` |

## Non-Functional Requirements

*   **Rendimiento:** el mixer a pasos hace menos trabajo que hoy: 12
    actualizaciones de pose por segundo en vez de 60. Conservar los 14 clips
    suma 9 `clipAction` por criatura (72 en total). Mientras no suenan,
    quedan inactivas y no cuestan nada por cuadro.
*   **Rollout y rollback:** tres commits que se revierten por separado
    (assets, canon, roster).
*   **Seguridad:** sin cambios. No se toca el protocolo ni el servidor.

--------------------------------------------------------------------------------

## Additional Resources

*   [concepts_brief_personajes.md](../briefs/concepts_brief_personajes.md): el brief
    de origen.
*   [docs/assets_checklist.md](../assets_checklist.md): el contrato de
    assets.
*   [docs/designs/dejarik_ar.md](dejarik_ar.md): el diseño base
    (su G3, combate animado).
*   [assets_src/SOURCES.md](../../assets_src/SOURCES.md): origen y licencia de los
    modelos.

## Future Improvements

*   **Salto al seleccionar, como UI** (alternativa C). Necesita la capa de
    postura (`stance`). Va solo si sobra tiempo antes del freeze (bastante
    antes del 2026-11-26, fecha de la demo).
*   **Run para movimientos de 2 casillas.** Necesita pasar por la casilla del
    medio (`walkTo` va en línea recta) y una velocidad propia.

--------------------------------------------------------------------------------

## Detailed Implementation Plan

Son tres commits y van en este orden. Después de cada uno el juego sigue
andando, y cada uno se puede revertir solo.

### Commit 1: assets (en el juego no cambia nada)

#### 1. `tools/adapt_glb.py` (Modify)

*   **Type / Scope**: herramienta del pipeline (Python).
*   **Proposed Changes**: `rename_clips(gltf)` sigue renombrando los 5 clips
    del contrato con `CLIP_NAMES`, como hoy. Las animaciones que no usó **se
    conservan**, con el nombre corto (lo que va después del último `|`) en
    minúscula, en el orden de origen. Si el nombre ya está en la salida, el
    clip se saltea. La firma no cambia: sigue devolviendo la lista de clips
    que faltan. En el docstring del módulo, "descarta el resto" pasa a
    "conserva el resto en minúscula".

#### 2. `tests/test_check_glb.py` (Modify)

*   **Type / Scope**: test unitario (pytest).
*   **Proposed Changes**:
    *   En `test_adapt_renames_scales_and_grounds`, la línea 81 pasa a esperar
        `CLIPS + ["dance"]`, porque ahora `Armature|Dance` se conserva.
    *   Test nuevo, `test_adapt_keeps_extra_clips`: el origen trae los 5 del
        contrato más `A|Wave` y `A|Yes`; el resultado tiene los 5 más `wave`
        y `yes`, y `check()` devuelve la lista vacía.

#### 3. `web/creatures.js`, solo las acciones (Modify)

*   **Type / Scope**: cliente.
*   **Proposed Changes**: el constructor de `Creature` recorre
    `gltf.animations` en lugar de `CLIPS` y crea una acción por cada clip.
    `LOOPING` sigue siendo `{idle, walk}`. Se borra `CLIPS`, porque no se usa
    en ningún otro archivo de `web/`. La cápsula de reemplazo no cambia. Va
    en este commit porque el visor (punto 4) lo necesita.

#### 4. `web/main.js`, el visor (Modify)

*   **Type / Scope**: cliente, solo `runViewer`.
*   **Proposed Changes**: la lista fija de la línea 193 pasa a ser
    `Object.keys(creature.actions)`, o sea, un botón por cada clip que tenga
    el modelo.

#### 5. `web/assets/creatures/{guardian,bestia,acechador,soldado}.glb` (Modify)

*   **Type / Scope**: assets binarios regenerados.
*   **Proposed Changes**: se regeneran con `python tools/adapt_glb.py
    assets_src/originals/<kind>_<Monstruo>.glb
    web/assets/creatures/<kind>.glb`. Cada uno queda con 14 clips.
    `check_glb` tiene que dar 0 errores y ningún archivo puede pasar de 5 MB.
    Se espera que pesen lo mismo que hoy, unos 0.5 MB.

#### 6. `assets_src/SOURCES.md` (Modify)

*   **Type / Scope**: documentación.
*   **Proposed Changes**:
    *   La última columna de la tabla lista los 14 clips conservados, y se
        agrega la ruta del original en `assets_src/originals/`.
    *   Sección nueva, "Clips sin usar a propósito", con una línea por clip y
        su motivo canon:
        *   `duck`: en el canon, el que pierde recibe el golpe, no lo esquiva.
        *   `no`: las piezas no reaccionan a los jugadores.
        *   `jump`, `jump_idle` y `jump_land`: en el canon no hay saltos. El
            salto al seleccionar es UI y queda para después.
        *   `run`: el canon no muestra piezas corriendo; el `walk` alcanza
            para 2 casillas.
        *   `weapon`: el daño es siempre 1, así que no hay un golpe "más
            fuerte" que mostrar.
        *   El que pierda entre `wave` y `yes` (se completa en el commit 2).

#### 7. `docs/assets_checklist.md` y `docs/designs/dejarik_ar.md` (Modify)

*   **Type / Scope**: documentación del contrato.
*   **Proposed Changes**:
    *   `assets_checklist.md` línea 37: "descarta los demás" pasa a "conserva
        los demás en minúscula".
    *   `assets_checklist.md` líneas 25 y 85: los 5 nombres siguen siendo el
        **mínimo** obligatorio, y se aclara que los demás clips son
        opcionales.
    *   `assets_checklist.md` línea 104: "los 5 clips" pasa a "todos los
        clips".
    *   `dejarik_ar.md:91`: "los 5 clips" pasa a "al menos los 5 clips del
        contrato".

**Control del commit 1:** pasa `pytest`, `check_glb` da 0 errores en los 4
modelos y el visor de cada tipo muestra 14 botones. En el juego no cambia
nada.

**Paso manual entre el commit 1 y el 2:** el autor mira `wave` y `yes` en
`?viewer=<kind>&still` para los 4 tipos y elige uno. El que elija va en
`WIN_CLIP` (commit 2).

### Commit 2: canon (victoria, contraataque y stop-motion)

#### 8. `web/creatures.js` (Modify)

*   **Type / Scope**: cliente.
*   **Proposed Changes**:
    *   `WIN_CLIP = "<clip elegido>"` y `STEP = 1/12`. `FADE` queda en 0.2.
        `Creature` guarda `this.owner = owner` (ver A3).
    *   `play(name)`: igual que hoy, más un `console.warn` la primera vez que
        falta un clip (un `Set` a nivel de módulo evita repetirlo).
    *   `celebrate()`: si `this.current` ya es la acción del gesto, no hace
        nada (así `win` no reinicia el gesto que arrancó en `death`). Si no,
        reproduce `WIN_CLIP` y vuelve a `idle` al terminar solo si
        `this.current` sigue siendo esa acción. No devuelve la promesa (ver
        A2).
    *   `stepTime()` (exportado): devuelve `Math.floor(performance.now() /
        1000 / STEP) * STEP`. `Army.update` y `walkTo` la usan (ver A5).

#### 9. `web/events.js` (Modify)

*   **Type / Scope**: cliente, cola de eventos.
*   **Proposed Changes**:
    *   Variable nueva `fight = null` dentro de `createEventQueue`.
    *   `attack(e)`: después de que los dos se miran, guarda
        `fight = { atk: c, def: target }`. Si `e.result.outcome` es
        `"counter"` y `target` existe, pega `target` (attack y después idle).
        Si no, pega `c`, como hoy. El sonido `attack` suena en los dos casos.
    *   `death(e)`: después de `await c.play("die")` y **antes** del fade,
        busca al sobreviviente: el miembro de `fight` que no es `c`. Si
        existe y sigue en `army.byId`, llama a `celebrate()`. Después sigue el
        fade como hoy y al final pone `fight = null` (ver A3).
    *   `win(e)`: además de lo que hace hoy, cada criatura de `army.byId` con
        `owner === e.result.winner` llama a `celebrate()`.

#### 10. `web/main.js`, el visor (Modify)

*   **Type / Scope**: cliente.
*   **Proposed Changes**: `runViewer` actualiza el mixer con `stepTime()`
    igual que `Army.update`, así el visor se ve igual que el juego.

#### 11. `assets_src/SOURCES.md` (Modify)

*   **Type / Scope**: documentación.
*   **Proposed Changes**: el clip que no se eligió entre `wave` y `yes` pasa a
    "Clips sin usar a propósito" con su motivo.

**Control del commit 2:**

*   Los CUJs 1 a 3 con click del mouse. El replay (`--replay`) solo reproduce
    la cámara y la mano, no trae combates.
*   Para CUJ 2, jugar con mouse hasta que salga un `counter`.
*   En 5 partidas completas no puede aparecer en la consola
    `"evento sin terminar en 8 s"`.

### Commit 3: roster

#### 12. `web/style.css` (Modify)

*   **Type / Scope**: estilos.
*   **Proposed Changes**: en la línea 44, `top: 64px` pasa a `bottom: 18px`.
    `left: 12px` y el resto quedan igual.

**Control del commit 3:** con el debug encendido (tecla D), y con el espejo
encendido y apagado (tecla F), el roster no se pisa con el texto de estado
del debug ni con `#role`. Los marcadores del debug y `#errors` pueden taparlo
(ver Riesgos y mitigaciones).

### Verification Plan

*   **Compilation/Build**: no hay build (JS sin bundler, Python sin
    compilar).
*   **Unit Tests**: `pytest`, que incluye los tests de adapt nuevos y los
    modificados.
*   **Static Analysis & Linting**: lo que el repo ya usa. No se agrega nada.
*   **Assets**: `python tools/check_glb.py web/assets/creatures/guardian.glb
    web/assets/creatures/bestia.glb web/assets/creatures/acechador.glb
    web/assets/creatures/soldado.glb` da 0 errores.
*   **E2E manual**: los CUJs 1 a 3 con mouse, `?viewer=<kind>` para los 4
    tipos, y debug y espejo para el roster.
*   **Ensayo (checklist)**: elegir Wave o Yes en el visor a escala; ajustar
    `STEP` mirando el share de Teams; mirar el roster con la cámara real
    encuadrada.
*   **Demo (G6)**: queda sujeta a la pregunta abierta sobre cómo se mide G6.

--------------------------------------------------------------------------------

<!-- Provenance: Indicates initial structural drafting via EGM. -->

*Drafted with EGM*
