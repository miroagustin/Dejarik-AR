# Guion de la demo (26/11, por Teams)

> Borrador del día 2. Los tiempos de los respaldos se miden en los ensayos de los días 19, 21 y 23 y se completan acá.

## Roles

| Quién | Qué hace |
|---|---|
| **Anfitrión** | Tiene el tablero y la webcam. Corre el juego y comparte la ventana de Chrome en Teams, con "compartir audio del sistema". Juega el bando azul. |
| **Remoto** | Un integrante desde su casa. Abre el link que el anfitrión pega en el chat de Teams. Juega el bando rojo. |
| **Narrador** | Explica lo que se ve y lee las reglas de 20 segundos de `docs/rules.md`. |
| **Respaldo** | Está atento al checklist de abajo y avisa qué tecla o flag usar si algo falla. |

## Guion (3 minutos)

| Tiempo | Qué se ve |
|---|---|
| Antes | El anfitrión corre `python -m dejarik --mode remote` y pega el link en el chat. El remoto ya está conectado. Con `P` se pasa a `cpu`. |
| 0:00–0:20 | Arranca la pantalla compartida. Se detecta el tablero, suena el "encendido" y aparecen las 8 criaturas. El narrador lee las reglas. |
| 0:20–1:10 | Partida **contra la PC**: el anfitrión mueve con la mano; el narrador dice: «Apoyá el índice en una casilla y sostené». La PC responde ("La PC está pensando…") y hay al menos 1 combate con dados. |
| 1:10–1:20 | Se aprieta `P` dos veces para pasar a **remoto**. El HUD muestra "Jugador 1 conectado". |
| 1:20–2:20 | Partida **remota**: el integrante desde su casa mueve las rojas y hay al menos 1 combate más. |
| 2:20–2:40 | El anfitrión mete la mano y tapa marcadores: las criaturas siguen ancladas. |
| 2:40–3:00 | El anfitrión aprieta `D` para mostrar el **overlay de debug** (marcadores, ejes, grilla reproyectada, fps, error de reproyección). El narrador nombra las técnicas de clase. |

## Checklist del anfitrión (el día anterior y 30 minutos antes)

- [ ] La PC conectada **por cable de red**, no por Wi-Fi.
- [ ] Webcam en el trípode, más una webcam de repuesto.
- [ ] Lámpara para iluminar el tablero de forma pareja, sin reflejos.
- [ ] Tablero pegado sobre foamboard, más un tablero de repuesto.
- [ ] `calib.npz` hecho con esta webcam y esta resolución.
- [ ] `tools/bin/cloudflared.exe` presente, y que no exista `%USERPROFILE%\.cloudflared\config.yml`.
- [ ] Teams con "compartir audio del sistema" activado. Probar que la ventana siga andando cuando Teams la tapa.
- [ ] El MP4 de respaldo en el escritorio.
- [ ] Ensayo completo hecho ese mismo día.

## Respaldos

| Falla | Qué hacer | Tecla o flag | Tiempo medido |
|---|---|---|---|
| La mano no responde | Seguir con el mouse | `--input mouse`, o simplemente usar el mouse | — |
| La mano confirma sin querer | Subir el tiempo de sostén y reiniciar | `hold_ms` en `[hands]` de `config.toml` | — |
| El remoto se cae o el túnel no levanta | Pasar a local o contra la PC | `P` | — |
| El tracking tiembla por la luz | Bloquear la pose | `L` | — |
| Python se cuelga | Relanzarlo con el estado guardado (Chrome se reconecta solo) | `python -m dejarik --resume` | — |
| La cámara no funciona | Reproducir la sesión grabada y jugar con el mouse | `--replay recordings/<sesion>.dj` | — |
| No anda nada | Compartir el MP4 | — | — |
