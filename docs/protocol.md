# Protocolo v1 y convención de coordenadas

**Se congela el día 2.** Agregar un campo opcional no sube `v`, porque cada lado ignora los campos que no conoce. Cambiar o quitar un campo sí: se sube `v` y se cambian Python y el navegador en el mismo commit.

Fuente: [docs/designs/dejarik_ar.md](designs/dejarik_ar.md), secciones "Convención de coordenadas", "Protocolo WebSocket v1" e ítems 7 y 22.

## Coordenadas

**Sistema del tablero**

- Origen en el centro del tablero, unidades en metros.
- **Z hacia arriba**, saliendo del papel.
- **X apunta al centro del sector 1.**
- Los sectores se numeran en sentido antihorario vistos desde arriba.

**Casillas**

| Casillas | Ubicación |
|---|---|
| `0` | Centro |
| `1`–`12` | Anillo interno |
| `13`–`24` | Anillo externo |

La casilla `12+k` queda detrás de la `k`. La geometría está en [board_spec.json](../board_spec.json), y la única función que convierte un punto en casilla es `dejarik.board.cell_at`.

**Pose y conversión a Three.js**

- La pose sale de OpenCV como `[R|t]`, de tablero a cámara: x a la derecha, y hacia abajo, z hacia adelante.
- **Python hace la conversión a Three.js, y es el único lugar donde se hace:** `dejarik.vision.to_view_matrix` manda `T = diag(1,-1,-1,1) · [R|t]` como 16 números en **orden por columnas**, listo para `Matrix4.fromArray(T)`. La traslación queda en `T[12..14]`.

**Escena en Three.js**

- La cámara virtual queda fija en el origen.
- El grupo `board` recibe `T` con `matrixAutoUpdate = false` y `matrixWorldNeedsUpdate = true` después de cada pose.
- Dentro de `board` hay un grupo `boardY` rotado **+90° en X** (`rotation.x = Math.PI / 2`), una sola vez, porque el tablero tiene Z hacia arriba y glTF tiene Y hacia arriba: así +Y del glTF va a +Z del tablero. Las criaturas cuelgan de `boardY`. Un punto `(x, y)` del tablero es `(x, 0, -y)` en `boardY`. (Corregido el día 2: decía −90°, que acuesta a las criaturas hacia abajo.)
- **Proyección.** `camera.projectionMatrix` se arma con `K = [fx, fy, cx, cy]`, `size = [w, h]`, `near = 0.01` y `far = 10`. No se llama a `updateProjectionMatrix()`, y hay que actualizar `projectionMatrixInverse` a mano. En orden por filas:

  ```text
  [ 2fx/w   0       1-2cx/w          0              ]
  [ 0       2fy/h   2cy/h-1          0              ]
  [ 0       0       -(f+n)/(f-n)     -2fn/(f-n)     ]
  [ 0       0       -1               0              ]
  ```

- **Canvas.** Tiene la misma relación de aspecto que el cuadro, con bandas negras si hace falta y sin `object-fit: cover`. El clic se calcula sobre el rectángulo del contenido, sin contar las bandas.

## Mensajes de Python al navegador

### `frame`: binario, uno por cuadro

```text
[uint32 big-endian: largo del header N][N bytes: header JSON UTF-8][resto: JPEG]
```

```json
{"v":1,"type":"frame","frame_id":42,"t":1400,
 "pose":{"ok":true,"T":[1,0,0,0, 0,0.766,0.643,0, 0,-0.643,0.766,0, 0,0,-0.6,1],
         "n_markers":12,"reproj_px":0.4,"locked":false},
 "K":[900,900,640,360],"size":[1280,720],
 "hand":{"cell":null,"pinch":false,"px":null,"hold":0,"box":null}}
```

- `K` y `size` van en todos los cuadros. Para el remoto, se mandan escalados a 854×480.
- `hand.px` es la punta del índice, `[u, v]` en píxeles del cuadro, o `null`.
- `hand.pinch` significa "gesto cerrado" (el nombre queda por v1). `hand.cell` es la casilla resaltada; durante el gesto, la fijada.
- `hand.hold` es el progreso del gesto, de 0 a 1. Vale 1 desde que se confirma hasta que se suelta. Si baja de un valor menor que 1 a 0, el gesto se canceló.
- `hand.box` es `[u0, v0, u1, v1]`, la caja de la mano en píxeles del cuadro, o `null`.
- En el remoto, `px` y `box` van escalados como `K`.
- `hold` y `box` son opcionales para quien lee: los `.dj` viejos no los tienen (`hold ?? 0`, `box ?? null`).
- `debug` solo va cuando el overlay está activo:

  ```json
  "debug":{"corners":[[[u,v],[u,v],[u,v],[u,v]]],"ids":[0],"T_raw":[16 floats],
           "ms":{"read":3,"detect":6,"pnp":1,"filter":0.1,"jpeg":5},
           "hand":{"metric":0.4,"metric2d":0.5,"extended":true,"hold":0.6,"lock_cell":7,"reason":""}}
  ```

  `debug.hand.reason` vale `""`, `"suelta"`, `"salió"`, `"sin mano"` o `"afuera"`. `metric` es `null` cuando el medio está doblado.

### `state`: texto, en cada cambio

```json
{"v":1,"type":"state","turn":0,"phase":"target",
 "pieces":[{"id":0,"owner":0,"kind":"guardian","cell":23,"hp":3,"alive":true}],
 "selected":0,"legal":[22,11],"winner":null}
```

- **`phase`** puede valer `select`, `target`, `animating` u `over`. `animating` no existe en `game`: la agrega `transport` mientras hay eventos sin `anim_done`.
- **`legal`** se calcula con `legal_targets(state, selected)`: casillas para mover más casillas para atacar, o `[]`.
- **Ids de pieza:** del 0 al 3 son del jugador 0 y del 4 al 7 del jugador 1, en el orden guardian, bestia, acechador, soldado.

### `events`: texto, cuando se aplica una acción

```json
{"v":1,"type":"events","events":[
 {"id":17,"kind":"attack","piece":1,"to":18,"result":{"atk_roll":5,"def_roll":2,"outcome":"hit"}},
 {"id":18,"kind":"hit","piece":5,"result":{"hp":1}},
 {"id":19,"kind":"turn","result":{"turn":1}}]}
```

| `kind` | Campos |
|---|---|
| `move` | `piece`, `from`, `to` |
| `attack` | `piece`, `to`, `result: {atk_roll, def_roll, outcome: "hit"\|"counter"\|"tie"}` |
| `hit` | `piece` (la que perdió vida), `result: {hp}` |
| `death` | `piece`, `from` |
| `turn` | `result: {turn}` |
| `win` | `result: {winner}` |

**Orden fijo de los eventos:**

- **Ataque:** `attack` → `hit` (solo si no hubo empate) → `death` (si el HP llegó a 0) → `win` o `turn`.
- **Movimiento:** `move` → `turn`.

**Confirmación:**

- El navegador del anfitrión responde `anim_done` por cada evento. El evento `turn` se confirma de inmediato.
- Si en 5 s no llega ningún `anim_done`, Python da por terminados todos los eventos pendientes.

### `hello`: al conectar, y cuando cambia el modo o el estado del remoto

```json
{"v":1,"type":"hello","you":0,"mode":"remote","role":"host",
 "remote":{"url":"https://xxx.trycloudflare.com/?p=1&k=...","tunnel":"up","connected":false}}
```

- `you` es el bando del que recibe (0 azul, 1 rojo). En modo `cpu`, el anfitrión juega `[game] cpu_human_side` de `config.toml` y la PC el otro bando. Si la PC juega los azules, abre ella en cuanto se conecta el anfitrión.
- `role` es `"host"` o `"remote"` (campo opcional, agregado sin subir `v`). El navegador lo usa para el `frame_ack` y para no mostrar el anillo de la mano en el remoto; antes eso salía de `you`.
- `remote` solo se le manda al anfitrión.
- `tunnel` puede valer `up`, `down` u `off`.

### `denied`: respuesta a una entrada rechazada

```json
{"v":1,"type":"denied","reason":"not_your_turn"}
```

`reason` puede valer `not_your_turn` o `animating`.

## Mensajes del navegador a Python (texto)

```json
{"v":1,"type":"click","x":0.031,"y":-0.054}
{"v":1,"type":"anim_done","id":17}
{"v":1,"type":"key","key":"reset"}
{"v":1,"type":"frame_ack","frame_id":42}
```

- **`click`:** `x` e `y` están en coordenadas del tablero, en metros. Python los convierte en casilla con `cell_at`.
- **`key`:** puede ser `reset`, `debug`, `lock` o `mode`. Solo se aceptan del anfitrión, salvo `debug`, que funciona en cada navegador de forma local.
- **`frame_ack`:** lo manda solo el remoto. Python le manda como máximo 2 cuadros sin confirmar.
- **Límite de tamaño:** un mensaje de más de 1 KB cierra la conexión.

## Conexión

- **URL:** el servidor está en `http://127.0.0.1:8000`. Sirve los archivos estáticos en `/` y el WebSocket en `/ws`. El navegador usa `(https ? wss : ws)://location.host/ws` + `location.search`.
- **Roles:** `?p=0&k=<host_token>` es el anfitrión y `?p=1&k=<remote_token>` es el remoto.
- **Códigos de cierre:**

| Código | Motivo |
|---|---|
| `4401` | Token inválido |
| `4409` | Ya hay un jugador 1 |

## Formato de grabación `.dj`

- Es un JSONL con una línea por cuadro que sale hacia el anfitrión: `{"dt_ms": 33, "data": "<base64 del mensaje frame completo>"}`.
- No guarda `state` ni `events`: en `--replay`, `game` corre en vivo.
- Para escribir se usa `dejarik.recording.Recorder` y para leer `read_dj`.
- `fixtures/session_01.dj` lo genera `tools/fake_session.py`: 90 cuadros sintéticos (3 s en loop) del tablero visto a 0,6 m con 40° de inclinación, con `K = [900, 900, 640, 360]`.
