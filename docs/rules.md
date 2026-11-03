# Reglas de Dejarik AR

**Se congelan el día 2.** Los números de la tabla se pueden ajustar después de los ensayos, editando `KINDS` en `dejarik/game.py`.

## Versión de 20 segundos (para leer en la demo)

> Cada jugador tiene 4 criaturas. En tu turno hacés una sola cosa: mover una criatura o atacar a una rival que esté al lado. En un ataque, los dos tiran un dado y le suman su ataque o su defensa. El que saca más le saca una vida al otro. Gana el que elimina a las 4 criaturas rivales.

## Tablero

- **Casillas.** Son 25: el centro (`0`), el anillo interno (`1`–`12`) y el anillo externo (`13`–`24`).
- **Adyacencias** (las que figuran en `board_spec.json`):

| Casilla | Es adyacente a |
|---|---|
| Interna `k` | Sus 2 vecinas del anillo, la casilla externa `12+k` y el centro |
| Externa `12+k` | Sus 2 vecinas del anillo y la casilla interna `k` |
| Centro | Las 12 casillas internas |

## Piezas

Cada jugador tiene una pieza de cada tipo.

| Tipo | ATK | DEF | HP | MOV | Rol |
|---|---|---|---|---|---|
| `guardian` | 1 | 3 | 3 | 1 | Aguanta golpes |
| `bestia` | 3 | 1 | 2 | 1 | Pega fuerte |
| `acechador` | 2 | 1 | 2 | 2 | Se mueve rápido |
| `soldado` | 2 | 2 | 2 | 1 | Equilibrado |

**Posiciones iniciales,** en el orden guardian, bestia, acechador, soldado:

| Jugador | Color | Casillas | Ids de pieza |
|---|---|---|---|
| 0 | Azul | `23, 24, 13, 14` | 0–3 |
| 1 | Rojo | `17, 18, 19, 20` | 4–7 |

**Empieza el jugador 0.**

## Turno

En cada turno se hace **una** de estas dos acciones:

- **Mover:** ir a una casilla vacía a una distancia de hasta MOV pasos, sin atravesar casillas ocupadas.
- **Atacar:** a una pieza rival adyacente. El atacante no se mueve.

## Cómo se elige con clic, toque o pinch

**Sin ninguna pieza elegida** (fase `select`):

| Si tocás… | Pasa esto |
|---|---|
| Una pieza propia | Queda seleccionada. Se iluminan las casillas vacías a las que puede llegar y las adyacentes con un rival. |
| Cualquier otra cosa | Nada. |

**Con una pieza elegida** (fase `target`):

| Si tocás… | Pasa esto |
|---|---|
| Otra pieza propia | Cambia la selección. |
| Una casilla vacía iluminada | La pieza se mueve ahí. |
| Una casilla iluminada con un rival | La pieza ataca. |
| Cualquier otra casilla, o fuera del tablero | Se deselecciona. |

## Combate

1. El atacante tira **1d6 + ATK** y el defensor tira **1d6 + DEF**.
2. Se comparan los resultados:

| Resultado | Qué pasa | Nombre |
|---|---|---|
| Gana el atacante | El defensor pierde 1 HP | `hit` |
| Gana el defensor | El atacante pierde 1 HP | `counter` (contragolpe) |
| Empate | No pasa nada | `tie` |

3. Una pieza que llega a HP 0 muere y sale del tablero.

Los dados usan `random.Random(seed)`, y su estado se guarda con la partida. Con la misma semilla y las mismas acciones, la partida sale igual.

## Fin de la partida

- Gana quien elimina las 4 piezas rivales.
- Con 4 piezas en el tablero siempre hay alguna acción legal, así que no hace falta una regla para pasar el turno.
- Una partida completa dura entre 6 y 8 minutos (objetivo G2). En la demo se muestra un tramo de unos 3 minutos.
