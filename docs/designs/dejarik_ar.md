# Dejarik AR — TP integrador de Visión Artificial

*   **Author:** miroagustin
*   **Status:** Proposed
*   **Date:** 2026-11-03

--------------------------------------------------------------------------------

## Overview

Dejarik AR es un juego de mesa en realidad aumentada para la demo del TP integrador de Visión Artificial, que se entrega el 26/11/2026.

Los elementos físicos son:

*   un tablero circular impreso, con marcadores ArUco alrededor del borde;
*   una webcam en trípode que apunta al tablero;
*   la PC del **anfitrión**, que es el único integrante que necesita tablero y cámara.

La clase es virtual. La demo se muestra compartiendo la pantalla del anfitrión en Teams.

El software se reparte así:

*   **Python**, en la PC del anfitrión, calcula dónde está el tablero respecto de la cámara (su pose) y aplica las reglas del juego.
*   **Un navegador** dibuja sobre el video criaturas 3D animadas, con estética de holograma, que se mueven y pelean entre las casillas.

**Cómo se juega.** Hay dos bandos con 4 piezas cada uno. El **jugador 0** siempre es el anfitrión, que juega en su PC con el mouse y, si da el tiempo, con la mano sobre su tablero. El **jugador 1** depende del modo:

| Modo (`--mode`) | Quién maneja al jugador 1 |
|---|---|
| `cpu` | Un rival automático en Python (contra la PC). |
| `local` | El mismo anfitrión, que juega los dos turnos en su PC. |
| `remote` | Otra persona, desde su casa y en cualquier navegador. Entra con un link que expone el servidor del anfitrión a internet a través de un túnel. Ve el mismo video AR del anfitrión y elige con clic, sin tablero propio. |

**Reglas en una línea.** Cada bando tiene un `guardian`, una `bestia`, un `acechador` y un `soldado`, con ATK, DEF, HP y MOV distintos. En su turno cada jugador mueve una pieza o ataca a una rival adyacente; el combate es 1d6 + ATK contra 1d6 + DEF. Gana quien elimina las 4 piezas rivales. Detalle en "Reglas definitivas".

Durante la partida se puede cambiar de modo sin reiniciarla. La tecla `P` del anfitrión pasa por `cpu → local → remote → cpu` (`remote` solo si se arrancó con `--mode remote`). Si el remoto se cae, la partida sigue.

El trabajo lo hacen 5 integrantes en 24 días. Un integrante (el líder) sabe Blender, Three.js y Unity. Los otros cuatro trabajan en Python.

## The Problem

La consigna pide lo siguiente:

*   una aplicación de realidad aumentada;
*   que muestre modelos 3D con animaciones;
*   que use las técnicas vistas en clase: calibración, ArUco, homografías, PnP, features, flujo óptico y segmentación, todas en Python.

El profesor aclaró dos criterios:

*   lo que más suma es que la aplicación sea llamativa y entretenida;
*   la demo en vivo vale más que cualquier informe; las diapositivas son opcionales y breves.

Tenemos tres problemas concretos:

1.  **Hay que superar el trabajo anterior.** El TP previo del grupo fueron cartas de Yu-Gi-Oh peleando sobre marcadores ArUco sueltos, y el profesor lo consideró precario. Si este TP se ve como "monstruos sobre marcadores" otra vez, no suma. La diferencia tiene que verse en los primeros segundos de la demo:
    *   un juego con reglas y turnos;
    *   un tablero entero que se mantiene anclado aunque se tapen marcadores;
    *   combate animado;
    *   la estética de holograma.
2.  **La nota depende de una demo en vivo de pocos minutos, por Teams.** Pueden fallar:
    *   la luz en la casa del anfitrión;
    *   la cámara o el tracking;
    *   el túnel o la conexión del jugador remoto;
    *   la pantalla compartida, porque Teams comprime la imagen y baja los fps.

    Hace falta un camino de respaldo para cada falla que se pueda prever.
3.  **El tiempo es poco y las habilidades están desparejas.** 24 días no alcanzan para que todos aprendan un stack nuevo. La visión y la lógica tienen que quedar en Python, donde trabaja la mayoría. El render 3D animado tiene que quedar en la herramienta que conoce el líder. Además, los cinco tienen que poder trabajar en paralelo desde el día 3 sin bloquearse entre sí.

**Solución propuesta:**

*   **Python es dueño de la cámara.** Detecta el tablero con un board ArUco, estima la pose con `solvePnP` sobre la cámara calibrada, la suaviza con un filtro One-Euro y lleva el estado del juego.
*   **Por cada cuadro, Python manda al navegador**, por WebSocket:
    *   la imagen del cuadro;
    *   la pose de ese mismo cuadro;
    *   los cambios del juego.
*   **El navegador (Three.js) solo dibuja.** Muestra el video, las criaturas animadas, el HUD y los efectos.
*   **Jugador 1 según el modo:**
    *   remoto: el mismo servidor atiende a un segundo navegador remoto, le manda el video en menor calidad y recibe sus clics, que Python acepta solo en su turno;
    *   contra la PC: Python elige la jugada del jugador 1;
    *   local: el anfitrión juega los dos turnos.

## Goals

*   **G1 — Tablero anclado.** Las criaturas quedan pegadas al tablero impreso mientras la cámara o el tablero se mueven, y siguen ahí cuando una mano tapa hasta la mitad de los marcadores.
    *   Error de alineación: menos de 3 px respecto de la cruz central.
    *   Temblor con la cámara quieta: menos de 1 mm y 1°.
*   **G2 — Partida completa y fácil de seguir.**
    *   Una partida de principio a fin dura entre 6 y 8 minutos.
    *   En la demo se muestra un tramo de unos 3 minutos con al menos 2 combates. La partida completa se juega en los ensayos.
    *   Alguien que no conoce Star Wars entiende de quién es el turno, qué movimientos se pueden hacer y quién ganó, mirando el HUD.
*   **G3 — Combate animado.** Las criaturas tienen look de holograma y los 5 clips (`idle`, `walk`, `attack`, `hit`, `die`), con sonido. Cada combate es una secuencia de acercarse, golpear, impacto y caída que dura entre 2 y 5 s.
*   **G4 — Demo con respaldos ensayados.**
    *   El juego corre en la PC del anfitrión y arranca con un solo comando en menos de 2 minutos.
    *   El modo local funciona sin internet. Solo el jugador remoto y Teams necesitan red.
    *   Cada falla prevista tiene un respaldo ensayado (detalle en Risks & Mitigations):
        *   mano no responde → mouse (`--input mouse`);
        *   remoto se cae → `local` o `cpu` (`P`);
        *   tracking inestable → bloqueo de pose (`L`);
        *   cámara muerta → `--replay`;
        *   Python no arranca → MP4.
*   **G5 — Visión visible.** Una tecla muestra un overlay de debug:
    *   marcadores y ejes;
    *   grilla reproyectada;
    *   pose cruda contra pose filtrada;
    *   fps y error de reproyección.

    Una diapositiva vincula cada técnica de clase con dónde se usa.
*   **G6 — Trabajo en paralelo.** Al final del día 2 están congelados:
    *   la geometría del tablero (`board_spec.json`);
    *   el formato de mensajes;
    *   la convención de coordenadas;
    *   las reglas escritas.

    Desde ahí cada integrante avanza con datos grabados, sin esperar a los demás.
*   **G7 — Tres modos de juego: contra la PC, local y remoto.**
    *   **Contra la PC:**
        *   el rival automático juega dentro de 1,5 s después de que terminan las animaciones;
        *   ataca cuando tiene ventaja y avanza cuando no;
        *   en los ensayos tiene que ganar al menos 1 de cada 5 partidas contra un humano que juega en serio, para que no se vea tonto.
    *   **Local:** los clics valen para el bando que tiene el turno.
    *   **Remoto:**
        *   el jugador 1 entra desde su casa con un link, sin instalar nada y sin tablero;
        *   ve el video AR a ≥ 15 fps;
        *   su clic se refleja en menos de 500 ms;
        *   si intenta jugar fuera de su turno, no pasa nada.
    *   **Cambio de modo:** pasar de un modo a otro con `P` no reinicia la partida.

## Non-Goals

*   **Visión en celulares, iPhone o web móvil.** La consigna no lo exige, y Safari iOS con OpenCV.js no entra en 24 días. El jugador remoto puede entrar desde un celular, pero esa vista no se optimiza.
*   **Segundo tablero AR, tablero 3D virtual para el remoto, más de 2 jugadores y SLAM.** Duplicaría la visión y la calibración, y obligaría a sincronizar el estado entre dos PCs por internet; no entra en 24 días.
*   **Usar todas las técnicas de clase.** El profesor confirmó que alcanza con calibración, ArUco, homografía y PnP. Features, flujo óptico y segmentación quedan fuera.
*   **Reglas fieles a Galaxy's Edge.** Se usa una regla propia simple, escrita en una página.
*   **8 criaturas únicas con rig propio.** Se usan de 2 a 4 tipos ya animados, repetidos en los dos bandos con distinto color.
*   **Que la mano tape los hologramas (oclusión).** Solo el tablero oculta lo que está por debajo de él.
*   **Pantalla de calibración y dashboard de métricas.** La calibración es un script que se corre una vez y las métricas van a una diapositiva.
*   **Filtro de Kalman.** Se usa solo One-Euro.
*   **Lógica del juego en JavaScript.** El navegador nunca decide un resultado.
*   **Publicar el código o la app.** Es de uso académico privado.

## Open Questions

*   **Interacción "wow".** ¿Mano con MediaPipe o un puntero con un marcador ArUco? Se decide en el control 2 (días 14–16), según la precisión medida.

## Critical User Journeys (CUJs)

### CUJ 1: Arranque de la demo

*   **Given:**
    *   la PC del anfitrión está recién prendida;
    *   la webcam está en el trípode y el tablero impreso está sobre la mesa;
    *   el anfitrión ya está en la llamada de Teams.
*   **When:** el anfitrión corre un solo comando.
*   **Then:**
    *   en menos de 2 minutos Chrome se abre en una ventana con el video de la cámara;
    *   la consola imprime el link para el jugador remoto;
    *   al detectar el tablero se reproduce la animación de "encendido";
    *   aparecen las 8 piezas en sus casillas iniciales;
    *   el HUD muestra el turno del jugador 0;
    *   el anfitrión comparte esa ventana en Teams, con el audio del sistema.

### CUJ 2: Turno con mouse

*   **Given:** una partida en curso, con el tablero detectado.
*   **When:** el jugador de turno, en su propio navegador (local o remoto), hace clic en una de sus piezas y después en una casilla iluminada como legal.
*   **Then:**
    *   la pieza camina hasta la casilla con su animación;
    *   si ahí hay un rival, se reproduce la secuencia de combate con sonido;
    *   el HUD actualiza la vida y el resultado;
    *   el turno pasa al otro jugador;
    *   un clic en una casilla que no es legal deselecciona la pieza y no cambia el turno;
    *   un clic del jugador que no tiene el turno se ignora y su HUD muestra "Turno del rival".

### CUJ 3: Mano sobre el tablero

*   **Given:** una partida en curso, con el modo mano activo.
*   **When:** un jugador mete la mano y tapa parte de los marcadores.
*   **Then:**
    *   las criaturas siguen ancladas en el mismo lugar;
    *   si se tapan todos, se mantiene la última pose unos 0,5 s y después las criaturas se desvanecen y aparece "tracking perdido";
    *   cuando la mano sale, todo vuelve en menos de 200 ms;
    *   la casilla bajo el dedo se resalta;
    *   un pinch sobre una casilla funciona como un clic.

### CUJ 4: Falla en vivo

*   **Given:** durante la demo falla algo: la mano no responde, el tracking es inestable con la luz, el remoto pierde la conexión o Python se cuelga.
*   **When:** el anfitrión aprieta la tecla o reinicia con el flag del respaldo que corresponde.
*   **Then:**
    *   la demo sigue en menos de 30 segundos;
    *   si Python se reinició, la partida retoma el último estado guardado y el navegador del anfitrión se reconecta solo. En modo `remote` hay un link nuevo: el anfitrión lo copia del HUD y se lo pasa al jugador 1, que vuelve en menos de 30 s;
    *   si el remoto no vuelve, el anfitrión aprieta `P` y pasa a modo local o contra la PC, sin perder la partida.

### CUJ 5: Mostrar la visión

*   **Given:** una partida en curso.
*   **When:** el anfitrión aprieta la tecla de debug.
*   **Then:**
    *   el overlay muestra los marcadores detectados con sus IDs, los ejes del tablero, la grilla de casillas reproyectada, la pose cruda contra la filtrada, los fps y el error de reproyección;
    *   otra pulsación lo oculta sin cortar la partida.

### CUJ 6: El jugador remoto entra

*   **Given:**
    *   el anfitrión arrancó con `--mode remote`;
    *   la consola mostró un link `https://<algo>.trycloudflare.com/?p=1&k=<token>`;
    *   el anfitrión le pasó ese link al jugador 1 por chat privado de Teams (no el chat de la clase).
*   **When:** el jugador 1 abre el link en su navegador.
*   **Then:**
    *   en menos de 5 s ve el video AR del anfitrión, a ≥ 15 fps;
    *   ve un HUD que dice "Sos el jugador 1 (rojo)";
    *   en su turno, sus clics mueven sus piezas;
    *   un link sin token, o con un token equivocado, recibe un rechazo y no ve nada.

### CUJ 7: Contra la PC

*   **Given:** el anfitrión arrancó con `--mode cpu`, o cambió a ese modo con `P`.
*   **When:** el anfitrión termina su jugada y terminan las animaciones.
*   **Then:**
    *   el HUD muestra "La PC está pensando…";
    *   dentro de 1,5 s, la pieza elegida por la PC se ilumina y mueve o ataca, con las mismas animaciones que una jugada humana;
    *   el turno vuelve al anfitrión;
    *   los clics del anfitrión durante el turno de la PC se ignoran.

## Technical Plan (Architecture)

### Vista general

En la PC del anfitrión hay dos procesos, tres en modo `remote`:

*   **Un proceso Python** (`dejarik`). Concentra la lógica:
    *   captura de la cámara;
    *   visión;
    *   detección de la mano;
    *   reglas del juego;
    *   rival automático;
    *   un único servidor HTTP + WebSocket en `127.0.0.1:8000`. Sirve los archivos estáticos en `/` y el WebSocket en `/ws`.
*   **Un navegador Chrome** en una ventana `--app`, que es la que se comparte en Teams.
    *   Se conecta a `ws://127.0.0.1:8000/ws?p=0&k=<host_token>`.
    *   Recibe cuadros, pose y estado, y dibuja.
    *   Solo devuelve clics, teclas y avisos de "animación terminada".
*   **`cloudflared`**, solo en modo `remote`. Abre un túnel rápido (`cloudflared tunnel --url http://127.0.0.1:8000`) y obtiene una URL pública `https://….trycloudflare.com`.

El navegador del jugador remoto entra por esa URL. El túnel lleva HTTPS y WSS hasta el mismo puerto local, así que no hace falta abrir puertos en el router ni tener cuenta.

```text
                    ┌──────────────────────── Proceso Python (anfitrión) ─────────────────────┐
 Webcam USB ──────► │ capture ─► vision ─► filter ─┐                                           │
 (720p MJPG)        │   │                          ├─► frame_bus ─► server :8000 (asyncio) ────┼─► ws local ─► Chrome anfitrión (p=0) ─► Teams
                    │   └──► hands (hilo aparte) ──┤                    ▲   ▲                   │
                    │                              └─► game (autoridad) ┘   └── ai (modo cpu)   │
                    └───────────────────────────────────────┬──────────────────────────────────┘
                                                            │ http://127.0.0.1:8000
                                                       cloudflared ══ internet ══► navegador remoto (p=1, 480p, ≤15 fps)
```

### Modos de juego y jugadores

*   **Modo.** `transport` guarda `mode ∈ {cpu, local, remote}`. Se elige con `--mode` (por defecto `cpu`) y se cambia en vivo con la tecla `P` del anfitrión.
*   **Cambio de modo con `P`.**
    *   El ciclo es `cpu → local → remote → cpu`. `remote` solo entra en el ciclo si el programa arrancó con `--mode remote`, porque el túnel se abre solo al arrancar.
    *   Al salir de `remote`, la conexión `p=1` sigue conectada y mirando, pero `can_act` le da `false`.
    *   Cualquier cambio de modo cancela la jugada pendiente del rival automático (una sola tarea `asyncio`, que se cancela).
*   **Rol de cada conexión.** Lo decide la URL:
    *   `?p=0&k=<host_token>`: anfitrión. `host_token` es otro token al azar que se genera al arrancar y solo va en la URL `--app` de Chrome; nunca se imprime ni pasa por el túnel.
    *   `?p=1&k=<token>`: jugador remoto. El `token` son 16 bytes al azar que se generan al arrancar (`secrets.token_urlsafe`) y se imprimen en el link. Un token que no coincide cierra la conexión con el código 4401. Lo mismo vale para `p=0`.
    *   Se acepta un solo `p=1` a la vez: gana el primero. Otro `p=1` se cierra con el código 4409 mientras el primero siga conectado.
*   **Quién puede jugar el turno de cada bando:**

| Modo | Turno del bando 0 | Turno del bando 1 |
|---|---|---|
| `cpu` | Anfitrión (clic o mano) | `ai.choose(state)` |
| `local` | Anfitrión | Anfitrión |
| `remote` | Anfitrión | Solo la conexión `p=1` |

*   **Entradas fuera de turno.** Cualquier otra entrada se ignora y le llega un `{"type":"denied","reason":"not_your_turn"}` a quien la mandó.
*   **Mano.** La mano siempre es del anfitrión. Cuenta como entrada del anfitrión.

### Rival automático (`ai.py`)

*   Es una función pura `choose(state) -> list[action]`, sin cv2 ni entrada/salida.
*   Recorre todas las acciones legales de todas sus piezas y les pone un puntaje:
    *   **atacar:** probabilidad de ganar la tirada (se calcula exacta con las 36 combinaciones de 1d6 contra 1d6) × 10, más 15 si el defensor tiene 1 de HP, menos la probabilidad de recibir el contragolpe × 6 cuando el atacante tiene 1 de HP;
    *   **mover:** cuánto se reduce la distancia en el grafo hasta el rival más cercano × 2, menos 4 si la casilla de destino queda al lado de una `bestia` rival y la pieza tiene 1 de HP.
*   Elige la acción con mayor puntaje. Los empates se rompen por el menor `(piece_id, casilla)`, así que la elección es determinista y no usa el RNG.
*   Devuelve la secuencia de `tap`s equivalentes: tocar la pieza y después el destino. `transport` los aplica con 0,6 s entre uno y otro, para que se vea la selección.
*   Después de que el último evento recibe `anim_done`, espera entre 0,4 y 0,9 s antes de jugar, para que parezca que "piensa".

### Video para el jugador remoto

*   Cada conexión tiene su propia tarea de envío, que toma siempre el último paquete del `frame_bus`. Mientras un `send` no termina, esa conexión no recibe cuadros nuevos. Así una conexión lenta pierde cuadros pero no acumula demora, y no frena a la del anfitrión. Para el remoto esto no alcanza, porque `cloudflared` acepta todo y acumula en el túnel. Por eso el remoto confirma cada cuadro con `{"type":"frame_ack","frame_id"}`, y su tarea de envío no manda uno nuevo mientras haya 2 sin confirmar.
*   **Anfitrión:** recibe el JPEG de 1280×720 con calidad 80, al ritmo de la cámara.
*   **Remoto:**
    *   recibe una versión de 854×480 con calidad 60, codificada solo si hay un `p=1` conectado;
    *   máximo 15 fps, unos 3–5 Mbps de subida para el anfitrión;
    *   `K` se escala a ese tamaño en el header, para que su raycast del clic dé el mismo punto del tablero.
*   **Animaciones.** Las animaciones del remoto son solo visuales. Python solo espera el `anim_done` del anfitrión, para que un remoto lento no trabe la partida.

### Hilos dentro del proceso Python

| Hilo | Qué hace | Frecuencia |
|---|---|---|
| **Captura y visión** | Lee el cuadro, detecta ArUco, calcula la pose y la filtra. Codifica el JPEG y deja en el `frame_bus` un paquete con `frame_id`, JPEG y pose. | Al ritmo de la cámara, objetivo 30 fps |
| **Manos** | Toma el cuadro más reciente, lo achica a 640×360 y corre MediaPipe. Publica `hand` (casilla bajo el dedo y estado del pinch). | Lo más rápido que pueda, sin frenar al hilo de visión |
| **asyncio** (principal) | Sirve los archivos estáticos y el WebSocket en el mismo puerto. Por cada conexión, manda el paquete más nuevo del `frame_bus`. Recibe `click`/`anim_done`/`key`, revisa el rol y el turno, y los pasa a `game`. Aplica las acciones de pinch y las del rival automático. | Por evento |

El `frame_bus` es una variable protegida por un lock que guarda **solo el último paquete**, no una cola. Si el navegador va más lento, los cuadros viejos se pierden en vez de acumularse. Así la demora no crece con el tiempo.

### Visión: del cuadro a la pose

1.  **Captura.** `cv2.VideoCapture(idx, CAP_DSHOW)` a 1280×720 con FOURCC MJPG. Autofoco, exposición y balance de blancos se fijan con los valores de `config.toml`.
2.  **Calibración.** Se hace una vez, offline, con `findChessboardCornersSB` y `calibrateCamera`. Usa la misma cámara, resolución y foco de la demo. Guarda `K` y `dist` en `calib.npz`. Si la resolución de captura es otra, `K` se escala.
3.  **Detección.**
    *   Con la API de OpenCV ≥ 4.7: `ArucoDetector(getPredefinedDictionary(DICT_4X4_50), params)` con `cornerRefinementMethod = CORNER_REFINE_SUBPIX`.
    *   El board se arma con `cv2.aruco.Board(objPoints, dict, ids)` a partir de `board_spec.json`.
    *   Lleva 12 marcadores en el borde, uno por sector.
4.  **Pose.**
    *   `board.matchImagePoints` junta las esquinas visibles.
    *   Si hay ≥ 2 marcadores (8 o más puntos), se llama a `cv2.solvePnPGeneric` con `SOLVEPNP_IPPE`. Devuelve las dos soluciones posibles de un plano y se elige:
        *   la de menor error de reproyección;
        *   si los dos errores están a menos de un 20% entre sí, la más cercana a la pose anterior.
    *   Se refina con `solvePnPRefineLM`.
5.  **Validación.**
    *   La pose se rechaza si el error de reproyección supera 3 px o si hay menos de 2 marcadores.
    *   Al rechazarla se mantiene la última pose válida durante 0,5 s. Después se manda `ok=false`.
6.  **Bloqueo de pose (opcional, tecla `L`).** Con la cámara en trípode, congela la pose después de 2 s estables. Así las manos que tapan marcadores no la mueven. `L` de nuevo la libera.
7.  **Filtro One-Euro.**
    *   Se aplica a la traslación (3 componentes) y a la rotación como cuaternión (4 componentes, invirtiendo el signo si `dot(q, q_prev) < 0` y renormalizando).
    *   `min_cutoff` y `beta` están en `config.toml`.
    *   El `rvec` no se filtra directamente.

### Convención de coordenadas (única)

*   **Tablero:** origen en el centro, en metros, **Z hacia arriba** saliendo del papel. **X apunta al centro del sector 1.** Los sectores se numeran en sentido antihorario visto desde arriba.
*   **Python aplica la conversión de OpenCV a Three.js, y es el único lugar donde se hace.** Manda `T_view = diag(1,-1,-1,1) · [R|t]`, en orden por columnas, listo para `Matrix4.fromArray`.
*   **Three.js:**
    *   La cámara virtual queda fija en el origen.
    *   El grupo `board` recibe `T_view` con `matrixAutoUpdate = false`.
    *   Como el tablero tiene Z hacia arriba y glTF tiene Y hacia arriba, dentro de `board` hay un grupo hijo `boardY` rotado +90° en X (corregido el día 2; −90° acostaba las criaturas), una sola vez. Las criaturas cuelgan de `boardY`.
*   **Proyección.** `camera.projectionMatrix` se escribe a partir de K, el ancho, el alto, `near = 0.01` y `far = 10`. No se llama a `updateProjectionMatrix`. Se actualiza `projectionMatrixInverse` a mano.
*   **Canvas.** Tiene la misma relación de aspecto que el cuadro (16:9), con bandas negras si hace falta, sin recortar.

### Geometría del tablero (`board_spec.json`)

Es la única fuente de verdad. Contiene:

*   diccionario ArUco, IDs, lado de cada marcador en metros y sus 4 esquinas en el sistema del tablero;
*   radios: centro `r0`, anillo interno `r1`, anillo externo `r2`;
*   12 sectores de 30°, con `sector_offset_deg` (0 = el sector 1 queda centrado en +X);
*   casillas: `0` es el centro, `1–12` el anillo interno y `13–24` el anillo externo, y la casilla `12+k` queda detrás de `k`;
*   adyacencias:
    *   cada casilla interna está junto a sus 2 vecinas del anillo, a su casilla externa y al centro;
    *   cada casilla externa está junto a sus 2 vecinas del anillo y a su casilla interna;
    *   el centro está junto a las 12 internas;
*   `print_scale_measured`: lo que mide de verdad la regla de 100 mm impresa, que corrige los tamaños.

Lo leen o se genera a partir de él: el PDF para imprimir, `vision`, `hands`, `game` y `web`.

### Dedo / clic → casilla

Se usa **una sola función** `cell_at(x_board, y_board)`, en `board.py`:

*   radio y ángulo → anillo y sector → número de casilla, o `None` si cae afuera del tablero.

Hay dos formas de obtener el punto en el plano:

*   **Dedo (Python).**
    1.  La punta del índice (landmark 8) se pasa a píxeles de 1280×720 (MediaPipe da coordenadas normalizadas) y pasa por `cv2.undistortPoints(pt, K, dist, P=K)`, que lo deja en píxeles.
    2.  Se aplica la homografía imagen→tablero `H⁻¹`, con `H = K·[r1 r2 t]`.
    3.  El resultado va a `cell_at`.

    Se eligió la homografía y no el rayo porque es una técnica vista en clase y es una sola línea. En un plano dan el mismo resultado.
*   **Clic (navegador).**
    1.  `Raycaster` contra un disco invisible del tablero.
    2.  El punto se pasa a coordenadas del tablero.
    3.  Se manda `click{x, y}`.

    Python aplica `cell_at`. El navegador no calcula casillas, para que haya un solo mapeo.

### Mano y pinch

*   El gesto y su config se reemplazan por `docs/designs/hand_interaction.md`.
*   MediaPipe Tasks `HandLandmarker` en modo VIDEO, con `num_hands = 1` y el modelo `.task` guardado localmente.
*   El pinch se mide como `d(4,8) / d(0,9)`, con histéresis:
    *   empieza cuando baja de 0,25;
    *   termina cuando sube de 0,35;
    *   tiene que durar al menos 300 ms.
*   Un pinch se convierte en la misma acción que un clic, sobre la casilla que está bajo el dedo en ese momento.
*   El modo de entrada se elige con `--input mouse|hand|both` (por defecto, `both`).

### Juego (autoridad)

*   `game` es Python puro, sin cv2 ni entrada/salida: `apply(state, action) -> (state, events)`.
*   Hay dos acciones: `("tap", cell)`, que resuelve seleccionar, mover, atacar o deseleccionar según el estado (ver Reglas definitivas), y `("reset",)`.
*   **Bloqueo durante animaciones.**
    *   Mientras haya eventos sin confirmar, `transport` no aplica la entrada y responde `denied{reason:"animating"}`.
    *   El navegador confirma cada evento con `anim_done(id)`.
    *   Si un evento no se confirma en 5 s, se da por hecho, para que un navegador colgado no trabe la partida.
*   Después de cada acción el estado se guarda en `save/state.json`. Se escribe en un archivo temporal y se reemplaza con `os.replace`, para que un corte no lo deje a medias. `--resume` lo carga al arrancar.
*   **Combate con dados.**
    *   El atacante tira 1d6 + ATK y el defensor tira 1d6 + DEF.
    *   Si gana el atacante, el defensor pierde 1 de vida.
    *   Si gana el defensor, el atacante pierde 1 de vida (contragolpe).
    *   Si empatan, no pasa nada.
    *   El generador de números al azar es `random.Random(seed)` y su estado se guarda con la partida. Así, con la misma semilla y las mismas acciones, la partida sale igual (para tests y replay).

### Protocolo WebSocket v1

**De Python al navegador, por cuadro (binario):**

```text
[uint32 big-endian: largo del header N][N bytes: header JSON UTF-8][resto: JPEG]
header = {"v":1,"type":"frame","frame_id":int,"t":ms,
          "pose":{"ok":bool,"T":[16 floats],"n_markers":int,"reproj_px":float,"locked":bool},
          "K":[fx,fy,cx,cy],"size":[w,h],
          "hand":{"cell":int|null,"pinch":bool,"px":[u,v]|null},
          "debug":{...}?}
```

*   `K` y `size` van en cada cuadro. Son 6 números y así el navegador no necesita un estado inicial.
*   `debug` solo va cuando el overlay está activo. Lleva esquinas, IDs, pose cruda y tiempos por etapa.

**De Python al navegador, por cambio de estado (texto JSON):**

```text
{"v":1,"type":"state","turn":0|1,"phase":"select"|"target"|"animating"|"over",
 "pieces":[{"id","owner","kind","cell","hp","alive"}],"selected":int|null,"legal":[int],"winner":0|1|null}
{"v":1,"type":"events","events":[{"id","kind":"move"|"attack"|"hit"|"death"|"turn"|"win","piece","from","to","result"}]}
```

**De Python al navegador, al conectar y cuando cambia el modo o el estado del remoto (texto JSON):**

```text
{"v":1,"type":"hello","you":0|1,"mode":"cpu"|"local"|"remote",
 "remote":{"url":str|null,"tunnel":"up"|"down"|"off","connected":bool}}
```

*   `remote` solo se le manda al anfitrión, que lo ve en su HUD para copiar el link.

**De Python al navegador, en respuesta a una entrada rechazada (texto JSON):**

```text
{"v":1,"type":"denied","reason":"not_your_turn"|"animating"}
```

*   Códigos de cierre del WebSocket: 4401 token inválido, 4409 ya hay un jugador 1.

**Del navegador a Python (texto JSON):**

```text
{"v":1,"type":"click","x":float,"y":float}
{"v":1,"type":"anim_done","id":int}
{"v":1,"type":"key","key":"reset"|"debug"|"lock"|"mode"}
{"v":1,"type":"frame_ack","frame_id":int}
```

*   `frame_ack` solo lo manda el remoto.

*   Las teclas `reset`, `lock` y `mode` solo se aceptan del anfitrión.

*   Cada lado ignora los campos que no conoce.
*   Para cambiar `v` hay que actualizar los dos lados en el mismo commit.

### Navegador (Three.js)

*   **Archivos:** Three.js r169, `GLTFLoader` y `SkeletonUtils` van copiados en `web/vendor/`. No se usa CDN ni un paso de build, solo ES modules sueltos.
*   **Fondo:** cada cuadro se decodifica con `createImageBitmap` y se dibuja en un plano de fondo.
*   **Tablero:**
    *   un disco invisible que solo escribe profundidad, para que el tablero tape la parte de las criaturas que quedaría debajo;
    *   anillos y casillas con emisión azul;
    *   las casillas legales brillan.
*   **Criaturas:**
    *   se copian con `SkeletonUtils.clone`;
    *   cada una tiene su `AnimationMixer`;
    *   se pasa de un clip a otro con `crossFadeTo`;
    *   los clips se llaman exactamente `idle`, `walk`, `attack`, `hit` y `die`;
    *   el material de holograma es un `MeshBasicMaterial` extendido con `onBeforeCompile` (así trae el esqueleto) con brillo de borde (fresnel), scanlines, parpadeo y mezcla aditiva, teñido de rojo o azul según el bando.
*   **Cola de eventos.** Los eventos se reproducen de a uno y en orden: caminar hasta la casilla, atacar, golpe con destello y sacudida, morir con disolución y partículas. Al terminar cada uno se manda `anim_done`.
*   **Audio:** sintetizado con Web Audio en `web/audio.js` (sin archivos): zumbido de fondo, encendido, selección, pasos, dado, ataque, golpe, muerte, cambio de turno, victoria y rechazo. `M` silencia. Se cambió el día 2: evita buscar y licenciar archivos, y funciona offline.
*   **HUD:** en HTML/CSS sobre el canvas. Muestra:
    *   el turno, con el color del bando;
    *   la pieza seleccionada;
    *   la vida;
    *   el resultado del último combate;
    *   la pantalla de victoria;
    *   el aviso de "tracking perdido".
*   **Pérdida de tracking.** Con `pose.ok=false` las criaturas bajan su opacidad durante 300 ms y aparece el aviso. Mientras dure, Python ignora los clics y los pinch.
*   **Reconexión.** Si se corta el WebSocket, se reintenta cada 1 s. Al reconectar, Python reenvía el `state` completo.
*   **URL del WebSocket.** Sale de `location`: `(https ? wss : ws)://location.host/ws` + `location.search`. La misma página sirve para el anfitrión y para el remoto.
*   **HUD según el rol:**
    *   "Sos el jugador N (color)";
    *   "Turno del rival" o "La PC está pensando…";
    *   para el anfitrión, el modo actual y, en modo `remote`, el link con un botón de copiar y el estado del remoto (conectado o desconectado).
*   **Aviso de Teams.** La compresión de Teams puede aplanar el parpadeo y las scanlines. Por eso la intensidad del shader de holograma se ajusta con una variable (`uScan`, `uFlicker`) y se calibra mirando la pantalla compartida desde otra cuenta.
*   **Overlay de debug** (con la tecla `D`): dibuja en un canvas 2D encima marcadores, ejes, la grilla reproyectada, el rayo del dedo y un panel de números.

### Arranque, respaldos y modo replay

*   **Arranque.** `python -m dejarik` levanta todo y abre Chrome con `--app=http://127.0.0.1:8000/?p=0&k=<host_token>`, en una ventana sin barras para compartirla en Teams. Chrome se lanza además con `--disable-features=CalculateNativeWinOcclusion --disable-renderer-backgrounding --disable-backgrounding-occluded-windows --autoplay-policy=no-user-gesture-required`, para que no se pause cuando Teams tapa la ventana y para que suene el audio de arranque. En el ensayo se prueba tapar la ventana con Teams.
*   **Flags:**

| Flag | Qué hace |
|---|---|
| `--mode cpu\|local\|remote` | Modo inicial (por defecto `cpu`). En `remote` lanza `cloudflared` como subproceso, lee la URL pública de su salida e imprime el link con el token. |
| `--input mouse` | Desactiva la mano. |
| `--replay archivo.dj` | En lugar de la cámara, reproduce los cuadros grabados (JPEG + pose) en loop. `game` corre en vivo y se juega con mouse. |
| `--record archivo.dj` | Graba los cuadros que salen hacia el anfitrión (JPEG + pose), no el estado. |
| `--resume` | Carga el último estado guardado. |

*   **Teclas en el navegador:**
    *   `D`: overlay de debug;
    *   `L`: bloquear o liberar la pose;
    *   `R`: reiniciar la partida;
    *   `P`: cambiar de modo (`cpu → local → remote → cpu`).

    Solo el anfitrión puede usar `L`, `R` y `P`.
*   **Último respaldo:** un MP4 de una partida completa en el escritorio, listo para compartir en Teams.
*   **Si falla el túnel:** `--mode remote` sigue funcionando en local. El HUD muestra "Túnel no disponible" y el anfitrión pasa a `local` o `cpu` con `P`.

### Archivos compartidos que se congelan el día 2

| Archivo | Contenido |
|---|---|
| `board_spec.json` | Geometría del tablero. |
| `docs/protocol.md` | El protocolo de arriba, con ejemplos. |
| `docs/rules.md` | Las reglas en una página. |
| `calib.npz` | Calibración de la webcam de la demo. |
| `fixtures/session_01.dj` | Una sesión grabada a mano o generada, para que `web` y `game` arranquen sin cámara. |

### Presupuesto de rendimiento (por cuadro, 720p)

| Etapa | Costo estimado |
|---|---|
| Lectura MJPG | ~3 ms |
| ArUco + PnP | 5–10 ms |
| Filtro | < 1 ms |
| JPEG calidad 80 | ~5 ms |

*   El hilo de visión queda en unos 20 ms, o sea 30 fps con margen.
*   MediaPipe (15–30 ms) corre en su propio hilo. Se espera que el GIL se libere dentro de OpenCV y MediaPipe, así que dos hilos deberían alcanzar.
*   Se verifica el día 12 en la PC de la demo: fps de pose con y sin el hilo de manos. Si con la mano la pose baja de 30 fps, `hands` pasa a un `multiprocessing.Process`.
*   Latencia objetivo de punta a punta (de la cámara a la pantalla): menos de 100 ms en el anfitrión.
*   Codificar el JPEG de 480p para el remoto agrega ~2 ms por cuadro, y solo cuando hay un remoto conectado.

## Alternatives Considered

### Alternativa A: Web app en el celular con OpenCV.js (brief original)

*   **Pros:**
    *   La RA queda en la mano del usuario, que es lo más llamativo.
    *   Un solo código sirve para iPhone y Android.
*   **Cons:**
    *   Hay que reescribir en TypeScript todo lo que el equipo sabe hacer en Python.
    *   El build estándar de OpenCV.js no trae ArUco.
    *   Safari iOS es difícil de depurar.
    *   Proyectar la pantalla del celular agrega otro punto de falla.
*   **Motivo del rechazo:** La consigna no exige celular, son 24 días y cuatro de los cinco integrantes trabajan solo en Python.

### Alternativa B: Unity + AR Foundation

*   **Pros:**
    *   El tracking nativo es estable.
    *   El pipeline de animación es maduro.
*   **Cons:**
    *   El tracking es una caja negra (ARKit/ARCore), y la consigna pide usar las técnicas vistas en clase.
    *   Solo el líder sabe Unity.
*   **Motivo del rechazo:** La parte evaluada quedaría en manos de una sola persona y el trabajo de visión del equipo no se vería.

### Alternativa C: Unity solo como motor de render, con la visión en Python

*   **Pros:**
    *   Mejores herramientas para animar y para efectos.
*   **Cons:**
    *   La conexión de red entre procesos sigue siendo necesaria.
    *   Solo una persona puede trabajar el render.
    *   El build de Unity es pesado para iterar.
*   **Motivo del rechazo:** Mantiene la complejidad de la conexión y le suma un motor pesado, sin una ventaja que compense el costo para 2 a 4 criaturas.

### Alternativa D: Render en Python (pyrender, moderngl, Ursina, Open3D)

*   **Pros:**
    *   Un solo lenguaje y un solo proceso.
*   **Cons:**
    *   pyrender no reproduce animaciones con esqueleto.
    *   En moderngl habría que programarlas a mano.
    *   Ursina tiene soporte flojo para glTF animado.
    *   Open3D se ve pobre.
*   **Motivo del rechazo:** Ninguna de estas librerías muestra criaturas animadas sin escribir el animador desde cero, y los modelos animados son un requisito de la consigna.

### Alternativa E: Panda3D (Actor + panda3d-gltf)

*   **Pros:**
    *   Es la única opción todo-Python que reproduce glTF animado.
    *   Elimina el WebSocket.
*   **Cons:**
    *   Nadie del equipo la conoce.
    *   El look de holograma con shaders cuesta bastante más que en Three.js, donde el líder ya tiene experiencia.
*   **Motivo del rechazo:** Queda como **plan B** si la conexión por WebSocket no funciona para el control del día 5.

### Alternativa F: El navegador muestra su propio video (getUserMedia) y Python manda solo la pose

*   **Pros:**
    *   No hay que mandar el video por el WebSocket.
*   **Cons:**
    *   En Windows dos procesos se pelean por la misma webcam.
    *   Aunque pudieran compartirla, el video y la pose serían de cuadros distintos, y las criaturas se deslizarían sobre el tablero.
*   **Motivo del rechazo:** Rompe la alineación, que es justamente lo que tiene que verse mejor que en el TP de Yu-Gi-Oh.

### Alternativa G: Visión en el navegador (OpenCV.js / MediaPipe JS)

*   **Pros:**
    *   Un solo proceso, sin WebSocket.
*   **Cons:**
    *   La visión pasa a JavaScript, que solo maneja el líder.
    *   Hay que compilar OpenCV.js con ArUco.
*   **Motivo del rechazo:** Saca las técnicas de clase del lenguaje en que las vio el equipo.

### Alternativa H: Un solo marcador ArUco, o una pose por marcador promediada

*   **Pros:**
    *   Es simple, y ya lo hicieron en el TP anterior.
*   **Cons:**
    *   Con un marcador chico la pose salta entre dos soluciones.
    *   Promediar poses individuales da peor resultado que un único PnP con todas las esquinas.
    *   No se diferencia del TP de Yu-Gi-Oh.
*   **Motivo del rechazo:** Con pocos píxeles por marcador la pose salta entre las dos soluciones del plano; el board de 12 marcadores evita eso y sigue anclado con la mitad tapada (G1). No se usa ni como respaldo: el board ya tolera la mitad de los marcadores tapados y `L` cubre el resto.

### Alternativa I: Auto-rig de Mixamo para criaturas propias

*   **Pros:**
    *   Animaciones gratis.
*   **Cons:**
    *   Solo funciona con humanoides bípedos, y la mayoría de los monstruos no lo son.
*   **Motivo del rechazo:** La mayoría de las criaturas no son bípedas, así que el auto-rig no sirve; se usan modelos que ya vienen animados (Quaternius CC0, Sketchfab).

### Alternativa J: Filtro de Kalman para la pose

*   **Pros:**
    *   Modela velocidad y puede predecir.
*   **Cons:**
    *   Hay que ajustar unos 6 parámetros de ruido, contra 2 de One-Euro.
*   **Motivo del rechazo:** One-Euro se valida contra el temblor de G1 (< 1 mm y 1°); si no lo cumple, se revisa.

### Alternativa K: `solvePnP` simple con `useExtrinsicGuess`

*   **Pros:**
    *   Es una sola llamada.
*   **Cons:**
    *   No ve la segunda solución del plano.
    *   Cuando quedan pocos marcadores puede quedarse trabado en la pose espejada.
*   **Motivo del rechazo:** Con pocos marcadores elige la pose espejada y no se recupera; IPPE devuelve las dos soluciones y permite elegir por error y continuidad.

### Alternativa L: Que el navegador calcule la casilla del clic

*   **Pros:**
    *   Python recibe directamente un número de casilla.
*   **Cons:**
    *   El mapeo de punto a casilla quedaría duplicado en Python y en JS, y podría divergir.
*   **Motivo del rechazo:** El navegador manda `(x, y)` en coordenadas del tablero y `cell_at` en Python es la única que decide.

### Alternativa M: Multijugador por red local (LAN)

*   **Pros:**
    *   No depende de un túnel ni de internet.
*   **Cons:**
    *   La clase es virtual y cada integrante está en su casa.
*   **Motivo del rechazo:** No sirve para la situación real de la demo.

### Alternativa N: El remoto ve un tablero 3D virtual y solo recibe el estado

*   **Pros:**
    *   Pocos kbps en lugar de 3–5 Mbps.
    *   El remoto puede girar la cámara.
*   **Cons:**
    *   Hace falta un modo de escena sin video.
    *   La vista del remoto no es RA.
*   **Motivo del rechazo:** Se prefiere que los dos vean la misma RA, con menos código, a cambio de depender de la subida del anfitrión.

### Alternativa O: Segundo tablero AR opcional en la casa del remoto (Python en modo satélite)

*   **Pros:**
    *   Cada jugador ve las criaturas sobre su propio tablero.
    *   Es lo que más se diferenciaría.
*   **Cons:**
    *   Duplica la visión, la calibración y la impresión.
    *   Hay que sincronizar el estado entre dos procesos Python por internet.
*   **Motivo del rechazo:** No entra en 24 días junto con las criaturas y el combate.

### Alternativa P: Port forwarding, ngrok o Tailscale en lugar de cloudflared

*   **Pros:**
    *   ngrok y Tailscale son conocidos.
    *   Con port forwarding no hay intermediario.
*   **Cons:**
    *   Port forwarding requiere tocar el router del anfitrión y no da HTTPS.
    *   ngrok gratis requiere cuenta y muestra una página de aviso antes de entrar.
    *   Tailscale requiere que el remoto instale algo y tenga cuenta.
*   **Motivo del rechazo:** Decisión mecánica de diseño. El túnel rápido de cloudflared no necesita cuenta ni instalación del lado del remoto, y da HTTPS/WSS.

### Alternativa Q: Rival automático que juega al azar, o con minimax

*   **Pros:**
    *   Al azar son 10 líneas.
    *   Minimax juega mejor.
*   **Cons:**
    *   Al azar se ve tonto en la demo: no ataca piezas que tiene al lado.
    *   Minimax con dados necesita expectiminimax, que es más código y más lento, sin una mejora visible en 3 minutos.
*   **Motivo del rechazo:** Decisión mecánica de diseño. Una heurística de un paso, con probabilidades exactas de los dados, es poco código y se ve razonable.

### Alternativa R: El remoto ve la RA por Teams y su página es solo un mapa 2D para hacer clic

*   **Pros:**
    *   Sin video por el túnel (pocos kbps), sin descargar criaturas y sin `K` escalado.
*   **Cons:**
    *   El remoto ve la RA con 1–2 s de demora de Teams, así que su clic va sobre una imagen vieja.
    *   Tiene que mirar dos ventanas a la vez.
*   **Motivo del rechazo:** La demora de Teams rompe la meta de < 500 ms de G7. Queda como respaldo si la medición del día 12 no alcanza.

### Alternativa S: Video al remoto por WebRTC (`aiortc`, H.264)

*   **Pros:**
    *   De 3 a 5 veces menos ancho de banda que JPEG.
    *   Trae control de congestión.
*   **Cons:**
    *   Hace falta señalización e ICE/TURN detrás del túnel, y una dependencia nativa pesada.
*   **Motivo del rechazo:** Con `frame_ack` y 480p, JPEG por WebSocket entra en la subida medida y es mucho menos código.

## Risks & Mitigations

| Riesgo | Mitigación | Respaldo en vivo |
|---|---|---|
| El líder es el único que sabe Three.js y Blender; si se atrasa, no hay criaturas ni HUD. | P4 opera la generación de criaturas (archivo 35), así el líder solo hace `web/`. | Cubos con color por bando y las mismas animaciones de posición. |
| Los modelos descargados traen otros nombres y cantidad de clips. | Los clips se renombran al importar en Blender y `check_glb.py` verifica los 5 nombres. | Usar `idle` para el clip que falte. |
| Teams, Chrome y MediaPipe compiten por la CPU del anfitrión. | Se mide el día 12 en la PC de la demo, con Teams compartiendo. Requisito: 4 núcleos y 8 GB. | `--input mouse` libera el hilo de MediaPipe. |
| Mala luz en la casa del anfitrión. | Exposición fija en `config.toml`, y una lámpara en el ensayo. | `L` (bloqueo de pose), y después el MP4. |
| El túnel no levanta o se cae. | `cloudflared` se prueba en cada ensayo. | `P` pasa a `cpu` o `local`. |
| La subida del anfitrión no alcanza para el remoto y Teams a la vez. | Se mide el día 12 (ver NFR). | `P` pasa a `cpu`. |
| Un compañero entra con el link y ocupa el lugar del jugador 1. | El link va por chat privado, y gana la primera conexión `p=1` (ver Modos). | `P` pasa a `local`. |
| La mano de MediaPipe no es precisa. | Se decide en el control 2 (Open Questions). | Mouse. |
| El rival automático no llega a ganar 1 de 5. | Los pesos son constantes al principio de `ai.py` y se ajustan después del primer ensayo. | Ninguno; no bloquea la demo. |

--------------------------------------------------------------------------------

## Non-Functional Requirements

*   **Rendimiento.**
    *   Captura y pose a ≥ 30 fps a 720p.
    *   Render a ≥ 30 fps.
    *   Latencia de la cámara a la pantalla < 100 ms.
    *   Detección de mano a ≥ 15 Hz, sin frenar la pose.
*   **Modo remoto:**
    *   subida del anfitrión ≥ 8 Mbps (3–5 Mbps del video remoto más 2–3 Mbps de Teams);
    *   todo `web/` (Three.js, criaturas, sonidos) pesa ≤ 10 MB, y se mide el día 12;
    *   el jugador remoto entra antes de empezar la demo, así la descarga no compite con Teams en vivo;
    *   el clic del remoto se refleja en < 500 ms;
    *   se mide el día 12 con un integrante conectado desde otra casa.
*   **Sin conexión.**
    *   Los modos `cpu` y `local` no dependen de la red: Three.js, el modelo de MediaPipe, las criaturas y los sonidos están en el repo.
    *   El modo `remote` necesita internet y `cloudflared.exe`, que se descarga una vez y se guarda en `tools/bin/`, ignorado por git.
    *   El entorno de Python está congelado en `requirements.txt` con versiones fijas.
*   **Seguridad.** En modo `remote` el servidor queda expuesto a internet a través del túnel. Las medidas son:
    *   el servidor escucha solo en `127.0.0.1`, y el túnel es la única entrada externa;
    *   el WebSocket exige un token al azar de 16 bytes, que se genera en cada arranque, y el link solo se comparte por chat privado de Teams;
    *   el rol de anfitrión exige `host_token`, que no sale de la PC; sin él no se puede usar `reset`, `lock` ni `mode`;
    *   el servidor estático solo sirve archivos que, ya resueltos, quedan dentro de `web/`; cualquier otra ruta da 404;
    *   los mensajes del cliente se validan con `parse_client`, y si superan 1 KB la conexión se cierra.
*   **Recuperación.**
    *   El estado de la partida se guarda en disco después de cada acción.
    *   El navegador se reconecta solo.
    *   Volver a lanzar Python con `--resume` retoma la partida en menos de 30 s.

## Future Improvements

*   **Celular:** misma visión portada a OpenCV.js o un cliente que mande la cámara del celular a la PC del anfitrión.
*   **Oclusión por la mano:** máscara de segmentación de MediaPipe usada como buffer de profundidad.
*   **Rival automático con niveles de dificultad:** expectiminimax de 2 jugadas.
*   **Vista alternativa para el remoto:** la alternativa R (o la N), si la subida del anfitrión no alcanza.
*   **Reglas completas de Galaxy's Edge:** con empujes.

--------------------------------------------------------------------------------

## Detailed Implementation Plan

### Reglas definitivas (van en `docs/rules.md`)

**Tablero y piezas**

*   25 casillas, con las adyacencias de `board_spec.json`.
*   Cada jugador tiene 4 piezas, una de cada tipo:

| Tipo (`kind`) | ATK | DEF | HP | MOV | Rol |
|---|---|---|---|---|---|
| `guardian` | 1 | 3 | 3 | 1 | Aguanta golpes |
| `bestia` | 3 | 1 | 2 | 1 | Pega fuerte |
| `acechador` | 2 | 1 | 2 | 2 | Se mueve rápido |
| `soldado` | 2 | 2 | 2 | 1 | Equilibrado |

*   **Posiciones iniciales** (anillo externo):
    *   Jugador 0: casillas `23, 24, 13, 14`, en el orden guardian, bestia, acechador, soldado.
    *   Jugador 1: casillas `17, 18, 19, 20`, en el mismo orden.
*   **Valores ajustables.** Los números de la tabla viven en `dejarik/game.py`, en una constante `KINDS`. Se pueden ajustar después del primer ensayo sin tocar nada más.

**Turno**

*   En cada turno el jugador hace **una** acción:
    *   **Mover:** a una casilla vacía a una distancia de hasta MOV pasos, sin atravesar casillas ocupadas.
    *   **Atacar:** a una pieza rival adyacente. El atacante no se mueve.
*   **Elegir la acción:**
    *   El jugador selecciona una de sus piezas.
    *   Las casillas legales se iluminan: las vacías alcanzables y las adyacentes con rival.
    *   Al tocar una casilla con rival, ataca; al tocar una vacía, se mueve.
    *   Tocar otra pieza propia cambia la selección.
    *   Tocar una casilla no legal la deselecciona.
*   **Combate:** el atacante tira 1d6 + ATK y el defensor 1d6 + DEF. Si gana el atacante, el defensor pierde 1 HP (`hit`); si gana el defensor, el atacante pierde 1 HP (`counter`); si empatan, no pasa nada (`tie`). Una pieza con HP 0 muere y se retira del tablero.
*   **Fin de la partida:** gana quien elimina las 4 piezas rivales. Con 4 piezas siempre hay alguna acción legal, así que no hace falta una regla de turno pasado.

### Archivos a crear

Hoy el repo solo tiene `Dejarik_AR_Brief.pdf`, `concepts_brief.md` y este documento, así que **todos los archivos son nuevos**. Cada uno lleva su responsable. L es el líder y P1–P4 son los otros cuatro integrantes, según la tabla de roles del brief.

#### Raíz y configuración

##### 1. `requirements.txt` (Create, P4)

*   **Tipo:** dependencias de Python 3.11.
*   **Cambios:** versiones exactas (`==`). Punto de partida:
    *   `opencv-contrib-python==4.10.0.84`;
    *   `mediapipe==0.10.14` (pide `numpy<2`);
    *   `numpy==1.26.4`;
    *   `websockets==15.0.1` (hace falta ≥ 14 para `websockets.asyncio.server`);
    *   `pillow==10.4.0` (lo usa `make_board.py`);
    *   `pytest==8.3.3`.

    El día 1 se instalan en un venv limpio y se verifica que importen `cv2.aruco` y `mediapipe.tasks`. Si alguno falla, se cambia ese pin y queda registrado en el archivo.
*   **Por qué:** los dos paquetes de OpenCV instalan el módulo `cv2` y uno pisa al otro, y se pierde `aruco`. Por eso se instala solo `opencv-contrib-python`.

##### 2. `config.toml` (Create, P1)

*   **Tipo:** configuración que se ajusta en la casa del anfitrión. Se lee con `tomllib`.
*   **Cambios:**
    *   `[camera]`: index, width, height, fourcc, autofocus, focus, exposure, wb;
    *   `[pose]`: max_reproj_px = 3, min_markers = 2, hold_ms = 500, lock_stable_s = 2, lock_max_dt_mm = 2, lock_max_drot_deg = 0.5;
    *   `[filter.t]` (traslación): min_cutoff = 1.0, beta = 0.5, d_cutoff = 1.0; `[filter.r]` (rotación): min_cutoff = 1.0, beta = 0.05, d_cutoff = 1.0. Son valores iniciales;
    *   `[hands]`: reemplazado por `docs/designs/hand_interaction.md` (gesture, on, off, hold_ms, …, input_width = 640);
    *   `[net]`: port = 8000, jpeg_quality = 80, remote_width = 854, remote_quality = 60, remote_max_fps = 15, cloudflared_path = "tools/bin/cloudflared.exe";
    *   `[ai]`: think_min_s = 0.4, think_max_s = 0.9, tap_gap_s = 0.6;
    *   `[game]`: seed;
    *   `[anim]`: anim_timeout_s = 5;
    *   `[browser]`: chrome_path = "C:/Program Files/Google/Chrome/Application/chrome.exe".
*   **Por qué:** los valores que dependen del lugar y la luz tienen que cambiarse sin tocar código.

##### 3. `board_spec.json` (Create, P1 con L; se congela el día 2)

*   **Tipo:** datos.
*   **Cambios:** tiene los campos definidos en el Technical Plan:
    *   `dictionary: "DICT_4X4_50"`;
    *   `markers: [{id, center_xy_m, size_m, rotation_deg}]` × 12;
    *   `radii_m: {r0, r1, r2}`;
    *   `sector_offset_deg`;
    *   `cells: [{id, ring, sector}]`;
    *   `adjacency: {id: [ids]}`;
    *   `print_scale_measured`.

    Las esquinas de cada marcador **no** se escriben a mano: `board.py` las calcula a partir del centro, el tamaño y la rotación.

    Valores iniciales, que entran en A2 (420 × 594 mm) con margen y se congelan el día 2:
    *   `r0 = 0.0495`, `r1 = 0.102`, `r2 = 0.156`;
    *   12 marcadores de `0.031` m sobre el radio `0.177`, en el centro de cada sector; el sector k lleva el ID k−1;
    *   se pasó de A3 a A2 (×1,41) el día 2: con A3 la casilla interna medía 28 mm y ninguna criatura animada de Quaternius entraba sin superponerse. En A2 mide 40 mm de ancho y los marcadores ganan tamaño para la detección;
    *   `sector_offset_deg = 0`;
    *   `rotation_deg`: ángulo del borde superior del marcador, antihorario desde +X; el borde superior mira hacia afuera;
    *   las claves de `adjacency` son strings (JSON).
*   **Por qué:** es la única fuente de la geometría del tablero.

##### 4. `calib.npz` (Create, generado por P1)

*   **Tipo:** salida de `tools/calibrate.py`.
*   **Cambios:** contiene `K`, `dist`, `size` y `rms`.
*   **Por qué:** sin K no hay pose ni proyección.

##### 5. `README.md` (Create, P4)

*   **Tipo:** documentación.
*   **Cambios:**
    *   instalación (venv con Python 3.11 y `pip install -r requirements.txt`);
    *   cómo imprimir y calibrar;
    *   cómo correr cada modo (`python -m dejarik --mode cpu|local|remote`, flags y teclas);
    *   cómo descargar `cloudflared.exe` a `tools/bin/` y cómo pasar el link al remoto;
    *   cómo correr los tests;
    *   un glosario corto: pose, PnP, One-Euro, glTF, rig, pass-and-play.

##### 6. `.gitignore` (Create, P4)

*   **Cambios:** ignora `.venv/`, `save/`, `recordings/`, `__pycache__/` y `tools/bin/`.

#### Documentos congelados el día 2

##### 7. `docs/protocol.md` (Create, L y P4)

*   **Cambios:**
    *   el protocolo v1 del Technical Plan, con un ejemplo real de cada mensaje;
    *   la convención de coordenadas: ejes del tablero, `diag(1,-1,-1,1)`, orden por columnas y el grupo `boardY`;
    *   el formato `.dj` (punto 22);
    *   los campos de cada evento:
        *   `move{piece, from, to}`;
        *   `attack{piece, to, result:{"atk_roll":int,"def_roll":int,"outcome":"hit"|"counter"|"tie"}}`;
        *   `hit{piece, result:{"hp":int}}` (la pieza que perdió vida);
        *   `death{piece, from}`;
        *   `turn{result:{"turn":0|1}}`;
        *   `win{result:{"winner":0|1}}`;
    *   el orden fijo: un ataque es `attack` → `hit` (si no hubo empate) → `death` (si el HP llegó a 0) → `win` o `turn`; un movimiento es `move` → `turn`;
    *   el payload de `debug`: `{"corners":[[[u,v]×4]], "ids":[int], "T_raw":[16], "ms":{"read","detect","pnp","filter","jpeg"}, "pinch_ratio":float|null}`.

##### 8. `docs/rules.md` (Create, P2)

*   **Cambios:** las reglas definitivas de arriba en una página, más una versión de 20 segundos para leer en la demo.

##### 9. `docs/assets_checklist.md` (Create, L)

*   **Tipo:** especificación de los modelos. Es también el prompt base para la IA que opera Blender a través del MCP de Blender.
*   **Cambios:**
    *   **Contrato de salida**, que es lo mismo que verifica `tools/check_glb.py`:
        *   `.glb`, +Y hacia arriba, 1 unidad = 1 m, en el primer cuadro de `idle`: vista desde arriba entra en un círculo de 44 mm centrado en el origen (una casilla del anillo interno del A2 mide 40 mm de ancho) y mide de 30 a 70 mm de alto. Se cambió el día 2, después de medir los monstruos de Quaternius: son casi tan anchos como altos y quedan entre 35 y 50 mm;
        *   menos de 5 MB, sin Draco;
        *   un solo esqueleto, o animación por objeto si la criatura es rígida;
        *   clips llamados exactamente `idle|walk|attack|hit|die`; `idle` y `walk` deben hacer loop sin saltos;
        *   la criatura mira hacia +Z, con el origen en la base entre las patas.
    *   **Orden de preferencia de las fuentes**, que se le pasa a la IA en este orden:
        1.  modelos que ya vienen animados (Quaternius CC0, Sketchfab descargable CC, a través de la integración de Sketchfab del MCP);
        2.  un modelo estático, más un esqueleto simple de 4 a 8 huesos (columna, cabeza, cola o patas) que la IA arma por script, con los 5 clips en keyframes;
        3.  si nada de eso funciona, animación por objeto: mover, rotar y escalar la pieza entera, guardado como clips dentro del `.glb`.
    *   **Un prompt por criatura**, con el rol del tipo (por ejemplo "bestia: agresiva, ataque con embestida"), la silueta buscada y el contrato de salida.
    *   **Revisión humana:** cada `.glb` se abre en el visor de `web/` (`?viewer=<kind>`), que reproduce los 5 clips. Si no pasa el contrato, vuelve a la IA con el error concreto.
*   **Por qué:** una IA a través del MCP puede armar escenas y escribir `bpy`, pero hacer rigging y animación de criaturas no humanoides es lo que peor le sale. Sin un contrato verificable y un orden de respaldo, el riesgo es llegar al día 16 con modelos que no animan.

##### 10. `docs/demo_script.md` (Create, P4)

*   **Cambios:**
    *   el guion de 3 minutos, minuto a minuto: arranque con `--mode remote` y `P` hasta `cpu` → partida contra el rival automático → `P` dos veces para volver a `remote` con un integrante desde su casa → al menos 2 combates → overlay de debug;
    *   quién hace qué durante la demo: el anfitrión comparte la ventana, un integrante es el remoto y otro narra;
    *   el checklist del anfitrión: webcam de repuesto, trípode, lámpara, tablero de repuesto, cable de red en lugar de Wi-Fi, "compartir audio del sistema" activado en Teams, y el MP4 en el escritorio;
    *   la tabla de respaldos: qué tecla o flag, cuándo usarla y cuánto tarda (medido en los ensayos).

#### Herramientas

##### 11. `tools/make_board.py` (Create, P1)

*   **Cambios:**
    *   lee `board_spec.json`;
    *   dibuja a 300 dpi los anillos, sectores, números de casilla, la cruz central, los 12 marcadores (con `cv2.aruco.generateImageMarker`) y una regla de 100 mm;
    *   guarda `print/board.pdf` con Pillow, en tamaño A2 (se imprime en una copistería). `--page A3` y `--page A4` generan versiones achicadas en una sola hoja, con la regla achicada igual; `print_scale_measured` corrige la escala. Sirven para probar en casa. Se descartó partir el tablero en varias hojas porque la unión cruza marcadores y los márgenes de impresión la cortan;
    *   `--checker` genera `print/checker.pdf`, el damero 9×6 para `calibrate.py`.
*   **Por qué:** el tablero impreso y el spec no pueden diferir.

##### 12. `tools/calibrate.py` (Create, P1)

*   **Cambios:**
    *   abre la cámara con los parámetros de `config.toml`;
    *   con `ESPACIO` captura una vista del damero (9×6) si `findChessboardCornersSB` lo encuentra;
    *   con `C` corre `calibrateCamera`, muestra el RMS y guarda `calib.npz`;
    *   no guarda si el RMS es ≥ 0,5 px o si hay menos de 15 vistas.

##### 13. `tools/fake_session.py` (Create, P4; se usa desde el día 2)

*   **Cambios:**
    *   genera `fixtures/session_01.dj` sin cámara;
    *   proyecta el tablero del spec con una pose fija que oscila un poco, usando `cv2.projectPoints` sobre una imagen gris de 1280×720;
    *   codifica cada cuadro con `protocol.encode_frame`;
    *   no genera `state` ni `events`: el `.dj` solo tiene cuadros.
*   **Por qué:** permite que `web/` y la integración avancen sin esperar a la visión real.

#### Paquete Python `dejarik/`

##### 14. `dejarik/__main__.py` (Create, P4)

*   **Cambios:**
    *   lee los flags (`--mode cpu|local|remote`, `--input mouse|hand|both`, `--replay PATH`, `--record PATH`, `--resume`, `--no-browser`). `--input hand` ignora los clics del anfitrión; `--input mouse` no arranca el hilo de manos;
    *   carga la config, el spec y la calibración;
    *   genera `host_token` y `remote_token` con `secrets.token_urlsafe(16)`. `host_token` se guarda en `save/host_token` y `--resume` lo reutiliza, para que la ventana de Chrome ya abierta se reconecte sola;
    *   arranca el hilo de visión (o el de replay), el hilo de manos (si corresponde) y el loop asyncio de `transport`, al que le pasa los dos tokens;
    *   en modo `remote` llama a `tunnel.start()` e imprime `<url>/?p=1&k=<remote_token>`. `host_token` nunca se imprime;
    *   abre Chrome (`[browser] chrome_path`) con `subprocess`, con `--app=http://127.0.0.1:8000/?p=0&k=<host_token>` y los flags del Technical Plan (`--disable-features=CalculateNativeWinOcclusion --disable-renderer-backgrounding --disable-backgrounding-occluded-windows --autoplay-policy=no-user-gesture-required`). Con `--resume` no abre otra ventana si ya hay una;
    *   al salir, termina el subproceso de `cloudflared`.

##### 15. `dejarik/config.py` (Create, P4)

*   **Cambios:** `load_config() -> dict` (tomllib) y `load_calib() -> (K, dist, size)`. Si la resolución de captura es otra, escala K.

##### 16. `dejarik/board.py` (Create, P1)

*   **Cambios:**
    *   `load_spec()`;
    *   `marker_corners(spec) -> {id: float32 (4,3)}` (esquinas en sentido horario desde arriba a la izquierda, z = 0, corregidas por `print_scale_measured`);
    *   `aruco_board(spec) -> cv2.aruco.Board`;
    *   `cell_at(x, y, spec) -> int | None`;
    *   `cell_center(cell, spec) -> (x, y)`;
    *   `neighbors(cell, spec) -> list[int]`.
*   **Por qué:** visión, manos, juego y herramientas usan la misma geometría.

##### 17. `dejarik/vision.py` (Create, P1)

*   **Cambios:**
    *   `open_camera(cfg) -> VideoCapture`: fija `CAP_PROP_FOURCC` **antes** del ancho y el alto (si no, DSHOW cae a YUY2 con pocos fps), y después `CAP_PROP_AUTOFOCUS`, `CAP_PROP_FOCUS`, `CAP_PROP_AUTO_EXPOSURE`, `CAP_PROP_EXPOSURE`, `CAP_PROP_AUTO_WB` y `CAP_PROP_WB_TEMPERATURE`;
    *   `class PoseEstimator(spec, K, dist, cfg)`, con `update(gray) -> Pose`.
        *   `Pose` es un dataclass con `ok, rvec, tvec, n_markers, reproj_px, locked, raw` y, en modo debug, `corners, ids`.
        *   Hace la detección, `matchImagePoints`, `solvePnPGeneric(IPPE)`, elige la solución (menor `reprojectionError` RMS que devuelve `solvePnPGeneric`; si difieren < 20%, la de menor ángulo de `Rodrigues(R_prevᵀ·R_i)`), `solvePnPRefineLM`, recalcula el error con `projectPoints` y valida, mantiene la última pose 500 ms, bloquea la pose y aplica el filtro.
    *   `to_view_matrix(rvec, tvec) -> list[16]`: aplica `diag(1,-1,-1,1)` y devuelve la matriz en orden por columnas. Es el único lugar donde se convierte de OpenCV a Three.js.
    *   `vision_loop(cap, estimator, bus, flags, stop)`: lee el cuadro, estima la pose, codifica el JPEG (y el de 480p si `flags.remote_connected`) y publica el paquete (ver "Hilos y datos compartidos").
    *   El bloqueo de pose se activa cuando, durante `lock_stable_s`, las poses crudas no se alejan más de `lock_max_dt_mm` y `lock_max_drot_deg` de su promedio.

##### 18. `dejarik/one_euro.py` (Create, P1)

*   **Cambios:**
    *   `class OneEuro(min_cutoff, beta, d_cutoff)`, con `__call__(x: np.ndarray, t: float) -> np.ndarray`;
    *   `class PoseFilter`: filtra la traslación con un OneEuro de 3 componentes y la rotación como cuaternión (corrige el signo, filtra 4 componentes y renormaliza);
    *   funciones `rvec↔quat` con `cv2.Rodrigues`.

##### 19. `dejarik/hands.py` (Create, P3)

*   **Cambios:**
    *   `class HandTracker(model_path, cfg)` con `HandLandmarkerOptions(base_options=BaseOptions(model_asset_path=...), running_mode=VIDEO, num_hands=1)`. La entrada es `mp.Image(image_format=SRGB, data=cvtColor(small, BGR2RGB))` y `timestamp_ms` es el `t` del cuadro. Si el `frame_id` no cambió desde la última vez, se saltea (MediaPipe exige timestamps estrictamente crecientes);
    *   `class Pinch` con histéresis y tiempo mínimo;
    *   `hands_loop(bus, hands_box, on_tap, stop)`:
        *   toma el último cuadro (`bgr`) y lo achica;
        *   obtiene el landmark 8 en píxeles de la imagen completa (`x·1280`, `y·720`);
        *   aplica `undistortPoints` y la homografía `H⁻¹` de la pose actual;
        *   pasa el punto por `cell_at`;
        *   publica `hand` en `hands_box`;
        *   cuando se completa un pinch, llama a `on_tap(cell)` (ver "Hilos y datos compartidos").
    *   Si la pose no está ok, `cell = None` y los gestos de pinch no tienen efecto. Con `--replay` no hay hilo de manos.

##### 20. `dejarik/game.py` (Create, P2)

*   **Cambios:**
    *   dataclasses `Piece(id, owner, kind, cell, hp, alive)` y `State(turn, phase, pieces, selected, winner, rng_state, next_event_id)`, con `phase ∈ {select, target, over}`; `animating` no es una fase del juego (ver `protocol.state_msg`);
    *   `KINDS`, `INITIAL`, `new_game(seed) -> State`. Ids de pieza: 0–3 del jugador 0 y 4–7 del jugador 1, en el orden de la tabla. `game.py` carga `board.load_spec()` una vez al importarse;
    *   `legal_targets(state, piece_id) -> {"moves": [...], "attacks": [...]}`, con BFS sobre `neighbors` hasta MOV pasos por casillas vacías;
    *   `apply(state, action) -> (State, list[Event])`:
        *   acciones: `("tap", cell)` y `("reset",)` (`reset` usa `seed + 1`);
        *   `tap` según la fase:
            *   `select` + pieza propia del turno → `selected = pieza`, fase `target`, sin eventos;
            *   `select` + cualquier otra cosa → sin cambios;
            *   `target` + otra pieza propia → cambia la selección;
            *   `target` + casilla vacía legal → mover;
            *   `target` + casilla legal con rival → atacar;
            *   `target` + cualquier otra casilla o `None` → `selected = null`, fase `select`, sin eventos;
            *   `over` → se ignora;
        *   eventos (`Event = dict`): los de `docs/protocol.md`, en su orden fijo;
    *   `to_json(state)` y `from_json(s)`. `to_json` convierte `rng_state` (tuplas de `getstate()`) en listas y `from_json` lo vuelve a tuplas;
    *   sin cv2 ni I/O.

##### 20b. `dejarik/ai.py` (Create, P2)

*   **Cambios:**
    *   `win_prob(atk, dfn) -> (p_hit, p_counter)` recorre las 36 combinaciones de dados;
    *   `score(state, piece, action) -> float` con la heurística del Technical Plan;
    *   `choose(state) -> list[("tap", cell)]`. Los empates se rompen por el menor `(piece_id, casilla)`, sin RNG;
    *   los pesos de la heurística son constantes al principio del archivo;
    *   la distancia es un BFS sobre `adjacency` que no tiene en cuenta las casillas ocupadas;
    *   Python puro, que solo depende de `game.py` y `board.py`.
*   **Por qué:** el modo contra la PC tiene que poder testearse sin red ni cámara.

##### 20c. `dejarik/tunnel.py` (Create, P4)

*   **Cambios:**
    *   `start(port, cloudflared_path) -> str | None`:
        *   lanza `cloudflared tunnel --no-autoupdate --url http://127.0.0.1:<port>` con `subprocess.Popen`;
        *   un hilo daemon lee la salida de error línea por línea durante toda la vida del proceso: busca `https://[a-z0-9-]+\.trycloudflare\.com`, guarda la URL, activa un `threading.Event` y escribe todo en `recordings/cloudflared.log`. Si nadie vaciara esa salida, el buffer se llena y `cloudflared` se traba;
        *   `start` espera con `event.wait(20)`; si encuentra la URL la devuelve, si no devuelve `None`;
    *   `alive() -> bool` (el proceso sigue vivo);
    *   `stop()`.
*   Un túnel rápido falla si existe `%USERPROFILE%\.cloudflared\config.yml`; el README lo avisa.
*   **Por qué:** el anfitrión solo corre un comando y obtiene el link, sin manejar el túnel a mano.

##### 21. `dejarik/protocol.py` (Create, P4)

*   **Cambios:**
    *   `encode_frame(frame_id, t, jpeg_bytes, pose, K, size, hand, debug=None) -> bytes`, con el formato `[uint32 BE N][header JSON][JPEG]`;
    *   `decode_frame(b) -> (header, jpeg)`, usado en los tests y en el replay;
    *   `state_msg(state, animating)`: manda `phase:"animating"` mientras `transport` tiene eventos sin confirmar, y `legal` = `legal_targets(state, selected)` (o `[]`);
    *   `events_msg(events)`, `hello_msg(you, mode, remote=None)` (`remote` con `url`, `tunnel` y `connected`, solo para el anfitrión), `denied_msg(reason)`;
    *   `parse_client(text) -> dict`, que valida `v == 1`, acepta `click`, `anim_done`, `key` y `frame_ack`, y descarta lo demás.

##### 22. `dejarik/recording.py` (Create, P4)

*   **Cambios:** formato `.dj` = JSONL, una línea por cuadro saliente hacia el anfitrión: `{"dt_ms":int,"data":<base64>}` (header + JPEG). No se graban `state` ni `events`.
    *   `Recorder(path).write(data)`;
    *   `read_dj(path) -> Iterator[(dt_ms, bytes)]`;
    *   `replay(path, bus, flags, stop)` decodifica cada cuadro con `decode_frame` y publica en el `frame_bus` un paquete con la misma forma que `vision_loop` (pose del header, JPEG de 720p y, si hay remoto, el de 480p recodificado), respetando `dt_ms`, en loop. `game` corre en vivo.
*   **Por qué:** sirve como respaldo en la demo y como fixture para desarrollar sin cámara.

##### 23. `dejarik/transport.py` (Create, P4)

*   **Cambios:**
    *   `class LatestBox` (lock + último valor), que se usa como `frame_bus` y como `hands_box`;
    *   un único servidor `websockets.asyncio.server.serve(handler, "127.0.0.1", 8000, process_request=..., max_size=1024, compression=None)`. `max_size` cierra solo los mensajes de más de 1 KB, y sin compresión no se gasta CPU en desinflar JPEG:
        *   `process_request(connection, request)` devuelve `None` para `/ws`. Para el resto sirve archivos de `web/`: la ruta es `(WEB / unquote(urlsplit(request.path).path).lstrip("/")).resolve()`, y si no queda `is_relative_to(WEB)` o no es un archivo, responde 404. `/` sirve `index.html`. Responde con `websockets.http11.Response` y el `Content-Type` de `mimetypes.guess_type`; al importar se llama a `mimetypes.add_type("text/javascript", ".js")` y `mimetypes.add_type("model/gltf-binary", ".glb")`, porque en Windows el registro suele dar `text/plain` para `.js` y Chrome rechaza los módulos;
        *   el handler de `/ws` lee `p` y `k` de `connection.request.path`, compara el token con `secrets.compare_digest` (`host_token` para `p=0`, `remote_token` para `p=1`) y, si no corresponde, hace `await connection.close(4401)`; si ya hay un `p=1`, `close(4409)`. El código de cierre solo existe después del handshake, por eso no se rechaza en `process_request`;
    *   roles: `host` (`p=0`) y `remote` (`p=1`);
    *   en cada conexión manda `hello` y el `state` completo, y arranca una tarea de envío por conexión: 720p para el anfitrión, y 480p con un máximo de `net.remote_max_fps` para el remoto. La tarea del remoto no manda un cuadro nuevo mientras haya 2 sin `frame_ack`;
    *   `can_act(role, mode, state.turn) -> bool`, según la tabla de modos;
    *   recibe `click` (lo pasa por `cell_at` y aplica `("tap", cell)` si `can_act`; si no, manda `denied`), `anim_done` (solo del anfitrión), `frame_ack` (solo del remoto) y `key` (solo del anfitrión; `mode` rota el modo y manda `hello` a todos);
    *   mientras `pose.ok=false` se ignoran los clics y los pinch;
    *   cualquier cambio de modo cancela la tarea pendiente del rival automático;
    *   manda `hello` al anfitrión cuando se conecta o se desconecta el `p=1`, y cuando cambia `tunnel.alive()`, que se consulta cada 2 s;
    *   bloqueo de entrada mientras haya eventos sin confirmar. El timeout de `anim.anim_timeout_s` se reinicia con cada `anim_done` y con cada tanda nueva; si vence, se dan por confirmados todos los pendientes;
    *   en modo `cpu`, cuando es el turno 1 y no hay eventos pendientes, programa `ai.choose` con la espera de "pensar" y aplica los taps con la separación configurada;
    *   después de cada `apply`, guarda `save/state.json` y manda `state` + `events` a todas las conexiones;
    *   si se pidió `--record`, graba cada mensaje binario `frame` que sale hacia el anfitrión.

**Hilos y datos compartidos.**

*   El paquete del `frame_bus` es `{frame_id, t, bgr, host_msg, remote_msg | None, pose}`. `bgr` es el cuadro crudo, para `hands`; `host_msg` y `remote_msg` ya vienen codificados con `encode_frame`.
*   Un objeto `Flags` con `threading.Event`: `remote_connected` (para codificar 480p solo si hace falta), `debug_on` (para incluir `debug`) y `lock_toggle` (la tecla `L`, que llega por asyncio y la lee `PoseEstimator`).
*   Después de publicar, `vision_loop` hace `loop.call_soon_threadsafe(frame_event.set)`, que despierta a las tareas de envío.
*   Un pinch llega al juego con `loop.call_soon_threadsafe(transport.on_host_tap, cell)`, que pasa por los mismos controles que un clic del anfitrión.

#### Navegador `web/`

##### 24. `web/vendor/three/` (Create, L)

*   **Cambios:** Three.js r169, copiado con la misma estructura que el original: `build/three.module.js`, `examples/jsm/loaders/GLTFLoader.js` y `examples/jsm/utils/{BufferGeometryUtils,SkeletonUtils}.js` (`GLTFLoader` importa `../utils/` de forma relativa). El `importmap` de `index.html` mapea `three` → `./vendor/three/build/three.module.js` y `three/addons/` → `./vendor/three/examples/jsm/`. `SkeletonUtils` se importa como `import * as SkeletonUtils from 'three/addons/utils/SkeletonUtils.js'`.

##### 25. `web/index.html` (Create, L)

*   **Cambios:** el canvas WebGL, el canvas 2D de debug, el HUD en HTML, el `importmap`, los `<audio>` y la carga de `main.js` como módulo.

##### 26. `web/style.css` (Create, L)

*   **Cambios:**
    *   el canvas con la relación de aspecto fija y bandas negras;
    *   la estética del HUD (azul y rojo, tipografía monoespaciada, brillo);
    *   el aviso de "tracking perdido";
    *   la pantalla de victoria.

##### 27. `web/net.js` (Create, L)

*   **Cambios:**
    *   conexión WebSocket a `(wss|ws)://location.host/ws` + `location.search`, con reintento cada 1 s. Si se cierra con el código 4401, no reintenta y muestra "Link inválido"; con 4409, no reintenta y muestra "Ya hay un jugador 1";
    *   maneja `hello` (rol y modo) y `denied`;
    *   parsea el binario: lee N con `DataView`, decodifica el header con `TextDecoder` y arma la imagen con `createImageBitmap(new Blob([jpeg], {type: "image/jpeg"}), {imageOrientation: "flipY"})` (WebGL ignora `texture.flipY` con `ImageBitmap`);
    *   el remoto contesta cada cuadro con `frame_ack`;
    *   despacha `frame`, `state` y `events` a callbacks;
    *   `send(obj)`.

##### 28. `web/scene.js` (Create, L)

*   **Cambios:**
    *   el renderer;
    *   la cámara con `setProjectionFromK(K, w, h)`. Con `n = 0.01` y `f = 10`, la matriz por filas es `[[2fx/w, 0, 1−2cx/w, 0], [0, 2fy/h, 2cy/h−1, 0], [0, 0, −(f+n)/(f−n), −2fn/(f−n)], [0, 0, −1, 0]]`, y después `projectionMatrixInverse.copy(P).invert()`;
    *   el plano de fondo con una sola textura que se reutiliza: se cambia `.image`, se marca `needsUpdate` y se llama a `close()` sobre el `ImageBitmap` anterior;
    *   los grupos `board` (`matrixAutoUpdate = false`) y `boardY`;
    *   `applyPose(T, ok)`: `board.matrix.fromArray(T)` y `board.matrixWorldNeedsUpdate = true` (con `matrixAutoUpdate = false`, sin eso el tablero no se mueve), más el desvanecimiento por pérdida de tracking;
    *   el disco que solo escribe profundidad;
    *   los anillos y casillas emisivos, con `highlight(cells)`;
    *   `boardPointFromClick(event) -> {x, y} | null`, por raycast al disco (hijo de `board`, no de `boardY`), con las coordenadas NDC calculadas sobre el rectángulo del video sin las bandas negras, y devuelto con `board.worldToLocal`.

##### 29. `web/hologram.js` (Create, L)

*   **Cambios:** `makeHologramMaterial(color)`, un `MeshBasicMaterial` extendido con `onBeforeCompile`, que ya trae el esqueleto: se inyectan el brillo de borde (fresnel), las scanlines y el parpadeo controlados por `uTime`. `transparent = true`, `blending = AdditiveBlending`, `depthWrite = false`.

##### 30. `web/creatures.js` (Create, L)

*   **Cambios:**
    *   `viewer(kind)`: con `?viewer=<kind>` en la URL muestra solo esa criatura sobre fondo negro, con botones para cada clip. Se usa para revisar lo que produce la IA;
    *   `loadKinds()` carga un `.glb` por `kind` desde `assets/creatures/<kind>.glb`. Si el archivo falta, usa una cápsula provisoria con los mismos nombres de clip, para no frenar el desarrollo;
    *   `spawn(piece)` crea la copia con `SkeletonUtils.clone`, su mixer y un material holográfico **propio** por malla (con `traverse`), del color del bando; `clone` comparte los materiales y cada criatura necesita su `uTime` y su disolución;
    *   `play(id, clip, {loop}) -> Promise`: hace `reset().play()` de la acción nueva y `crossFadeTo` desde la anterior. Los clips de una vez (`attack`, `hit`, `die`) usan `setLoop(LoopOnce, 1)` y `clampWhenFinished = true`, y la promesa se resuelve con el evento `finished` del mixer filtrado por `e.action`. Los clips en loop resuelven al terminar el fundido;
    *   `moveTo(id, x, y, ms)`;
    *   `syncFromState(state)` corrige las posiciones si la pantalla y el estado no coinciden (por ejemplo, después de reconectar).

##### 31. `web/events.js` (Create, L)

*   **Cambios:** una cola que reproduce los eventos en orden, cada uno como una `Promise`:
    *   `move`: girar y caminar hasta el centro de la casilla, después `idle`;
    *   `attack`: girar hacia el objetivo, `attack`, mostrar las tiradas en el HUD y sonido;
    *   `hit`: clip `hit`, destello y sacudida de cámara;
    *   `death`: `die`, disolución y partículas, y después la pieza se retira;
    *   `turn`: actualiza el HUD y manda `anim_done` enseguida;
    *   `win`: pantalla de victoria y sonido.

    Al terminar cada evento manda `anim_done(id)`. Con el primer `pose.ok` reproduce la animación de "encendido" y el sonido `boot`.

##### 32. `web/hud.js` (Create, L)

*   **Cambios:** el rol ("Sos el jugador N"), el modo, "Turno del rival" o "La PC está pensando…", y para el anfitrión el link remoto con un botón de copiar y el estado del remoto. También el turno con el color del bando, la vida de cada pieza (en una barra lateral), la última tirada ("Bestia 3+5=8 vs Guardián 2+3=5 → golpe"), el aviso de entrada ilegal, el aviso "Túnel no disponible" y la pantalla de victoria. Colores: jugador 0 azul, jugador 1 rojo.

##### 33. `web/debug.js` (Create, L con P1)

*   **Cambios:** con la tecla `D` alterna el overlay 2D, que dibuja:
    *   las esquinas de los marcadores con sus IDs;
    *   los ejes proyectados;
    *   la grilla de casillas proyectada con K y T;
    *   la pose cruda contra la filtrada;
    *   el punto del dedo;
    *   un panel con fps, ms por etapa, `reproj_px`, `n_markers`, `locked` y el ratio de pinch.

##### 34. `web/main.js` (Create, L)

*   **Cambios:**
    *   conecta los módulos y el loop `requestAnimationFrame`;
    *   el clic llama a `boardPointFromClick` y manda `click`;
    *   las teclas `D`, `L`, `R` y `P` mandan `key`. En el remoto solo funciona `D`, que es local;
    *   en el remoto no se mandan `anim_done`;
    *   al recibir el `state` llama a `syncFromState` y `highlight(legal)`;
    *   resalta `frame.hand.cell` con un estilo de "hover" distinto (CUJ 3);
    *   al recibir los `events` los pone en la cola.

##### 35. `web/assets/creatures/{guardian,bestia,acechador,soldado}.glb` (Create: monstruos de Quaternius CC0 adaptados con `tools/adapt_glb.py`; la IA de Blender solo si falta un clip; operador P4, revisión L)

*   **Cambios:**
    *   modelos producidos por la IA que pasan `tools/check_glb.py` y la revisión visual en el visor;
    *   pueden repetirse modelos entre tipos si solo se consiguen 2;
    *   el `.blend` fuente de cada uno se guarda en `assets_src/` para poder regenerarlo.
*   **Por qué:** el líder deja de hacer modelos y se dedica a `web/`, que era el cuello de botella. P4 maneja la IA y el líder solo aprueba el resultado.

##### 35b. `tools/check_glb.py` (Create, P4)

*   **Cambios:**
    *   lee el `.glb` como JSON más el binario, sin dependencias nuevas, siguiendo la especificación de glTF;
    *   verifica:
        *   el tamaño del archivo;
        *   que no use Draco;
        *   que estén los 5 nombres de clip;
        *   que haya un solo esqueleto, o ninguno con animación por objeto;
        *   la altura (30–70 mm), el círculo de 44 mm y que el origen esté en la base, en el primer cuadro de `idle`: deforma las mallas con su esqueleto vértice por vértice (la pose de bind suele ser en T y no es la que se ve);
    *   termina con código 1 y un mensaje concreto por cada falla. Ese mensaje es el que se le devuelve a la IA.
*   **Por qué:** el criterio de aceptación tiene que ser mecánico, porque el que produce los modelos no es una persona.

##### 35a. `tools/adapt_glb.py` (Create, P4)

*   **Cambios:** renombra los clips de un monstruo animado (Quaternius y similares) a `idle/walk/attack/hit/die`, descarta los demás, agrega un nodo raíz con la escala que lo hace entrar en el círculo de 44 mm (máximo 70 mm de alto) y lo apoya en y = 0. No toca geometría ni animaciones. Termina corriendo `check_glb`.
*   **Por qué:** con modelos que ya vienen animados, la adaptación es mecánica y no necesita Blender.

##### 35c. `assets_src/*.blend` (Create, P4)

*   **Cambios:** los archivos fuente de Blender de cada criatura y el prompt usado (`<kind>.prompt.md`).

##### 36. `web/audio.js` (Create; reemplaza a `web/assets/sfx/*.ogg`)

*   **Cambios:** cada sonido es una función chica con osciladores y ruido filtrado (`boot`, `select`, `step`, `dice`, `attack`, `hit`, `death`, `turn`, `win`, `denied`) más un zumbido de fondo. Volumen general en `VOLUME`. `?soundcheck` renderiza cada sonido offline y muestra su pico, para detectar sonidos mudos sin parlantes.
*   **Por qué:** no hay archivos que buscar, licenciar ni empaquetar, y el estilo sintético encaja con el holograma.

#### Otros archivos

##### 37. `models/hand_landmarker.task` (Create, P3)

*   **Cambios:** el modelo oficial de MediaPipe, descargado una vez de `https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task` y guardado en el repo.

##### 38. `fixtures/session_01.dj` (Create, P4)

*   **Cambios:** generado por `tools/fake_session.py` el día 2. Se reemplaza el día 9–10 por una grabación real hecha con `--record`.

#### Tests

##### 39. `tests/test_board.py` (Create, P1)

*   **Cambios:**
    *   que la adyacencia sea simétrica;
    *   que el centro tenga 12 vecinas, una casilla interna 4 y una externa 3;
    *   que `cell_at(cell_center(c)) == c` para las 25 casillas;
    *   que `cell_at` devuelva `None` fuera de `r2`;
    *   que `marker_corners` tenga z = 0 y el lado esperado.

##### 40. `tests/test_vision.py` (Create, P1)

*   **Cambios:** tests sintéticos sin cámara:
    *   se proyectan las esquinas del spec con una pose conocida;
    *   se agrega ruido de 0,3 px;
    *   con la cámara a 0,6 m y 40° de inclinación, el estimador recupera la pose con error < 2 mm y < 1°, con todos los marcadores y con solo 2;
    *   `to_view_matrix` sobre la identidad da `diag(1,-1,-1,1)`;
    *   una pose con error de reproyección alto se rechaza.

##### 41. `tests/test_one_euro.py` (Create, P1)

*   **Cambios:**
    *   una señal constante con ruido sale con menor varianza;
    *   un escalón se sigue en menos de 10 muestras a 30 Hz, con los valores iniciales de `[filter.t]`;
    *   un cuaternión que cambia de signo no provoca saltos.

##### 42. `tests/test_game.py` (Create, P2)

*   **Cambios:**
    *   la posición inicial es correcta;
    *   un movimiento con MOV 2 no atraviesa casillas ocupadas;
    *   un ataque solo puede ir a una casilla adyacente;
    *   con una semilla fija, las tiradas y los resultados (golpe, contragolpe, empate) son los esperados;
    *   una pieza con HP 0 muere;
    *   la victoria llega al eliminar las 4 rivales;
    *   `tap` en una casilla ilegal: en fase `target` solo deselecciona; en fase `select` no cambia nada;
    *   `from_json(to_json(s)) == s`;
    *   200 partidas al azar (semillas 0–199) terminan sin excepciones ni estados ilegales.

##### 42b. `tests/test_ai.py` (Create, P2)

*   **Cambios:**
    *   `win_prob(3, 1)` coincide con el valor calculado a mano;
    *   con un rival de 1 HP adyacente y `p_hit ≥ 0,5`, el rival automático ataca;
    *   sin rivales cerca, el rival automático reduce la distancia;
    *   `choose` siempre devuelve una acción legal, en 200 estados al azar;
    *   el rival automático contra sí mismo termina 200 partidas sin excepciones, y se registra cuánto duran para calibrar el objetivo G2 (partida de 6 a 8 minutos);
    *   el rival automático contra un jugador al azar gana más del 80% de las partidas, con las semillas 0–199.

##### 42c. `tests/test_transport.py` (Create, P4)

*   **Cambios:**
    *   la tabla de `can_act` completa (3 modos × 2 roles × 2 turnos);
    *   el rol según la URL: `p=0` sin `host_token` o con uno equivocado se cierra con 4401; `p=1` con un token equivocado, con 4401; un segundo `p=1`, con 4409;
    *   `process_request` no sirve `/../dejarik/game.py` ni `/%2e%2e/dejarik/game.py`;
    *   un mensaje de más de 1 KB cierra la conexión;
    *   la tarea de envío del remoto se detiene con 2 cuadros sin `frame_ack`;
    *   un `P` durante la espera de "pensar" del rival automático hace que no se aplique ningún tap suyo.

##### 43. `tests/test_protocol.py` (Create, P4)

*   **Cambios:**
    *   `decode_frame(encode_frame(...))` devuelve lo mismo que se codificó;
    *   un mensaje con `v ≠ 1` o un tipo desconocido se descarta;
    *   `read_dj` sobre un `.dj` recién grabado devuelve los mismos bytes.

### Calendario y dependencias

| Días | Entregable | Responsable |
|---|---|---|
| 1–2 | Archivos 1–10, `board.py` y `make_board.py` (con el tablero ya impreso y medido), `calib.npz`, `protocol.encode_frame/decode_frame` (P4), `fake_session.py` y `session_01.dj`. | Todos |
| 3–5 | `vision.py` y `one_euro.py` con sus tests · `game.py` con sus tests · `protocol.py`, `transport.py` y `__main__.py` · `scene.js` y `net.js`. **Control día 5:** un cubo anclado sobre el tablero real a través del WebSocket. Si falla, se evalúa Panda3D. | P1 · P2 · P4 · L |
| 2–4 | **Criaturas:** P4 elige 4 monstruos de Quaternius (lista medida en `docs/assets_checklist.md`), los adapta con `tools/adapt_glb.py` y los deja en `web/assets/creatures/`. La IA de Blender queda para agregar clips faltantes. **Control día 7:** las 4 se ven bien en el visor `?viewer=`. | P4 (revisa L) |
| 6–10 | `creatures.js` con cápsulas provisorias y visor `?viewer=`, `events.js`, `hud.js` y `hologram.js` · `hands.py` · `recording.py` · la IA genera las otras 3 criaturas. **Control 1 (día 10):** partida completa con mouse sobre video en vivo. | L · P3 · P4 |
| 8–12 | `ai.py` y `test_ai.py` (modo `cpu`) · roles, modos y video de 480p en `transport.py`, más `tunnel.py`. **Control día 12:** un integrante juega una partida remota desde su casa, por Teams, con la pantalla compartida. Se miden los fps del remoto, la latencia del clic y cómo se ve el shader a través de Teams. | P2 · P4 · L |
| 11–16 | Criaturas reales, sonido, `debug.js`, ajuste de la mano. **Control 2 (día 16):** se decide si la interacción es con la mano o con un puntero con marcador. Se graba el MP4 de respaldo. | L · P3 · P4 · P1 |
| 17–18 | Ajuste de `KINDS` según la duración de las partidas en los ensayos. **Congelamiento de funciones y de arte el día 18.** | Todos |
| 19–23 | Ensayos por Teams los días 19, 21 y 23, con los tres modos: uno cortándole la red al remoto a mitad de partida, otro arrancando con la PC del anfitrión apagada. Se cronometra cada respaldo. Diapositivas. | Todos |
| 24 (26/11) | Demo. | Todos |

### Verification Plan

*   **Build:** no hay paso de build. `python -m dejarik --no-browser` arranca sin errores y `http://127.0.0.1:8000` carga.
*   **Unit tests:** `pytest -q` en verde antes de cada merge a `main`. Cubre `board`, `vision` sintético, `one_euro`, `game`, `ai`, `transport` y `protocol`.
*   **Lint:** no se exige; el tiempo va a tests y ensayos.
*   **Cobertura:** sin un porcentaje fijo. Cada regla de `docs/rules.md` tiene que tener al menos un test en `test_game.py`.
*   **Integración:** `python -m dejarik --replay fixtures/session_01.dj` muestra el video en loop con el tablero anclado, y se juega una partida completa con mouse.
*   **Aceptación en la casa del anfitrión, por Teams** (días 19–23, contra los criterios del brief):
    *   **Alineación:** con el overlay `D`, la grilla reproyectada queda a menos de 3 px de la impresa y el error de reproyección es menor a 2 px.
    *   **Temblor:** con la cámara quieta, la desviación de la traslación filtrada es menor a 1 mm durante 10 s. Se registra con `--record` y se analiza con un script de un solo uso.
    *   **Oclusión:** tapando con la mano 6 de los 12 marcadores, `ok` se mantiene en `true`.
    *   **Mano:** 10 intentos por anillo, con al menos 9 casillas correctas, y 60 s con la mano quieta sin ningún pinch falso.
    *   **Arranque:** desde la máquina apagada, la partida está jugable en menos de 2 minutos en `cpu` y `local`, aun sin red.
    *   **Remoto:** desde otra casa, ≥ 15 fps y clic reflejado en < 500 ms. Un link con un token equivocado recibe cierre 4401 y ningún cuadro.
    *   **Contra la PC:** el rival automático juega dentro de 1,5 s y gana al menos 1 de cada 5 partidas contra un integrante.
    *   **Cambio de modo:** `P` en medio de una partida no pierde el estado.
    *   **Respaldos:** cada uno se activa en menos de 30 s, cronometrado.

--------------------------------------------------------------------------------

*Drafted with EGM*
