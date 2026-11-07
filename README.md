# Dejarik AR

TP integrador de Visión Artificial: holoajedrez en realidad aumentada sobre un tablero impreso con marcadores ArUco.

- **Python** hace la visión (calibración, ArUco, PnP, filtro) y aplica las reglas.
- **Three.js** dibuja criaturas animadas sobre el video.

Diseño completo: [docs/designs/dejarik_ar.md](docs/designs/dejarik_ar.md).

## Documentación

- [Briefs](docs/briefs/): consigna original, concepto general, mano, personajes y vista frontal.
- [Diseños](docs/designs/): especificaciones del sistema y sus funciones.
- [Borradores](docs/designs/drafts/): versiones de trabajo conservadas por separado.
- [Revisiones](docs/designs/reviews/): revisión general y carpetas por función (`hand_interaction/` y `criaturas_canon/`).

La calibración `calib.npz` y las grabaciones `.dj` son locales y no se versionan; las sesiones de prueba de `fixtures/` sí.

## Estado

Está implementado todo el diseño: visión (`vision`, `one_euro`), mano (`hands`), reglas (`game`), rival automático (`ai`), servidor y modos (`transport`), túnel (`tunnel`), grabación y replay (`recording`) y el navegador (`web/`). Falta lo que se hace en la casa del anfitrión: `calib.npz`, el ajuste de la mano y los ensayos por Teams.

## Instalación (Windows)

Hace falta **Python 3.11** con las versiones de `requirements.txt`. También anda en Python 3.14 con opencv-contrib 5.0, mediapipe 1.0.1, numpy 2.5 y websockets 15.

```powershell
py install 3.11                       # si no está instalado
py -3.11 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -c "import cv2.aruco, mediapipe.tasks; print('ok')"
```

## Imprimir el tablero

1. Generar los PDF:

   ```powershell
   python tools/make_board.py            # print/board.pdf, A2 a escala 1:1 (copistería)
   python tools/make_board.py --page A3  # print/board_a3.pdf, achicado, para probar en casa
   python tools/make_board.py --page A4  # print/board_a4.pdf, achicado, para probar en casa
   python tools/make_board.py --checker  # print/checker.pdf, el damero para calibrar
   ```

2. Imprimir **al 100% / "tamaño real"**, nunca con "ajustar a página". Usar papel mate y pegar la hoja sobre foamboard.
3. Medir con una regla la regla impresa. En A2 debería dar 100 mm; en A3 o A4, lo que indique `make_board.py`.
4. Anotar la medida real en `print_scale_measured` dentro de `board_spec.json`. Todas las longitudes se corrigen con ese valor.

## Calibrar la webcam

```powershell
python tools/calibrate.py            # con el damero (print/checker.pdf, hoja A4 aparte)
python tools/calibrate.py --tablero  # sin imprimir nada más: con los marcadores del tablero del juego
```

1. Mostrar el damero (o el tablero, con al menos 8 marcadores a la vista) en distintas posiciones e inclinaciones.
2. Apretar `ESPACIO` para guardar cada vista. Hacen falta al menos 15.
3. Apretar `C` para calibrar.
4. Si el error (RMS) es menor a 0,5 px, se guarda `calib.npz`.

Hay que usar la misma webcam, la misma resolución y el mismo foco que en la demo. Los valores de foco y exposición se configuran en la sección `[camera]` de `config.toml`.

## Sesión falsa (para trabajar sin cámara)

```powershell
python tools/fake_session.py   # genera fixtures/session_01.dj
```

Son 90 cuadros sintéticos del tablero, con la pose real en el header. El formato está en [docs/protocol.md](docs/protocol.md).

## Jugar

```powershell
python -m dejarik                         # contra la PC, con la webcam, mouse y mano
python -m dejarik --mode local            # dos jugadores en la misma máquina (pass-and-play)
python -m dejarik --mode remote           # abre el túnel e imprime el link para el remoto
python -m dejarik --replay fixtures/session_01.dj   # sin cámara: video grabado en loop, juego en vivo
```

- Abre Chrome en una ventana `--app` (la que se comparte en Teams). Con `--no-browser` no la abre; la URL del anfitrión es `http://127.0.0.1:8000/?p=0&k=` + el contenido de `save/host_token`.
- **Turno:** clic, o apoyá el índice en una casilla y sostené (`hold_ms`, 1,5 s por defecto, con un anillo de carga) sobre una pieza propia la selecciona y se iluminan sus destinos; sobre una casilla vacía iluminada se mueve, sobre un rival iluminado ataca.
- **Flags:** `--input mouse|hand|both`, `--record X.dj` (graba lo que ve el anfitrión), `--resume` (sigue la última partida, `save/state.json`).
- **Teclas:** `D` overlay de debug, `L` bloquear la pose, `R` reiniciar, `P` cambiar de modo (`cpu → local → remote`), `M` silenciar, `F` espejar la vista (solo en ese navegador; queda guardado).
- Sin `calib.npz` usa una K aproximada (avisa en la consola). Para la demo, calibrar.
- **Visor de criaturas:** `http://127.0.0.1:8000/?viewer=bestia` (o `guardian`, `acechador`, `soldado`). Agregar `&side=1` la muestra en rojo y `&still=1` la deja quieta.
- **Sonido:** se genera en el navegador (`web/audio.js`, sin archivos). `http://127.0.0.1:8000/?soundcheck` muestra el volumen pico de cada sonido; si alguno dice MUDO, está roto. En Teams hay que activar "compartir audio del sistema".
- **Ajustes visuales:** el oscurecimiento del video está en `BACKGROUND_DIM` (`web/scene.js`). Las scanlines y el parpadeo están en `holoUniforms` (`web/hologram.js`). Se ajustan mirando la pantalla compartida en Teams.
- **Ajustes de juego:** bando del anfitrión contra la PC en `[game] cpu_human_side` (por defecto 1, rojos: abre la PC); `KINDS` en `dejarik/game.py`; pesos del rival al principio de `dejarik/ai.py`; mano en `[hands]` de `config.toml`, con el gesto en `[hands] gesture` (`touch` o `dwell`).

## Modo remoto

- Descargar `cloudflared.exe` (de github.com/cloudflare/cloudflared, sección Releases) en `tools/bin/`.
- No debe existir `%USERPROFILE%\.cloudflared\config.yml`.
- El link para el jugador remoto aparece en la consola y en el HUD del anfitrión. Si el túnel falla, se sigue en `local` o `cpu` con `P`.

## Tests

```powershell
pytest -q
```

## Glosario

| Término | Qué es |
|---|---|
| **Pose** | Posición y rotación del tablero respecto de la cámara. |
| **PnP** | Calcula la pose a partir de puntos 3D conocidos (las esquinas de los marcadores) y sus píxeles en la imagen. |
| **One-Euro** | Filtro que suaviza el temblor sin agregar mucho retraso cuando algo se mueve rápido. |
| **glTF / .glb** | Formato de modelos 3D con animaciones. |
| **Rig** | El esqueleto que mueve la malla de una criatura. |
| **Pass-and-play** | Dos jugadores por turnos en la misma máquina (modo `local`). |
