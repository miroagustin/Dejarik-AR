// Material de holograma: MeshBasicMaterial extendido (así hereda el skinning).
// Brillo de borde con normales por cara (look low-poly), scanlines y parpadeo.
// Mezcla normal con transparencia, NO aditiva: sobre el papel blanco del tablero
// una mezcla aditiva satura a blanco y la criatura desaparece. uScan y uFlicker
// se ajustan mirando la pantalla compartida en Teams, que aplana los detalles finos.
import * as THREE from "three";

export const holoUniforms = {
  uTime: { value: 0 },
  uScan: { value: 0.55 },    // 0 = sin scanlines, 1 = muy marcadas
  uFlicker: { value: 0.12 }, // amplitud del parpadeo
};

export const SIDE_COLORS = [new THREE.Color(0x4cc9ff), new THREE.Color(0xff5a4c)];

export function makeHologramMaterial(color) {
  const mat = new THREE.MeshBasicMaterial({
    color, transparent: true, opacity: 1, depthWrite: true,
    side: THREE.DoubleSide,
  });
  mat.userData.flash = { value: 0 }; // 0..1, destello al recibir un golpe
  mat.onBeforeCompile = shader => {
    Object.assign(shader.uniforms, holoUniforms, { uFlash: mat.userData.flash });
    shader.vertexShader = shader.vertexShader
      .replace("#include <common>", "#include <common>\nvarying vec3 vViewPos;")
      .replace("#include <project_vertex>", "#include <project_vertex>\nvViewPos = mvPosition.xyz;");
    shader.fragmentShader = shader.fragmentShader
      .replace("#include <common>", `#include <common>
        varying vec3 vViewPos;
        uniform float uTime, uScan, uFlicker, uFlash;`)
      .replace("#include <opaque_fragment>", `
        vec3 n = normalize(cross(dFdx(vViewPos), dFdy(vViewPos)));
        float facing = abs(dot(n, normalize(-vViewPos)));
        float rim = pow(1.0 - facing, 1.6);
        float scan = 1.0 - uScan * 0.5 * (0.5 + 0.5 * sin(gl_FragCoord.y * 1.6 - uTime * 6.0));
        float flicker = 1.0 - uFlicker * (0.5 + 0.5 * sin(uTime * 37.0) * sin(uTime * 13.0));
        outgoingLight = diffuseColor.rgb * (0.55 + 1.1 * rim) * scan * flicker + uFlash * vec3(1.0);
        diffuseColor.a *= 0.7 + 0.3 * rim;
        #include <opaque_fragment>`);
  };
  return mat;
}
