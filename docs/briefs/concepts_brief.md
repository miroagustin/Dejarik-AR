# Dejarik AR — TP integrador de Visión Artificial

* **Author:** miroagustin
* **Date:** 2026-11-02
* **Entrega:** 2026-11-26 (24 días) · 5 integrantes

## Overview

Juego de dejarik (el holoajedrez de Star Wars) en realidad aumentada sobre un tablero circular impreso. Una webcam enfoca el tablero, Python calcula la pose del tablero y aplica las reglas del juego, y el navegador dibuja encima criaturas 3D animadas que se mueven y pelean.

La consigna de la cátedra pide una aplicación de RA con modelos 3D animados, hecha con las técnicas vistas en clase. Según el profe, suma más que sea llamativa y entretenida. Lo que más se valora es la demo en vivo; se pueden sumar unas diapositivas breves.

El TP anterior del grupo fueron cartas de Yu-Gi-Oh peleando sobre marcadores ArUco, y el profe lo trató como poca cosa. Este trabajo tiene que mostrar, desde los primeros segundos de la demo, qué agrega frente a aquel:

- reglas y turnos de verdad
- tracking estable de todo el tablero
- interacción con la mano
- animaciones de combate

**Arquitectura elegida:**

- **Python (notebook)** se encarga de:
  - la captura de la webcam (es el único proceso que abre la cámara)
  - la detección con `cv2.aruco`, usando un *board* de 10 o más marcadores
  - `solvePnP` con la cámara calibrada
  - el filtro One-Euro
  - las reglas del juego
  - MediaPipe Hands
- **Navegador (Three.js)** recibe por WebSocket cada cuadro junto con su pose y el estado del juego. Dibuja el video de fondo y las criaturas glTF animadas.
- La demo se proyecta desde la notebook. No hay versión para celular.

## Analysis

Los seis revisores mantienen el concepto: Python más Three.js por WebSocket. Ninguno recomienda Unity ni hacer todo el render en Python. Los riesgos están en lo que el concepto no definía.

### Bloqueantes (decidir en los días 1–2)

**1. Python es dueño de la cámara y manda cada cuadro junto con su pose.**

En Windows, en general solo un proceso puede abrir la webcam a la vez. Pero aunque el navegador pudiera mostrar su propio video, ese video y la pose de Python vendrían de cuadros distintos y las criaturas "patinarían" sobre el tablero.

La solución es que Python mande un único mensaje WebSocket binario por cuadro, con:
- el JPEG del cuadro
- un encabezado JSON con la pose de ese mismo cuadro
- un `frame_id`

Reglas para el envío y el dibujo:
- Mandar siempre solo el cuadro más nuevo. Si los mensajes se encolan, la demora crece sin parar.
- El navegador decodifica el cuadro con `createImageBitmap`.
- El tráfico es de 1,5 a 3 MB/s en la misma máquina, así que no es un problema.

**2. La conversión de coordenadas de OpenCV a Three.js se hace en un solo lugar.**

Los dos usan ejes distintos:
- OpenCV: x a la derecha, y hacia abajo, z hacia adelante.
- Three.js: y hacia arriba, z hacia atrás.

Si cada lado convierte un poco, se pierden días con modelos espejados o dados vuelta. La propuesta:

- **Python** manda la matriz tablero→cámara (4×4) con `diag(1,-1,-1,1)` ya aplicado. También manda K y el tamaño de la imagen.
- **Three.js:**
  - Al grupo del tablero se le pone `matrixAutoUpdate=false`.
  - `camera.projectionMatrix` se arma directamente a partir de K, incluido el punto principal. Un `fov` solo no alcanza para representarlo.
  - No hay que llamar a `updateProjectionMatrix()`, porque pisa la matriz armada.
  - Hay que actualizar `projectionMatrixInverse` para que funcione el raycast.
- **Canvas:** tiene que tener la misma relación de aspecto que el cuadro, sin `object-fit: cover`, que recorta la imagen y rompe la alineación.

**Prueba de aceptación (día 2):** un cubo y unos ejes en el origen quedan pegados a la cruz impresa del tablero, con menos de 3 px de error, mientras se mueve la cámara.

**3. Un solo `board_spec.json` con la geometría del tablero.**

Contiene:
- IDs y tamaño en mm de los marcadores
- esquinas de cada marcador en el sistema del tablero
- radios de los anillos
- 12 sectores, con ángulo de inicio y sentido
- casillas: 0 es el centro, 1 a 12 el anillo interno, 13 a 24 el externo
- adyacencias entre casillas

De ese archivo salen o lo leen todos: el PDF para imprimir, el `cv2.aruco.Board`, la casilla bajo el dedo, el grafo del juego y la posición de las casillas en Three.js.

Para imprimir:
- Imprimir al 100%, nunca con "ajustar a página".
- Agregar una regla de 100 mm en la hoja, medirla después de imprimir y anotar la medida real en la config.
- Usar papel mate pegado sobre foamboard.

**4. Formato de mensajes con versión, archivos de ejemplo y modo replay.**

Cada mensaje empieza con `{"v":1,"type":...,"t":ms,"frame_id"}`.

De Python al navegador:

| Tipo | Contenido |
|---|---|
| `pose` | `{T[16], K, size, ok, n_markers}` |
| `state` | `{turn, phase, pieces[{id,owner,kind,cell,hp,alive}], selected, legal[], winner}` |
| `event` | `{id, kind: move\|attack\|hit\|death, piece, from, to, result}` |
| `hand` | `{cell\|null, pinch, px}` |

Del navegador a Python:
- `click{cell}`: el clic del mouse, como alternativa a la mano
- `anim_done{id}`: aviso de que terminó una animación

Con mensajes grabados de una sesión real, el render se desarrolla sin cámara y la parte de Python sin navegador.

**5. Las reglas escritas en una página el día 2.**

"Basadas en Galaxy's Edge" no alcanza para programar. Hace falta definir:
- estadísticas de cada pieza
- cómo se mueve una pieza: por el anillo, entre anillos, a través del centro, y si puede saltar
- qué se hace en un turno: una sola acción, o mover y además atacar
- cómo se resuelve un combate: dado, o ataque contra defensa
- si el atacante pasa a ocupar la casilla atacada
- cómo se gana

Tienen que poder explicarse al público en 20 segundos.

Propuesta mínima: mover 1 o 2 casillas, atacar a una pieza adyacente, resolver con dado o ataque contra defensa, y gana el último bando que quede en pie. Son unas 100 líneas de Python.

**6. Definir la demo antes de construirla.**

- Un guion de 3 a 5 minutos:
  1. el tablero "se enciende"
  2. aparecen las criaturas
  3. se hace un movimiento
  4. hay un combate en menos de 90 segundos
  5. se tapa un marcador y el tracking se recupera
  6. alguien gana
- Criterios de aceptación medibles (tabla más abajo).
- Para el día 5: un cubo estable sobre el tablero, de punta a punta, con la pose calculada en Python.

### Riesgos importantes

**Las criaturas animadas son la tarea más lenta.**

El auto-rig de Mixamo solo funciona con figuras humanoides, y la mayoría de los monstruos no lo son. El plan:

- **Modelos:** 2 a 4 tipos de criatura que ya vengan animados (Quaternius CC0, Sketchfab). Se repiten en los dos bandos y se tiñen de rojo y de azul.
- **Clips:** cada criatura necesita 5, llamados exactamente `idle`, `walk`, `attack`, `hit` y `die`.
- **Checklist de exportación:**
  - formato `.glb`
  - +Y hacia arriba
  - 1 unidad = 1 m
  - menos de 5 MB
  - sin Draco, salvo que el decoder esté guardado localmente

  Con el checklist, un integrante que solo sabe Python puede convertir los modelos.
- **Mientras tanto:** hasta el día 10 se usan cápsulas provisorias con los mismos nombres de clip.
- **Congelamiento:** el arte se congela el día 18.
- **En Three.js:**
  - Copiar cada criatura con `SkeletonUtils.clone`, no con `.clone()`.
  - Usar un `AnimationMixer` por pieza.
  - Pasar de un clip a otro con `crossFadeTo`.

**La mano es lo más frágil. El mouse es la entrada principal y la mano un extra.**

- **Error de puntería.** El dedo está por encima del papel, así que proyectarlo hacia abajo introduce un error: la altura del dedo por la tangente del ángulo de la cámara. Un dedo a 3 cm con la cámara a 45° se desvía unos 3 cm, cerca del ancho de una casilla del anillo externo (unos 7,8 cm).
- **Cómo compensarlo:**
  - Resaltar la casilla que está bajo el dedo, para que el jugador corrija solo. Esto es lo que más ayuda.
  - Aceptar el pinch solo cerca de la superficie.
  - Pasar el píxel del dedo por `cv2.undistortPoints` antes de proyectarlo.
- **Detección del pinch** (reemplazado por `docs/designs/hand_interaction.md`):
  - Usar la distancia entre los puntos 4 y 8 dividida por la distancia entre los puntos 0 y 9, para que no dependa de qué tan lejos esté la mano.
  - Aplicar histéresis (`[hands] on/off` en `config.toml`).
  - Exigir que dure unos 300 ms.
  - Seguir una sola mano: `max_num_hands=1`.
- **Estados a definir:** hover, seleccionar, confirmar, cancelar, aviso de casilla ilegal, y qué pasa cuando la mano tapa los marcadores.
- **Alternativa más barata y robusta:** un palito con un marcador ArUco chico como puntero. Además reutiliza PnP.

**Trampas de versión de OpenCV y estabilidad de la pose.**

Desde OpenCV 4.7 ya no existen `estimatePoseBoard`, `estimatePoseSingleMarkers`, `Dictionary_get` ni `DetectorParameters_create`, y casi todos los tutoriales todavía los usan.

La secuencia que funciona hoy:
1. `getPredefinedDictionary`
2. `ArucoDetector`
3. `cv2.aruco.Board`
4. `board.matchImagePoints`
5. `cv2.solvePnP`

Detalles:
- Activar `CORNER_REFINE_SUBPIX`; sin eso la pose tiembla.
- Hacer un solo `solvePnP` con todas las esquinas visibles. No calcular una pose por marcador y promediarlas.
- **Ambigüedad de la pose.** Con muchos marcadores a la vista no molesta. Vuelve cuando las manos dejan solo 1 o 2 visibles. En ese caso, usar `solvePnPGeneric` con IPPE y quedarse con la solución más parecida a la pose anterior.
- **Pose mala.** Descartarla si se ven pocos marcadores o si el error de reproyección supera unos pocos píxeles. Mantener la última pose buena durante unos 0,5 s y después desvanecer las criaturas con un cartel de "tracking perdido".
- **Cámara en trípode.** La pose casi no cambia, así que se puede congelar tras unos segundos estables, y tapar marcadores con la mano deja de romperla. Se descongela para el momento de "levantar el tablero".

**Filtro: solo One-Euro, bien aplicado.**

- No filtrar el `rvec` directamente, porque salta en π.
- Pasar la rotación a cuaternión, cambiarle el signo cuando su producto punto con el anterior sea negativo, filtrar y renormalizar.
- Filtrar también la traslación.
- Ojo con el retraso: demasiado suavizado hace que las criaturas se despeguen del tablero cuando se mueve la cámara.
- Los parámetros `min_cutoff` y `beta` se ajustan en el aula.

**El estado del juego vive solo en Python.**

- Python manda el estado completo y una lista ordenada de eventos.
- El navegador reproduce los eventos y responde `anim_done`.
- Mientras hay una animación en curso, Python ignora la entrada.
- El navegador nunca decide resultados.
- Después de cada jugada, el estado se guarda en JSON, para retomar la partida si Python se cae en medio de la demo.

**Presupuesto de CPU.**

Costo aproximado por cuadro:
- MediaPipe: 15 a 30 ms
- ArUco + PnP a 720p: 5 a 10 ms
- codificar el JPEG: unos 5 ms

En un solo bucle eso da 15 a 25 fps. MediaPipe va en otro hilo, o cada dos cuadros con una imagen más chica, para no frenar la pose.

En Windows:
- Abrir la cámara con `CAP_DSHOW` o MSMF y FOURCC MJPG.
- Instalar un solo paquete de OpenCV: MediaPipe depende de `opencv-contrib-python`, y tenerlo junto con `opencv-python` rompe `cv2`.
- Fijar la versión de MediaPipe, o usar la API Tasks (`HandLandmarker`) con el modelo guardado localmente.
- Fijar Python 3.11 o 3.12 en las 5 máquinas.

**Lo que puede fallar el día de la demo.**

- **Cámara:**
  - Webcam externa (mejor dos iguales), en trípode.
  - Autofoco, exposición y balance de blancos bloqueados.
  - Calibrar con esa misma resolución y ese foco.
- **Materiales:** lámpara, tablero de repuesto, adaptadores HDMI/USB-C y cargador.
- **Todo offline:**
  - three.js, sus loaders y el modelo de MediaPipe guardados en el repo.
  - El venv congelado en la notebook de la demo.
  - Al menos un ensayo con el Wi-Fi apagado.
- **Software:**
  - Un solo comando arranca el servidor y el navegador en pantalla completa.
  - El navegador se reconecta solo.
  - Hay una tecla de reset.

**Mostrar lo llamativo y hacer visibles las técnicas de clase.**

- **Shader de holograma:** brillo azul en los bordes, scanlines, parpadeo. Es una tarde de trabajo y es la mayor señal de "Star Wars".
- **Coreografía del combate:** acercarse, golpear, destello del impacto, disolverse con partículas.
- **Sonido:** con `<audio>`, casi gratis.
- **Intro:** el tablero "se enciende" al detectarlo.
- **HUD:**
  - de quién es el turno
  - casillas legales iluminadas
  - barras de vida
  - resultado del combate
  - pantalla de victoria
- **Overlay de debug con una tecla:**
  - marcadores y ejes
  - grilla reproyectada
  - pose cruda contra pose filtrada
  - rayo del dedo
  - fps y latencias por etapa
  - error de reproyección

  Sirve para diagnosticar en vivo y deja a la vista que PnP y la calibración funcionan.

### Hitos

| Día | Objetivo |
|---|---|
| 1–2 | Congelar `board_spec.json`, el formato de mensajes con ejemplos, la convención de coordenadas, las reglas y el `calib.npz`. Esqueleto del repo. |
| 5 | Cubo anclado de punta a punta. Las reglas pasan los tests de movimiento. |
| 9–10 | **Control 1:** partida completa jugable con mouse sobre video en vivo, con criaturas provisorias o primeras, y shader de holograma. Esto ya supera al Yu-Gi-Oh. |
| 14–16 | **Control 2:** criaturas reales con clips de combate, sonido, pantalla de victoria, primera versión de la mano y video de respaldo. |
| 18 | Se congelan las funciones y el arte. Desde acá, solo arreglos. |
| 19–23 | Ensayos los días 19, 21 y 23: uno con luz fuerte tipo proyector y otro arrancando en frío sin internet. Cronometrar cuánto tarda cambiar a cada respaldo. |
| 24 (26/11) | Demo. |

**Respaldos, en orden.** Cada uno se activa con un flag o una tecla y está ensayado:
1. mano
2. mouse (`--input mouse`)
3. un solo marcador grande (`--single-marker`)
4. replay de una sesión grabada, con el render real (`--replay`)
5. MP4 en un pendrive

### Criterios de aceptación

| Componente | Criterio |
|---|---|
| Calibración | RMS de reproyección < 0,5 px con 15 a 25 vistas del damero (`findChessboardCornersSB`). |
| Tracking | Reproyección < 2 px. Temblor en reposo < 1 mm / 1°. Se sostiene con ~50% de los marcadores tapados. 30 fps a 720p. Reporta `ok=false` en < 200 ms al perder el tablero. |
| Reglas | Cada regla escrita tiene un test en pytest. No se puede llegar a un estado ilegal. |
| Mano | Casilla correcta en ≥ 9 de 10 intentos por anillo. Ningún pinch falso en 60 s de reposo. Latencia < 150 ms. |
| Render | Ejes a menos de 3 px de la cruz impresa. Los 5 clips se reproducen. ≥ 30 fps. Se reconecta cuando Python se reinicia. |
| Integración | El replay da siempre el mismo resultado. Del arranque en frío a la demo en < 2 min. |

### Módulos y roles

Cada módulo depende solo de los archivos compartidos: el spec del tablero, el formato de mensajes y la convención de coordenadas.

| Módulo | Qué hace | Responsable |
|---|---|---|
| `web/` | Render, shaders, HUD, animaciones. Solo muestra lo que recibe. | Líder (Blender / Three.js) |
| `vision/` | Calibración, ArUco, PnP, filtro. Devuelve una pose o `None`. | P1 |
| `game/` | Python puro, sin cv2 ni I/O: `apply(state, action) -> state, events`, con pytest. | P2 |
| `hands/` | MediaPipe y la alternativa con mouse. Devuelve `{cell, pinch}`. | P3 |
| `transport/` e integración | Bucle asyncio con `websockets` y servidor estático. Replay, empaquetado offline, archivos de impresión, conversión de modelos con el checklist, sonido, diapositivas, video de respaldo. | P4 |

### Para las diapositivas

- Una frase sobre qué es el dejarik.
- Un GIF de la demo, que además sirve de respaldo.
- Una tabla de técnicas de clase y dónde se usan:

| Técnica | Uso en el proyecto |
|---|---|
| Calibración | Da la matriz K. |
| ArUco + PnP | Dan la pose del tablero. |
| Homografía | Lleva la punta del dedo a la casilla del tablero. |
| Flujo óptico | Opcional, para suavizar la pose. |
| Segmentación | Extra: máscaras de mano con MediaPipe. |
| Features | No se usan; decirlo con honestidad. |

- Una fila de "qué agrega frente al Yu-Gi-Oh".

## Goals vs. Non-Goals

* **In-Scope Goals:**
  * El tablero queda anclado y estable aunque una mano tape algunos marcadores o se mueva la cámara.
  * Criaturas holográficas animadas, con sonido y una secuencia de combate completa.
  * Una partida simple y completa, de principio a victoria en menos de 3 minutos, que se entiende sin conocer Star Wars.
  * Todo corre en vivo, offline, en una notebook con proyector, arranca con un solo comando y tiene respaldos ensayados.
  * Las técnicas de clase quedan visibles en el overlay de debug y en una diapositiva.
* **Out-of-Scope Non-Goals:**
  * Reglas exactas de Galaxy's Edge.
  * 8 criaturas únicas con rig propio.
  * Celular / iPhone / web móvil, multijugador en red, SLAM.
  * Pantalla de calibración, oclusión de los hologramas por la mano, dashboard de métricas.
  * Kalman además de One-Euro.
  * Lógica del juego en JavaScript.

**Qué recortar primero, en este orden:**
1. la mano (la reemplazan el mouse o el puntero con marcador)
2. reglas completas
3. más de 2 a 4 tipos de criatura
4. tests más allá de adyacencia, combate y victoria
5. pantalla de calibración y métricas

**Nunca recortar:**
- tracking estable
- shader de holograma
- animación de combate
- sonido
- HUD
- plan de respaldo

## Alternatives Weighed

| Alternativa | Motivo del rechazo |
|---|---|
| Web app en el celular con OpenCV.js (brief original) | Rechazada por el autor: el equipo trabaja en Python, hay 24 días, OpenCV.js no trae ArUco en su build estándar y Safari iOS es difícil de depurar. La consigna no exige celular y el equipo aceptó una demo desde la notebook. |
| Unity + AR Foundation | Solo el líder sabe Unity, así que la parte evaluada dependería de una persona. Además el tracking queda como caja negra, mientras que la consigna pide usar las técnicas vistas en clase. |
| Unity como render, con la visión en Python | La conexión de red sigue siendo necesaria y solo una persona puede trabajar el render. |
| pyrender / moderngl / Ursina / Open3D | No reproducen animaciones con esqueleto (o habría que programarlas a mano), tienen soporte flojo para glTF animado, o el resultado se ve pobre. |
| Panda3D (Actor + panda3d-gltf) | Es la única opción todo-Python viable y elimina el WebSocket. Pero nadie la conoce y el look de holograma cuesta mucho más que en Three.js. Queda como plan B si el WebSocket no funciona. |
| El navegador muestra su propio video (getUserMedia) y Python manda solo la pose | Pelean por la cámara en Windows y los cuadros no coinciden, así que las criaturas patinan. |
| Visión en el navegador (OpenCV.js / MediaPipe JS) | Saca las técnicas de clase de Python, que es lo que maneja el resto del equipo. |
| Un solo marcador ArUco | La pose salta entre dos soluciones y no se diferencia del TP de Yu-Gi-Oh. Queda solo como respaldo. |
| Una pose por marcador, promediadas | Da peor resultado que un único `solvePnP` con todas las esquinas. |
| Auto-rig de Mixamo para las criaturas | Solo funciona con humanoides. |
| Kalman para la pose | Es más complejo que One-Euro sin un beneficio visible en la demo. |

## Key Decisions & Staging for Next Steps

**Decisiones tomadas:**
1. **Plataforma:** notebook con webcam externa en trípode y demo proyectada. Sin celular.
2. **División del trabajo:** Python hace captura, visión, reglas y manos. Three.js solo dibuja. Python es la única autoridad sobre el estado del juego.
3. **Transporte:** un mensaje WebSocket por cuadro, con el JPEG y la pose del mismo cuadro; se manda siempre el más reciente.
4. **Coordenadas:** la conversión de OpenCV a Three.js se hace una sola vez, en Python, y queda documentada.
5. **Tracking:** board de 10 o más marcadores con la API de OpenCV ≥ 4.7, un único `solvePnP` y filtro One-Euro sobre cuaterniones.
6. **Entrada:** el mouse es la principal y la mano es un extra que se puede recortar (confirmado por el autor: la mano es negociable).
7. **Arte:** 2 a 4 criaturas ya animadas, con 5 clips de nombres fijos y shader de holograma.

**Pendiente para los días 1–2:**
- Escribir la página de reglas: estadísticas, movimiento, combate y victoria.
- Crear `board_spec.json` e imprimir el tablero.
- Congelar el formato de mensajes v1 y grabar archivos de ejemplo.
- Escribir el guion de la demo.
- Calibrar la webcam de la demo.
- Elegir las criaturas (Quaternius / Sketchfab) y comprobar que tengan los 5 clips.

**Abierto:**
- La regla exacta de combate: dado o ataque contra defensa.
- La mano contra el puntero con marcador como interacción "wow". Se decide en el control 2 (día 14–16), según la precisión medida.
