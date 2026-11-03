# Checklist de criaturas (contrato de salida y prompt base para la IA de Blender)

**Quién hace qué:**
- P4 opera la IA a través del MCP de Blender.
- El líder (L) revisa cada criatura en el visor `web/?viewer=<kind>`.
- `tools/check_glb.py` verifica el contrato automáticamente. Su mensaje de error es lo que se le devuelve a la IA.

**Control del día 7:** tiene que haber **una** criatura (`bestia`) que cumpla el contrato y se vea bien en el visor. Si no la hay, las 4 pasan a usar la fuente 1 (modelos que ya vienen animados).

## Contrato de salida

Un archivo por tipo: `web/assets/creatures/{guardian,bestia,acechador,soldado}.glb`.

**Formato y escala**

- [ ] Formato `.glb` (glTF binario), **sin Draco**, de **menos de 5 MB**.
- [ ] +Y hacia arriba, 1 unidad = 1 m.
- [ ] Altura de **0,05 a 0,07 m**. Si viene de un FBX, revisar la escala de importación: suele ser 0,01.
- [ ] Mira hacia **+Z**. El origen está en la base, entre las patas.

**Animación**

- [ ] Tiene **un solo esqueleto**, o ninguno si se anima la pieza entera ("animación por objeto").
- [ ] Clips con estos nombres exactos: **`idle`, `walk`, `attack`, `hit`, `die`**. Si la fuente trae otros nombres, se renombran en Blender antes de exportar.
- [ ] `idle` y `walk` hacen loop sin saltos: el primer cuadro y el último coinciden.
- [ ] `walk` es "in place": la criatura no se desplaza dentro del clip. El movimiento lo hace el código.
- [ ] `attack`, `hit` y `die` duran entre 0,5 y 1,5 s.

**Archivos fuente**

- [ ] Se guardan en `assets_src/<kind>.blend` y `assets_src/<kind>.prompt.md`, con el prompt que se usó.

## Orden de preferencia de las fuentes (pasarle a la IA en este orden)

1. **Modelos que ya vienen animados.** Por ejemplo, Quaternius (CC0) o Sketchfab descargable con licencia CC, a través de la integración de Sketchfab del MCP. Hay que anotar la licencia y el autor en `<kind>.prompt.md`.
2. **Modelo estático más un esqueleto simple.** La IA arma por script un esqueleto de 4 a 8 huesos (columna, cabeza, cola o patas) y anima los 5 clips con keyframes.
3. **Animación por objeto.** Si nada de lo anterior funciona, se mueve, rota y escala la pieza entera, y se guarda como clips dentro del `.glb`.

No se usa el auto-rig de Mixamo, porque solo sirve para humanoides.

## Prompt base (se completa uno por criatura)

```text
Sos un asistente que trabaja en Blender a través del MCP. Necesito UNA criatura
para un juego de holoajedrez en realidad aumentada.

Tipo: <kind>. Rol: <rol>. Silueta: <silueta buscada>.

Probá las fuentes en este orden: (1) un modelo que ya venga animado (Sketchfab CC
o Quaternius CC0); (2) un modelo estático, más un esqueleto de 4 a 8 huesos con
keyframes; (3) animación de la pieza entera.

Contrato de salida (obligatorio):
- Exportar .glb sin Draco, menos de 5 MB, +Y hacia arriba, 1 unidad = 1 m.
- Altura entre 0,05 y 0,07 m. Mirando hacia +Z. Origen en la base.
- Clips con estos nombres exactos: idle, walk, attack, hit, die.
  idle y walk hacen loop; walk sin desplazamiento.
- Un solo esqueleto, o ninguno si es animación por objeto.
Guardá el .blend y decime la licencia y el autor del modelo de origen.
```

| Tipo | Rol | Silueta sugerida |
|---|---|---|
| `guardian` | Aguanta golpes; ataque lento | Ancho, con caparazón o armadura, de cuatro patas |
| `bestia` | Agresiva; ataque de embestida | Musculosa, con cuernos o colmillos, inclinada hacia adelante |
| `acechador` | Rápida; ataque de salto | Delgada, de patas largas, con cola |
| `soldado` | Equilibrado | Bípedo, con un arma o garras |

Si solo se consiguen 2 modelos, se repiten entre tipos. Los bandos se diferencian por el color del holograma (azul o rojo), no por el modelo.

## Revisión

1. `python tools/check_glb.py web/assets/creatures/<kind>.glb` termina sin errores.
2. Abrir `http://127.0.0.1:8000/?viewer=<kind>` y reproducir los 5 clips. Revisar que la malla no se deforme y que los loops no salten.
3. Si algo falla, se le devuelve a la IA el mensaje de `check_glb.py`, o una descripción concreta de lo que se ve mal.
