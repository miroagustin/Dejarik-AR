# Dejarik AR

TP integrador de Visión Artificial: holoajedrez en realidad aumentada sobre un tablero impreso con marcadores ArUco.

- **Python** hace la visión (calibración, ArUco, PnP, filtro) y aplica las reglas.
- **Three.js** dibuja criaturas animadas sobre el video.

Diseño completo: [docs/designs/dejarik_ar.md](docs/designs/dejarik_ar.md).

## Estado

Están listos los entregables de los días 1–2:

- `board_spec.json`
- los documentos congelados (`docs/`)
- `dejarik/board.py`
- `protocol.encode_frame` y `protocol.decode_frame`
- el formato `.dj`
- las herramientas para imprimir, calibrar y generar la sesión falsa

El resto (`vision`, `game`, `transport`, `web/`…) sigue el calendario del diseño.

## Instalación (Windows)

Hace falta **Python 3.11**. mediapipe no tiene versiones para 3.13 o posteriores.

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
python tools/calibrate.py
```

1. Mostrar el damero impreso en distintas posiciones e inclinaciones.
2. Apretar `ESPACIO` para guardar cada vista. Hacen falta al menos 15.
3. Apretar `C` para calibrar.
4. Si el error (RMS) es menor a 0,5 px, se guarda `calib.npz`.

Hay que usar la misma webcam, la misma resolución y el mismo foco que en la demo. Los valores de foco y exposición se configuran en la sección `[camera]` de `config.toml`.

## Sesión falsa (para trabajar sin cámara)

```powershell
python tools/fake_session.py   # genera fixtures/session_01.dj
```

Son 90 cuadros sintéticos del tablero, con la pose real en el header. El formato está en [docs/protocol.md](docs/protocol.md).

## Probar el render sin cámara ni juego

Mientras no existan `transport.py` y `game.py`, hay un servidor de desarrollo:

```powershell
python tools/dev_server.py                # reproduce fixtures/session_01.dj
python tools/dev_server.py --autoplay     # además juega solo una partida guionada
```

- Abrir `http://127.0.0.1:8000/?p=0`. Cada clic avanza la partida guionada (mover, atacar, golpe, contragolpe, muerte). `R` la reinicia y `D` muestra el overlay de debug.
- **Visor de criaturas:** `http://127.0.0.1:8000/?viewer=bestia` (o `guardian`, `acechador`, `soldado`). Agregar `&side=1` la muestra en rojo y `&still=1` la deja quieta.
- **Sonido:** se genera en el navegador (`web/audio.js`, sin archivos). Suena desde el primer clic o tecla. `M` silencia. `http://127.0.0.1:8000/?soundcheck` muestra el volumen pico de cada sonido; si alguno dice MUDO, está roto. En Teams hay que activar "compartir audio del sistema".
- **Ajustes visuales:** el oscurecimiento del video está en `BACKGROUND_DIM` (`web/scene.js`). Las scanlines y el parpadeo están en `holoUniforms` (`web/hologram.js`). Se ajustan mirando la pantalla compartida en Teams.

## Tests

```powershell
pytest -q
```

## Más adelante (según el diseño)

- **Correr el juego:**
  - `python -m dejarik --mode cpu|local|remote`
  - Flags: `--input mouse|hand|both`, `--replay`, `--record`, `--resume` y `--no-browser`.
  - Teclas: `D` overlay de debug, `L` bloquear la pose, `R` reiniciar, `P` cambiar de modo, `M` silenciar.
- **Modo remoto:**
  - Descargar `cloudflared.exe` (de github.com/cloudflare/cloudflared, sección Releases) en `tools/bin/`.
  - No debe existir `%USERPROFILE%\.cloudflared\config.yml`.
  - El link para el jugador remoto aparece en la consola y en el HUD del anfitrión.

## Glosario

| Término | Qué es |
|---|---|
| **Pose** | Posición y rotación del tablero respecto de la cámara. |
| **PnP** | Calcula la pose a partir de puntos 3D conocidos (las esquinas de los marcadores) y sus píxeles en la imagen. |
| **One-Euro** | Filtro que suaviza el temblor sin agregar mucho retraso cuando algo se mueve rápido. |
| **glTF / .glb** | Formato de modelos 3D con animaciones. |
| **Rig** | El esqueleto que mueve la malla de una criatura. |
| **Pass-and-play** | Dos jugadores por turnos en la misma máquina (modo `local`). |
