# Origen de las criaturas

Todas salen del paquete "Ultimate Monsters" de Quaternius, con licencia **CC0** (dominio público). Se descargaron como `.glb` desde poly.pizza y se adaptaron con `tools/adapt_glb.py` el 2026-11-03.

| Tipo | Archivo | Monstruo | Origen | Alto | Clip de origen → nuestro clip |
|---|---|---|---|---|---|
| `guardian` | `web/assets/creatures/guardian.glb` | MushroomKing | [poly.pizza/m/grnFTziU8u](https://poly.pizza/m/grnFTziU8u) | 41 mm | Idle, Walk, Punch, HitReact, Death |
| `bestia` | `web/assets/creatures/bestia.glb` | Cactoro | [poly.pizza/m/IGn9lhdama](https://poly.pizza/m/IGn9lhdama) | 50 mm | Idle, Walk, Punch, HitReact, Death |
| `acechador` | `web/assets/creatures/acechador.glb` | Bunny | [poly.pizza/m/irZjWFARyl](https://poly.pizza/m/irZjWFARyl) | 43 mm | Idle, Walk, Punch, HitReact, Death |
| `soldado` | `web/assets/creatures/soldado.glb` | Orc | [poly.pizza/m/5vO2YJsPEf](https://poly.pizza/m/5vO2YJsPEf) | 38 mm | Idle, Walk, Punch, HitReact, Death |

Los clips de origen se llaman `CharacterArmature|<Nombre>`.

Para regenerar una criatura:

```powershell
python tools/adapt_glb.py <descarga>.glb web/assets/creatures/<tipo>.glb
```

Los modelos no traen texturas: los colores vienen de los materiales. En el juego eso no se nota, porque el shader de holograma los tiñe de azul o rojo según el bando.
