# Origen de las criaturas

Todas salen del paquete "Ultimate Monsters" de Quaternius, con licencia **CC0** (dominio público). Se descargaron como `.glb` desde poly.pizza y se adaptaron con `tools/adapt_glb.py` el 2026-11-03.

| Tipo | Archivo | Original | Monstruo | Origen | Alto | Clip de origen → nuestro clip |
|---|---|---|---|---|---|---|
| `guardian` | `web/assets/creatures/guardian.glb` | `assets_src/originals/guardian_MushroomKing.glb` | MushroomKing | [poly.pizza/m/grnFTziU8u](https://poly.pizza/m/grnFTziU8u) | 41 mm | Idle, Walk, Punch, HitReact, Death |
| `bestia` | `web/assets/creatures/bestia.glb` | `assets_src/originals/bestia_Cactoro.glb` | Cactoro | [poly.pizza/m/IGn9lhdama](https://poly.pizza/m/IGn9lhdama) | 50 mm | Idle, Walk, Punch, HitReact, Death |
| `acechador` | `web/assets/creatures/acechador.glb` | `assets_src/originals/acechador_Bunny.glb` | Bunny | [poly.pizza/m/irZjWFARyl](https://poly.pizza/m/irZjWFARyl) | 43 mm | Idle, Walk, Punch, HitReact, Death |
| `soldado` | `web/assets/creatures/soldado.glb` | `assets_src/originals/soldado_Orc.glb` | Orc | [poly.pizza/m/5vO2YJsPEf](https://poly.pizza/m/5vO2YJsPEf) | 38 mm | Idle, Walk, Punch, HitReact, Death |

Los clips de origen se llaman `CharacterArmature|<Nombre>`. Los cuatro traen los mismos 14: los 5 de la tabla pasan a `idle`, `walk`, `attack`, `hit` y `die`, y los otros 9 se conservan con el nombre en minúscula (`duck`, `jump`, `jump_idle`, `jump_land`, `no`, `run`, `wave`, `weapon`, `yes`).

## Clips sin usar a propósito

El canon de Star Wars es la única fuente de verdad (ver `docs/designs/criaturas_canon.md`). Estos clips están en los `.glb` pero el juego no los usa:

- `duck`: en el canon, el que pierde recibe el golpe, no lo esquiva.
- `no`: las piezas no reaccionan a los jugadores.
- `jump`, `jump_idle` y `jump_land`: en el canon no hay saltos. El salto al seleccionar es UI y queda para después.
- `run`: el canon no muestra piezas corriendo; el `walk` alcanza para 2 casillas.
- `weapon`: el daño es siempre 1, así que no hay un golpe "más fuerte" que mostrar.
- `wave`: el gesto de victoria es `yes`; `wave` se puede leer como "hola/chau" o, con el gesto argentino, como "no".

Para regenerar una criatura:

```powershell
python tools/adapt_glb.py assets_src/originals/<tipo>_<Monstruo>.glb web/assets/creatures/<tipo>.glb
```

Los modelos no traen texturas: los colores vienen de los materiales. En el juego eso no se nota, porque el shader de holograma los tiñe de azul o rojo según el bando.
