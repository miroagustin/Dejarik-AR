# Guion de la demo (26/11, por Teams)

> La demo es solo **contra la PC** (modo `cpu`), sin túnel ni jugador remoto: no depende de la red. Los tiempos de los respaldos se miden en el ensayo y se completan acá.

## Roles

| Quién | Qué hace |
|---|---|
| **Anfitrión** | Tiene el tablero y la webcam. Corre el juego y comparte la ventana de Chrome en Teams, con "compartir audio del sistema". Juega el bando azul contra la PC, que juega el rojo. |
| **Narrador** | Explica lo que se ve, lee las reglas de 20 segundos de `docs/rules.md` y lee en voz alta el panel de combate. |
| **Respaldo** | Está atento al checklist de abajo y avisa qué tecla o flag usar si algo falla. |

## Guion (3 minutos)

| Tiempo | Qué se ve |
|---|---|
| Antes | El anfitrión corre `python -m dejarik` (el modo por defecto es `cpu`). |
| 0:00–0:20 | Arranca la pantalla compartida. Se detecta el tablero, suena el "encendido" y aparecen las 8 criaturas. El narrador lee las reglas. |
| 0:20–1:20 | Partida **contra la PC**. El anfitrión mueve con la mano y el narrador dice: «Apoyá el índice en una casilla y sostené». La PC responde ("La PC está pensando…"). El objetivo es acercar las criaturas hasta que haya un combate. |
| 1:20–2:20 | **Combates.** Tiene que haber al menos 2. A la derecha aparece el panel con los dos dados girando. Cuando caen, el narrador lee la cuenta («la Bestia saca 5 más 3 de ataque, 8; el Guardián saca 2 más 3 de defensa, 5») y el resultado: golpe, contragolpe o empate, y quién pierde la vida. |
| 2:20–2:40 | El anfitrión mete la mano y tapa marcadores: las criaturas siguen ancladas. |
| 2:40–3:00 | El anfitrión aprieta `D` para mostrar el **overlay de debug** (marcadores, ejes, grilla reproyectada, fps, error de reproyección). El narrador nombra las técnicas de clase. |

## Checklist del anfitrión (el día anterior y 30 minutos antes)

- [ ] La PC conectada **por cable de red**, no por Wi-Fi.
- [ ] Webcam en el trípode, más una webcam de repuesto.
- [ ] Lámpara para iluminar el tablero de forma pareja, sin reflejos.
- [ ] Tablero pegado sobre foamboard, más un tablero de repuesto.
- [ ] `calib.npz` hecho con esta webcam y esta resolución.
- [ ] Teams con "compartir audio del sistema" activado. Probar que la ventana siga andando cuando Teams la tapa.
- [ ] El MP4 de respaldo en el escritorio.
- [ ] Ensayo completo hecho ese mismo día.

## Respaldos

| Falla | Qué hacer | Tecla o flag | Tiempo medido |
|---|---|---|---|
| La mano no responde | Seguir con el mouse | `--input mouse`, o simplemente usar el mouse | — |
| La mano confirma sin querer | Subir el tiempo de sostén y reiniciar | `hold_ms` en `[hands]` de `config.toml` | — |
| El tracking tiembla por la luz | Bloquear la pose | `L` | — |
| Python se cuelga | Relanzarlo con el estado guardado (Chrome se reconecta solo) | `python -m dejarik --resume` | — |
| La cámara no funciona | Reproducir la sesión grabada y jugar con el mouse | `--replay recordings/<sesion>.dj` | — |
| No anda nada | Compartir el MP4 | — | — |
