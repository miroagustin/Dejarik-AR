# Criaturas fieles al canon: clips y etiqueta de vida

*   **Author:** miroagustin
*   **Status:** Draft
*   **Date:** 2026-11-06

--------------------------------------------------------------------------------

## Overview

Las criaturas del tablero tienen que comportarse como las piezas del dejarik de
las películas, y nada más. Este diseño cubre dos cambios que van en partes
separadas, cada una con su propio plan y sus propios commits:

*   **Parte A, clips.** Los modelos de Quaternius (`assets_src/originals/*.glb`)
    traen 14 clips y hoy usamos 5 (idle, walk, attack, hit, die). La parte A
    recupera los clips y le asigna uno a cada momento que el canon muestra. Los
    que no corresponden a ningún momento del canon quedan sin usar a propósito.
    También hace que el mixer avance de a pasos (unos 12 fps) para que el
    movimiento se vea como stop-motion.
*   **Parte B, etiqueta de vida.** Saca el `#roster` de arriba a la izquierda
    (`web/hud.js:24-26`, `web/style.css:44`) de la esquina donde lo pisa el
    texto del canvas de debug. Es un cambio solo de CSS.

Las dos partes no comparten código. La parte B no espera a la parte A: si la
etiqueta se complica, los clips se entregan igual.

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

**Etiqueta.** La vida de cada pieza solo se ve en `#roster`, y el canvas de
debug la tapa. Durante la demo, ni el operador ni el público pueden leer cuánta
vida le queda a cada pieza. La etiqueta no es canon (el tablero de la película
no muestra vida). Es una ayuda de interfaz, igual que el roster, y se justifica
como tal.

## Goals

*   **G1. Cada momento del canon tiene clip:** moverse, atacar, recibir el
    golpe, morir y desaparecer, y el sobreviviente levantando los brazos
    después de cada pelea que termina con una muerte.
*   **G2. `counter` se ve como lo resuelve el motor:** pega el defensor y el
    atacante recibe el golpe.
*   **G3. Movimiento stop-motion:** el mixer avanza de a pasos de unos 12 fps en
    todas las criaturas.
*   **G4. La vida se puede leer sin que la tape el debug,** con el tracking
    funcionando y con la imagen espejada (`#stage.mirror`).
*   **G5. Los tiempos no cambian para el jugador:** una pelea con muerte, más el
    gesto de victoria, entra en la espera de 5 s por evento del servidor
    (`config.toml:67`) sin que se dispare el timeout de 8 s del cliente
    (`events.js:68`).
*   **G6. Criterio de demo:** 2 de cada 3 personas que lo ven por primera vez
    dicen quién ganó el intercambio solo mirando la animación, y ninguna
    animación queda trabada en 5 partidas completas.
*   **G7. Rollback barato:** cada etapa es un commit que se puede revertir, y el
    flag `?clips=basic` vuelve a los 5 clips de hoy sin redeploy.

## Non-Goals

*   **Usar los 14 clips como cuota.** Duck, No, Jump, Jump_Idle, Jump_Land y el
    que pierda entre Wave y Yes quedan sin usar. Cada uno lleva una línea en
    `assets_src/SOURCES.md` con el motivo canon.
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
    brazos arriba. Se decide mirando los dos en el visor (`?viewer=<kind>`) a
    escala real.
*   **Cómo se mide G6:** quién convoca a las personas, cuántas, y si cuenta un
    ensayo con replay (`--replay fixtures/session_01.dj`) o solo partidas en
    vivo.

## Critical User Journeys (CUJs)

### CUJ 1: Golpe que mata

*   **Given**: partida en curso, tracking OK. El soldado azul (2 HP) está al
    lado de la bestia roja (1 HP).
*   **When**: el jugador azul ataca con el soldado y sale `hit`.
*   **Then**: el soldado hace `attack`, la bestia hace `hit` y después `die`
    con fade. Cuando arranca el fade, el soldado hace el gesto de victoria y
    vuelve a `idle`. El jugador rojo puede jugar sin esperar a que termine el
    gesto.

### CUJ 2: Contraataque

*   **Given**: igual que el CUJ 1.
*   **When**: sale `counter`.
*   **Then**: la **bestia** (el defensor) hace `attack` y el soldado hace
    `hit`. El soldado no hace `attack`.

### CUJ 3: Fin de partida

*   **Given**: el rojo tiene una sola pieza viva y le queda 1 HP.
*   **When**: el azul la mata.
*   **Then**: el atacante hace el gesto en el handler `death`. Después, en el
    handler `win`, todas las piezas azules vivas hacen el gesto y aparece el
    banner `GANA AZUL`.

### CUJ 4: Rollback en el ensayo

*   **Given**: el gesto de victoria se ve mal o algo se traba en el ensayo.
*   **When**: el operador abre la página con `?clips=basic`.
*   **Then**: no hay gesto de victoria y el mixer anda suave como hoy. El
    contraataque sigue corregido, porque es un arreglo de un error y no una
    animación nueva.

## Technical Plan (Architecture)

### Parte A: clips

#### A1. Assets: conservar todos los clips

Los cuatro originales traen los mismos 14 clips con el prefijo
`CharacterArmature|` (medido sobre `assets_src/originals/*.glb`). Hoy
`rename_clips` (`tools/adapt_glb.py:31-44`) se queda con 5 y descarta el resto
de la lista `animations` del JSON.

Cambio: `rename_clips` sigue renombrando los 5 del contrato (`idle`, `walk`,
`attack`, `hit`, `die`) con `CLIP_NAMES` y **conserva los demás**, con el
nombre corto en minúscula (`duck`, `jump`, `jump_idle`, `jump_land`, `no`,
`run`, `wave`, `weapon`, `yes`). El script no decide qué significa cada clip.
`check_glb.CLIPS` sigue siendo el mínimo de 5, sin cambios.

El tamaño no es un riesgo: `adapt` copia el buffer binario entero, así que los
datos de los 14 clips ya están dentro de los `.glb` de hoy (409-502 KB contra
444-538 KB de los originales). Conservarlos solo agrega entradas al JSON. El
límite de 5 MB (`check_glb.py:17`) queda lejos.

`assets_src/originals/` se commitea (son unos 2 MB, CC0) para que el pipeline
se pueda reproducir.

#### A2. Un solo mapa momento → clip

`Creature` crea una acción por **cada** clip del glTF, no solo por los de
`CLIPS`. En `creatures.js` se agrega un único objeto que dice qué clip
corresponde a cada momento:

```text
MOMENTS = { idle: "idle", walk: "walk", attack: "attack", hit: "hit",
            die: "die", win: "<wave|yes>" }
```

`events.js` llama a `c.play("win")` con el nombre del momento, y `play()` lo
traduce con `MOMENTS` antes de buscar la acción. Para cambiar de Wave a Yes se
toca una línea. Con `?clips=basic`, `MOMENTS.win` queda en `null` y `play()`
resuelve sin hacer nada, que es lo que ya hace hoy cuando falta un clip
(`creatures.js:75`). La primera vez que falta un clip, `play()` hace un
`console.warn`, así se nota en el ensayo si la cápsula de reemplazo está en
uso.

Los clips que no terminan en loop quedan clavados en su último cuadro
(`clampWhenFinished`). El gesto de victoria tiene que volver a `idle` cuando
termina, pero **solo si en el medio no arrancó otro clip** (por ejemplo, si el
jugador ya movió esa pieza). Si no se chequea eso, el `idle` le pisaría el
`walk`.

#### A3. Victoria después de cada muerte

```text
cola de eventos (events.js)
  attack  ──► guarda lastFight = { atacante, defensor }
  hit     ──► (igual que hoy)
  death   ──► die + fade de la que pierde
              └─► sobreviviente = el de lastFight que no murió
                  sobreviviente.play("win")   ← sin await
  win     ──► cada criatura viva con owner == winner: play("win")  ← sin await
              hud.win(...)
```

*   **Quién ganó la pelea.** El evento `death` trae `piece` y `from`, pero no
    dice quién lo mató. El handler `attack` ya busca al defensor
    (`events.js:28`), así que guarda la pareja en una variable de la cola.
    `death` toma de esa pareja al que no murió. Los eventos de una misma pelea
    llegan siempre juntos y en orden (`game.py:119-125`), así que la pareja no
    queda vieja.
*   **Sin `await`.** El gesto arranca al mismo tiempo que el fade (0.6 s) y
    dura 1.67 s. Como `death` no lo espera, el `anim_done` sale apenas termina
    el fade y la entrada no queda bloqueada más que hoy. Si sí se esperara, el
    handler `death` duraría unos 3.2 s (die 0.75 + crossfade 0.2 + fade 0.6 +
    gesto 1.67). Eso igual entra en los 5 s del servidor, pero suma 1.7 s de
    "Esperá…" en cada muerte.
*   **`owner` en la criatura.** El constructor de `Creature` ya recibe
    `owner` (`creatures.js:48`), pero no lo guarda. Se guarda en
    `this.owner`, y así el handler `win` puede elegir a los ganadores.

#### A4. Contraataque corregido

En el handler `attack`, si `e.result.outcome === "counter"`, hace `attack` el
**defensor** en vez del atacante. Los dos se siguen mirando como hoy. El
evento `hit` que viene después ya apunta al atacante (`game.py:121`), así que
no hay que tocar nada más. En `hit` y en `tie` todo queda igual.

Este cambio no depende de `?clips=basic`: corrige un error, no agrega una
animación.

#### A5. Mixer a pasos (stop-motion)

`Army.update(dt)` (`creatures.js:174`) acumula `dt` y llama a `mixer.update`
con el acumulado solo cuando pasa `STEP = 1/12` s. La pose cambia 12 veces
por segundo, y el render y el parpadeo del holograma siguen a 60 fps.

El desplazamiento de `walkTo` lo mueve un `tween` aparte (`creatures.js:107`),
no el mixer. Si no se cuantiza también, la pieza se desliza suave con las
patas a saltos, y eso se ve como un error, no como stop-motion. Por eso
`walkTo` redondea su `t` a múltiplos de `STEP / secs`. El flash del golpe y
los fades de opacidad siguen suaves: son efectos del holograma, no movimiento
de la pieza.

`FADE = 0.2` queda como está: a 12 fps son 2 o 3 cuadros de transición, que
alcanza para que no haya saltos de pose sin perder la sensación de golpe seco.
`STEP` y `FADE` son constantes que se ajustan en el ensayo. Con
`?clips=basic`, `STEP = 0` y el mixer vuelve a avanzar en cada cuadro.

El visor (`?viewer=<kind>`) usa la misma lógica de pasos, para que lo que se
elige ahí se vea igual que en el juego.

#### A6. Visor con todos los clips

El visor (`main.js:193`) arma un botón por cada acción que tiene la criatura
(`Object.keys(creature.actions)`), en vez de la lista fija de 5. Así se
comparan Wave y Yes a escala antes de llenar `MOMENTS.win`.

### Parte B: etiqueta de vida

Opción elegida por el autor: **(a) solo CSS**. No hay etiqueta flotante sobre
las piezas.

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

**Qué se conserva.** El roster sigue mostrando las 8 piezas, la barra de vida
y las muertas tachadas (`.dead`). La pregunta de dónde queda el resumen de
piezas muertas desaparece, porque el roster no se borra.

**Límites conocidos.**

*   La vida sigue en una lista aparte, lejos de las piezas. G4 pide que se
    pueda leer sin que la tape el debug, y eso se cumple. No pide que se lea
    sobre la pieza.
*   Abajo a la izquierda, `#errors` (`style.css:70`) también se dibuja en
    `bottom: 0; left: 0`. Solo aparece cuando hay un error de JS, y en ese
    caso tapar el roster es aceptable porque el error es lo más importante.
*   El debug dibuja los marcadores y la caja de la mano en cualquier parte del
    cuadro. Si un marcador cae abajo a la izquierda, el roster lo tapa. El
    debug lo usa solo el operador, así que no se mueve el roster por eso.

```text
┌──────────────────────────────────────────────┐
│ #role         #turn               #remote    │
│ [debug: fps / pose / ms / mano]   #notice    │
│                                              │
│                 (tablero)                    │
│                                              │
│ #roster          #hint                       │
│ (8 piezas)       #combat                     │
└──────────────────────────────────────────────┘
```

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
*   **Reason for Rejection**: Rejected by author: choca con la regla "solo
    canon" y necesita cambios de protocolo y eventos nuevos solo para
    justificar clips.

#### Alternativa C: B + salto al seleccionar, como ayuda de interfaz

*   **Pros**: se puede defender si se presenta como UI. Da una señal visible
    sobre la pieza elegida.
*   **Cons**: hace lo mismo que el resaltado de casilla que ya existe
    (`main.js:166`). Necesita una capa de postura (`stance`) por criatura,
    porque la selección llega por `state` y el combate por la cola de
    eventos: los handlers que terminan en `idle` (`events.js:31,43`) pisarían
    el loop y `army.sync` lo perdería al reconectar. Además, Jump_Idle deja a
    la criatura colgada en el aire con las piernas recogidas durante
    segundos.
*   **Reason for Rejection**: Rejected by author: queda fuera de este diseño.
    Pasa a Future Improvements, solo si sobra tiempo antes del freeze.

#### Alternativa D: agregar solo el clip de victoria a `CLIP_NAMES`

*   **Pros**: el diff más chico. Una entrada más en `CLIP_NAMES` y en `CLIPS`,
    y no hace falta el mapa `MOMENTS`.
*   **Cons**: para elegir entre Wave y Yes hay que regenerar los 4 `.glb` dos
    veces, o abrir los originales con otra herramienta, porque el visor solo
    muestra lo que adapt dejó. Cada clip opcional (Run, Weapon) vuelve a tocar
    adapt, check_glb, el contrato de `docs/assets_checklist.md` y los tests.
*   **Reason for Rejection**: Rejected by author (brief, etapa 1): conservar
    todos los clips con adapt cuesta lo mismo una sola vez y deja la decisión
    de qué clip significa qué en un solo objeto del cliente.

#### Alternativa E: gesto de victoria con `await`

*   **Pros**: el gesto nunca queda cortado por el movimiento siguiente, porque
    la entrada sigue bloqueada mientras dura.
*   **Cons**: suma unos 1.7 s de "Esperá…" en cada muerte. El handler `death`
    pasaría a unos 3.2 s: entra en los 5 s del servidor (`config.toml:67`),
    pero el margen es poco si el render anda lento.
*   **Reason for Rejection**: Rejected by author (brief, decisión 2): el gesto
    va sin `await`. Que el siguiente movimiento lo corte se acepta.

### Etiqueta

#### Alternativa b: etiqueta solo en las dos piezas que pelean

*   **Pros**: la vida aparece sobre la pieza justo cuando cambia, y como son
    solo dos casi nunca se enciman.
*   **Cons**: fuera de la pelea no se ve la vida de nadie. Necesita
    proyección por cuadro en `#hud` con la x espejada a mano, porque
    `#stage.mirror` daría vuelta el texto (`style.css:19`), y un momento para
    ocultarla que hoy no existe como evento.
*   **Reason for Rejection**: Rejected by author: la opción a cumple G4 con
    una línea de CSS, sin JS nuevo y sin riesgos de espejo.

#### Alternativa c: etiquetas siempre visibles en las 8 piezas

*   **Pros**: es la única opción que reemplaza al roster del todo. La vida se
    lee sobre cada pieza.
*   **Cons**: con el ángulo de la cámara, las piezas de atrás quedan pegadas
    a las de adelante y las etiquetas se enciman. Chocan con el anillo de
    espera (±40 px, `main.js:125`). Hay que ocultarlas sin tracking,
    desvanecerlas con `pass` y con la muerte, y conservar el resumen de
    piezas muertas en otro lugar. Además, el tablero del canon no muestra
    vida.
*   **Reason for Rejection**: Rejected by author: es la opción con más
    riesgos en vivo, y su ventaja no se pide en ningún goal.

#### Alternativa: ocultar `#roster` salvo con el debug, o cambiarlo por un contador de muertas

*   **Pros**: menos interfaz sobre la escena.
*   **Cons**: ocultarlo sin debug deja al público sin ninguna forma de ver la
    vida, así que no cumple G4. El contador de muertas pierde la vida de las
    piezas que siguen vivas.
*   **Reason for Rejection**: Rejected by author: se eligió la opción a, que
    mueve el roster y lo deja como está.

--------------------------------------------------------------------------------

## Non-Functional Requirements

*   **Rendimiento:** el mixer a pasos hace menos trabajo que hoy: 12
    actualizaciones de pose por segundo en vez de 60. Conservar los 14 clips
    suma 9 `clipAction` por criatura (72 en total). Mientras no suenan,
    quedan inactivas y no cuestan nada por cuadro.
*   **Rollout y rollback:** tres commits (más uno opcional) que se
    revierten por separado (assets, canon, roster y Run/Weapon). En el momento, `?clips=basic` saca el gesto de
    victoria y los pasos sin hacer redeploy. El arreglo de `counter` no se
    revierte con el flag.
*   **Seguridad:** sin cambios. No se toca el protocolo ni el servidor.

--------------------------------------------------------------------------------

### Additional Resources

*   [concepts_brief_personajes.md](../../briefs/concepts_brief_personajes.md): el brief
    de origen.
*   [docs/assets_checklist.md](../../assets_checklist.md): el contrato de
    assets.
*   [docs/designs/dejarik_ar.md](../dejarik_ar.md): el diseño base
    (G3, combate animado).
*   [assets_src/SOURCES.md](../../../assets_src/SOURCES.md): origen y licencia de los
    modelos.

### Future Improvements

*   **Salto al seleccionar, como UI** (alternativa C). Necesita la capa de
    postura (`stance`). Va solo si sobra tiempo antes del freeze.

--------------------------------------------------------------------------------

## Detailed Implementation Plan

Son tres commits, más un cuarto opcional, y van en este orden. Después de cada uno el juego sigue
andando, y cada uno se puede revertir solo.

### Commit 1: assets (en el juego no cambia nada)

#### 1. `tools/adapt_glb.py` (Modify)

*   **Type / Scope**: herramienta del pipeline (Python).
*   **Proposed Changes**: `rename_clips(gltf)` sigue renombrando los 5 clips
    del contrato con `CLIP_NAMES`, como hoy. Las animaciones que no usó **se
    conservan**, con el nombre corto (lo que va después del último `|`) en
    minúscula. Si un nombre conservado coincide con uno del contrato o con
    otro ya conservado, ese clip se descarta, para que no queden dos clips
    con el mismo nombre. La firma no cambia: sigue devolviendo la lista de
    clips que faltan. En el docstring del módulo, "descarta el resto" pasa a
    "conserva el resto en minúscula".

#### 2. `tests/test_check_glb.py` (Modify)

*   **Type / Scope**: test unitario (pytest).
*   **Proposed Changes**:
    *   En `test_adapt_renames_scales_and_grounds`, la línea 81 pasa a esperar
        `CLIPS + ["dance"]`, porque ahora `Armature|Dance` se conserva.
    *   Test nuevo, `test_adapt_keeps_extra_clips_without_duplicates`. El
        origen trae `A|Idle`, `A|Walk`, `A|Punch`, `A|HitReact`, `A|Death`,
        `A|Wave` y `A|Yes`, más `B|Idle` y `A|Attack`, que generan choques de
        nombre. En el resultado tienen que estar los 5 del contrato más
        `wave` y `yes`, sin nombres repetidos, y `check()` tiene que devolver
        la lista vacía.

#### 3. `web/creatures.js`, solo las acciones (Modify)

*   **Type / Scope**: cliente.
*   **Proposed Changes**: el constructor de `Creature` recorre
    `gltf.animations` en lugar de `CLIPS` y crea una acción por cada clip.
    `LOOPING` pasa a ser `{idle, walk, run}`. Se borra `CLIPS`, porque no se
    usa en ningún otro archivo de `web/`. La cápsula de reemplazo no cambia.
    Va en este commit porque el visor (punto 4) lo necesita.

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

#### 6. `assets_src/originals/*.glb` (Create: se commitean los archivos sin trackear)

*   **Type / Scope**: assets de origen, CC0.
*   **Proposed Changes**: se suman los 4 originales al repo (unos 2 MB en
    total), así el punto 5 se puede reproducir.

#### 7. `assets_src/SOURCES.md` (Modify)

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
        *   `run` y `weapon`: pendientes (ver commit 4).
        *   El que pierda entre `wave` y `yes`.

#### 8. `docs/assets_checklist.md` (Modify)

*   **Type / Scope**: documentación del contrato.
*   **Proposed Changes**:
    *   Línea 37: "descarta los demás" pasa a "conserva los demás en
        minúscula".
    *   Líneas 25 y 85: los 5 nombres siguen siendo el **mínimo**
        obligatorio, y se aclara que los demás clips son opcionales.
    *   Línea 104: "los 5 clips" pasa a "todos los clips".

**Control del commit 1:** pasa `pytest`, `check_glb` da 0 errores en los 4
modelos y el visor de cada tipo muestra 14 botones. En el juego no cambia
nada.

**Paso manual entre el commit 1 y el 2:** el autor mira `wave` y `yes` en
`?viewer=<kind>&still` para los 4 tipos y elige uno. El que elija va en
`MOMENTS.win` (commit 2) y en `SOURCES.md`.

### Commit 2: canon (victoria, contraataque y stop-motion)

#### 9. `web/creatures.js` (Modify)

*   **Type / Scope**: cliente.
*   **Proposed Changes**:
    *   `BASIC`: true si la URL tiene `clips=basic`. Se lee una sola vez, al
        cargar el módulo.
    *   `MOMENTS` (exportado): `idle→idle`, `walk→walk`, `attack→attack`,
        `hit→hit`, `die→die` y `win→<clip elegido>`, o `null` si `BASIC` es
        true.
    *   `STEP = BASIC ? 0 : 1/12`. `FADE` queda en 0.2.
    *   `Creature` guarda `this.owner = owner`.
    *   `play(moment)`: primero traduce el nombre con
        `MOMENTS[moment] ?? moment`. El `??` es para que el visor pueda pedir
        un clip por su nombre. Si no hay acción para ese nombre, la primera
        vez avisa con `console.warn` (un `Set` a nivel de módulo evita
        repetirlo) y devuelve una promesa ya resuelta, como hoy.
    *   `celebrate()`: busca la acción de `MOMENTS.win`. Si no existe, no
        hace nada. Si existe, la reproduce y, cuando termina, vuelve a
        `idle` **solo si** `this.current` sigue siendo esa acción. No
        devuelve la promesa, así nadie la espera por error.
    *   `walkTo`: el paso del `tween` redondea `t` hacia abajo a múltiplos de
        `STEP / secs` cuando `STEP > 0`. Con `t = 1` el valor no se redondea,
        así la pieza termina en el centro de la casilla.
    *   `stepMixer(mixer, dt, acc)` (exportado): si `STEP` es 0, hace
        `mixer.update(dt)`. Si no, suma `dt` al acumulador y, mientras el
        acumulador llegue a `STEP`, hace `mixer.update(STEP)` y le resta
        `STEP`. Devuelve el acumulador nuevo. El `while` evita que la pose se
        congele después de una pausa larga del navegador. Hay que cuidar que
        el tween y el mixer usen el mismo reloj. `Army` guarda un solo
        acumulador para todas las criaturas, y `Army.update` lo usa con cada
        mixer, así todas cambian de pose en el mismo cuadro.

#### 10. `web/events.js` (Modify)

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
        fade como hoy y al final pone `fight = null`. Esto cumple A3: el
        gesto arranca junto con el fade y no se espera.
    *   `win(e)`: además de lo que hace hoy, cada criatura de `army.byId` con
        `owner === e.result.winner` llama a `celebrate()`.

#### 11. `web/main.js`, el visor (Modify)

*   **Type / Scope**: cliente.
*   **Proposed Changes**: `runViewer` usa `stepMixer` en lugar de
    `creature.mixer.update(dt)`, así el visor se ve igual que el juego.

**Control del commit 2:**

*   Los CUJs 1 a 4, con click del mouse y con
    `--replay fixtures/session_01.dj`.
*   Para CUJ 2 hace falta un `counter`: buscar uno en el replay o jugar hasta
    que salga.
*   En 5 partidas completas no puede aparecer en la consola
    `"evento sin terminar en 8 s"`.

### Commit 3: roster

#### 12. `web/style.css` (Modify)

*   **Type / Scope**: estilos.
*   **Proposed Changes**: en la línea 44, `top: 64px` pasa a `bottom: 18px`.
    `left: 12px` y el resto quedan igual.

**Control del commit 3:** con el debug encendido (tecla D), y con el espejo
encendido y apagado (tecla F), el roster no se pisa con ningún texto.

### Commit 4 (opcional): Run y Weapon

Este commit se hace solo si los commits 1 a 3 están cerrados y queda tiempo
antes del freeze. Si no llega, el diseño igual cumple todos los goals.
`?clips=basic` también apaga lo que agrega este commit.

#### 13. `web/creatures.js` (Modify)

*   **Type / Scope**: cliente.
*   **Proposed Changes**:
    *   `MOMENTS` suma `run: BASIC ? "walk" : "run"`. En la cápsula, `run` no
        existe y `play()` resuelve vacío. Para evitarlo, `walkTo` usa `walk`
        cuando la criatura no tiene la acción `run`.
    *   `KIND_MOMENTS = { soldado: { attack: "weapon" } }`. Sirve para pisar
        un momento según el tipo de criatura. Si `BASIC` es true, queda
        vacío. Esta entrada se agrega **solo si** el autor, en el visor, ve
        que Weapon se lee mejor que Punch para el soldado. Si no, el objeto
        no se crea.
    *   `Creature` recibe `kind` como tercer parámetro y lo guarda. `play()`
        traduce primero con `KIND_MOMENTS[this.kind]?.[moment]` y después
        con `MOMENTS`. `Army.sync` le pasa `p.kind` y el visor le pasa
        `kind`.
    *   `walkTo(x, y, moment = "walk")`: el clip del recorrido sale del
        parámetro. Se agrega `RUN_SPEED = 2 * WALK_SPEED`, que se usa cuando
        `moment === "run"`. Si no, el ciclo de Run (0.54 s) se ve como correr
        en el lugar.

#### 14. `web/events.js` (Modify)

*   **Type / Scope**: cliente, cola de eventos.
*   **Proposed Changes**: en `move(e)`, si `e.to` no está en
    `spec.adjacency[String(e.from)]`, el movimiento es de 2 casillas.
    Entonces se busca la casilla del medio: la primera `n` de
    `spec.adjacency[String(e.from)]` que tenga `e.to` en
    `spec.adjacency[String(n)]` y que no ocupe ninguna criatura de
    `army.byId`. El motor garantiza que existe, porque la BFS no atraviesa
    casillas ocupadas (`game.py:61-67`). La criatura hace dos
    `walkTo(..., "run")` seguidos, pasando por `n`, y no va en línea recta.
    Así no cruza por encima de otra pieza. Después vuelve a `idle` como hoy.
    Si no se encuentra `n`, cosa que no debería pasar, hace un solo
    `walkTo(..., "run")` en línea recta. Los pasos de sonido no cambian.

#### 15. `assets_src/SOURCES.md` (Modify)

*   **Type / Scope**: documentación.
*   **Proposed Changes**: `run` sale de "Clips sin usar a propósito". `weapon`
    también sale si se usó para el soldado. Si no, queda con el motivo "Punch
    se lee mejor en el visor".

**Control del commit 4:** mover el acechador 2 casillas con una pieza al
costado del camino recto, y ver que corre por la casilla del medio y no
atraviesa a la otra pieza. El soldado ataca con Weapon, si se adoptó. Con
`?clips=basic` vuelven `walk` y Punch.

### Verification Plan

*   **Compilation/Build**: no hay build (JS sin bundler, Python sin
    compilar).
*   **Unit Tests**: `pytest`, que incluye los tests de adapt nuevos y los
    modificados.
*   **Static Analysis & Linting**: lo que el repo ya usa. No se agrega nada.
*   **Assets**: `python tools/check_glb.py web/assets/creatures/*.glb` da 0
    errores.
*   **E2E manual**: los CUJs 1 a 4 con mouse y con replay, `?viewer=<kind>`
    para los 4 tipos, y debug y espejo para el roster.
*   **Demo (G6)**: queda sujeta a la pregunta abierta sobre cómo se mide G6.
