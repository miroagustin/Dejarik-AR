# Checklist de criaturas (contrato de salida, fuentes y prompt para la IA de Blender)

**Camino por defecto:** monstruos animados de Quaternius (CC0) adaptados con `tools/adapt_glb.py`, sin Blender. La IA de Blender (MCP, la opera P4) solo hace falta para lo que el script no cubre: agregar un clip que falta o compactar la pose de `idle`.

**Quién hace qué:**
- P4 elige y adapta los modelos.
- El líder (L) revisa cada criatura en el visor `web/?viewer=<kind>`.
- `tools/check_glb.py` verifica el contrato automáticamente. Su mensaje de error es lo que se le devuelve a la IA, si se usó.

## Contrato de salida

Un archivo por tipo: `web/assets/creatures/{guardian,bestia,acechador,soldado}.glb`. Todas las medidas se toman en el primer cuadro de `idle`, que es la pose que se ve sobre el tablero.

**Formato y escala**

- [ ] Formato `.glb` (glTF binario), **sin Draco**, de **menos de 5 MB**.
- [ ] +Y hacia arriba, 1 unidad = 1 m.
- [ ] **Vista desde arriba, entra en un círculo de 44 mm de diámetro centrado en el origen.** Es lo que entra en una casilla del anillo interno del tablero A2 (40 mm de ancho en el medio, 52 mm de fondo). Un círculo, y no un cuadrado, porque la criatura gira para mirar a su objetivo.
- [ ] Altura de **30 a 70 mm**. La altura resulta de escalar hasta que entre la base. Los monstruos de Quaternius son casi tan anchos como altos, así que quedan entre 35 y 50 mm.
- [ ] El punto más bajo está a ±5 mm de y = 0. Mira hacia **+Z**.

**Animación**

- [ ] Tiene **un solo esqueleto**, o ninguno si se anima la pieza entera. Varias mallas (cuerpo y ojos) pueden compartir el mismo esqueleto.
- [ ] Como mínimo, clips con estos nombres exactos: **`idle`, `walk`, `attack`, `hit`, `die`**. Otros clips son opcionales.
- [ ] `idle` y `walk` hacen loop sin saltos, y `walk` es "in place": el movimiento lo hace el código.

## Fuente 1: Quaternius "Ultimate Monsters" (CC0)

- **De dónde bajarlos:** cada monstruo está en [poly.pizza](https://poly.pizza) como `.glb` (buscar por nombre y elegir el de autor Quaternius y etiqueta "Animated"). El paquete completo está en [quaternius.com](https://quaternius.com/packs/ultimatemonsters.html), pero su carpeta de Google Drive suele dar "Quota exceeded".
- **Cómo adaptarlos:**

  ```powershell
  python tools/adapt_glb.py descargas/Cactoro.glb web/assets/creatures/guardian.glb
  ```

  El script renombra los clips (`Idle`→`idle`, `Walk`→`walk`, `Punch`/`Bite_Front`/`Headbutt`→`attack`, `HitReact`/`HitRecieve`→`hit`, `Death`→`die`), conserva los demás en minúscula, escala hasta que entre en el círculo de 44 mm (máximo 70 mm de alto), apoya el modelo en y = 0 y corre `check_glb`.

**Resultados medidos el día 2.** Pasaron 19 de 34 monstruos. Los que cumplen el contrato, ordenados por altura:

| Monstruo | Alto | Tipo | Clip de ataque |
|---|---|---|---|
| Mushnub_Evolved | 51 mm | Camina | `Bite_Front` |
| Cactoro | 50 mm | Camina | `Punch` |
| Mushnub | 49 mm | Camina | `Bite_Front` |
| Tribal | 49 mm | Vuela (lo apoya en el piso) | `Headbutt` |
| Bunny | 43 mm | Camina | `Punch` |
| MushroomKing | 41 mm | Camina | `Punch` |
| Chicken | 39 mm | Camina | `Bite_Front` |
| Orc | 38 mm | Camina | `Punch` |
| Ghost, Monkroose | 37 mm | Ghost vuela, Monkroose camina | `Headbutt` / `Punch` |
| Ghost_Skull, BlueDemon, Yeti, GreenSpikyBlob | 35–36 mm | Camina (Ghost_Skull vuela) | — |
| GreenBlob, Hywirl, Ninja, Pigeon, Glub_Evolved | 31–33 mm | Camina o vuela | — |

**Los que no pasaron:**
- **Alien:** le falta el clip `hit`.
- **Dragon, Fish, Frog:** usan otros nombres de clip, o les faltan clips.
- **El resto:** quedan por debajo de 30 mm porque son muy anchos.

En todos estos casos, la IA de Blender puede agregar el clip o compactar la pose.

**Licencia:** CC0. No hace falta atribución, pero conviene anotar en `assets_src/<kind>.source.md` de qué monstruo salió cada tipo.

## Fuente 2: IA de Blender a través del MCP (solo si la fuente 1 no alcanza)

En este orden:

1. Agregar un clip que falta a un modelo de Quaternius. Por ejemplo, un `hit` como un sacudón corto.
2. Modelo estático más un esqueleto de 4 a 8 huesos, animado con keyframes.
3. Animación por objeto: mover, rotar y escalar la pieza entera.

No se usa el auto-rig de Mixamo, porque solo sirve para humanoides.

```text
Sos un asistente que trabaja en Blender a través del MCP. Necesito adaptar UNA
criatura para un juego de holoajedrez en realidad aumentada.

Tipo: <kind>. Rol: <rol>. Modelo de partida: <archivo o descripción>.
Qué hace falta: <p. ej. agregar un clip "hit" de 0,5 s / compactar la pose de idle>.

Contrato de salida (obligatorio):
- Exportar .glb sin Draco, menos de 5 MB, +Y hacia arriba, 1 unidad = 1 m.
- En el primer cuadro de idle, vista desde arriba, entra en un círculo de 44 mm
  centrado en el origen; alto entre 30 y 70 mm; punto más bajo en y = 0; mira a +Z.
- Como mínimo, clips con estos nombres exactos: idle, walk, attack, hit, die.
  Otros clips son opcionales.
  idle y walk hacen loop; walk sin desplazamiento.
- Un solo esqueleto, o ninguno si es animación por objeto.
- Antes de entregar, verificá con: python tools/check_glb.py <archivo>.glb
Guardá el .blend en assets_src/.
```

| Tipo | Rol |
|---|---|
| `guardian` | Aguanta golpes; ataque lento |
| `bestia` | Agresiva; ataque de embestida |
| `acechador` | Rápida; ataque de salto |
| `soldado` | Equilibrado |

Si solo se consiguen 2 modelos, se repiten entre tipos. Los bandos se diferencian por el color del holograma (azul o rojo), no por el modelo.

## Revisión

1. `python tools/check_glb.py web/assets/creatures/<kind>.glb` termina sin errores.
2. Abrir `http://127.0.0.1:8000/?viewer=<kind>` y reproducir todos los clips. Revisar que la malla no se deforme y que los loops no salten.
