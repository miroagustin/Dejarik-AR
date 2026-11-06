// Sonido sintetizado con Web Audio: sin archivos, sin licencias, funciona offline.
// Cada sonido es una función chica; para cambiar uno, se tocan sus números.
//
// El navegador no deja sonar nada hasta que el usuario hace clic o aprieta una
// tecla, salvo que Chrome/Edge se lance con --autoplay-policy=no-user-gesture-required
// (lo hace __main__.py). unlock() se llama en el primer clic o tecla.

export const VOLUME = 0.5; // volumen general (0..1)

export function createAudio(ctx = new AudioContext()) {
  const master = ctx.createGain();
  master.gain.value = VOLUME;
  const limiter = ctx.createDynamicsCompressor();
  master.connect(limiter).connect(ctx.destination);
  let muted = false, hum = null;

  const now = () => ctx.currentTime;

  // Un oscilador con envolvente de volumen y, opcionalmente, deslizamiento de frecuencia.
  function tone({ freq, to = freq, dur, type = "sine", gain = 0.3, at = 0, attack = 0.005 }) {
    const t = now() + at;
    const osc = ctx.createOscillator(), env = ctx.createGain();
    osc.type = type;
    osc.frequency.setValueAtTime(freq, t);
    if (to !== freq) osc.frequency.exponentialRampToValueAtTime(to, t + dur);
    env.gain.setValueAtTime(0, t);
    env.gain.linearRampToValueAtTime(gain, t + attack);
    env.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    osc.connect(env).connect(master);
    osc.start(t);
    osc.stop(t + dur + 0.02);
  }

  // Ruido blanco filtrado (impactos, chasquidos, el dado).
  function noise({ dur, freq = 1200, q = 1, type = "bandpass", gain = 0.3, at = 0, to = freq }) {
    const t = now() + at;
    const buf = ctx.createBuffer(1, Math.ceil(ctx.sampleRate * dur), ctx.sampleRate);
    const data = buf.getChannelData(0);
    for (let i = 0; i < data.length; i++) data[i] = Math.random() * 2 - 1;
    const src = ctx.createBufferSource(), filter = ctx.createBiquadFilter(), env = ctx.createGain();
    src.buffer = buf;
    filter.type = type;
    filter.Q.value = q;
    filter.frequency.setValueAtTime(freq, t);
    if (to !== freq) filter.frequency.exponentialRampToValueAtTime(to, t + dur);
    env.gain.setValueAtTime(gain, t);
    env.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    src.connect(filter).connect(env).connect(master);
    src.start(t);
  }

  const sounds = {
    // Encendido del tablero: barrido ascendente con brillo.
    boot() {
      tone({ freq: 80, to: 640, dur: 1.2, type: "sawtooth", gain: 0.12, attack: 0.3 });
      tone({ freq: 160, to: 1280, dur: 1.2, type: "sine", gain: 0.1, attack: 0.3 });
      noise({ dur: 1.0, freq: 400, to: 4000, q: 4, gain: 0.08, at: 0.1 });
      tone({ freq: 1320, dur: 0.6, type: "triangle", gain: 0.12, at: 1.1 });
    },
    // Selección de pieza: doble bip.
    select() {
      tone({ freq: 880, dur: 0.07, type: "square", gain: 0.15 });
      tone({ freq: 1320, dur: 0.09, type: "square", gain: 0.15, at: 0.07 });
    },
    // Paso de una criatura (se llama varias veces durante walk).
    step() { noise({ dur: 0.06, freq: 350, q: 0.7, gain: 2.5 }); },
    // El dado: varios chasquidos que se van espaciando.
    dice() {
      [0, 0.06, 0.13, 0.22, 0.34, 0.5].forEach((at, i) => noise({ dur: 0.035, freq: 2500 - i * 200, q: 6, gain: 0.8, at }));
    },
    // Ataque: zumbido que sube, tipo descarga.
    attack() {
      tone({ freq: 220, to: 880, dur: 0.25, type: "sawtooth", gain: 0.3 });
      noise({ dur: 0.25, freq: 800, to: 3000, q: 2, gain: 0.3 });
    },
    // Golpe recibido: impacto grave más crujido.
    hit() {
      tone({ freq: 140, to: 50, dur: 0.3, type: "sine", gain: 0.45 });
      noise({ dur: 0.18, freq: 1800, q: 1, gain: 0.3 });
    },
    // Muerte: tono que cae y se apaga con ruido.
    death() {
      tone({ freq: 660, to: 70, dur: 1.0, type: "sawtooth", gain: 0.12 });
      tone({ freq: 440, to: 55, dur: 1.0, type: "square", gain: 0.05, at: 0.05 });
      noise({ dur: 1.0, freq: 3000, to: 200, q: 1, gain: 0.1, at: 0.1 });
    },
    // Cambio de turno: campanita corta.
    turn() {
      tone({ freq: 1046, dur: 0.25, type: "triangle", gain: 0.16 });
      tone({ freq: 1568, dur: 0.35, type: "triangle", gain: 0.12, at: 0.08 });
    },
    // Victoria: arpegio mayor.
    win() {
      [523, 659, 784, 1046, 1318].forEach((f, i) => tone({ freq: f, dur: 0.5, type: "triangle", gain: 0.12, at: i * 0.12 }));
      tone({ freq: 1046, dur: 1.5, type: "sine", gain: 0.1, at: 0.6, attack: 0.1 });
    },
    // Entrada rechazada: zumbido grave corto.
    denied() { tone({ freq: 140, dur: 0.18, type: "square", gain: 0.3 }); },
    // Gesto de la mano: tic al empezar a sostener, descendente corto si se cancela.
    holdStart() { tone({ freq: 1200, dur: 0.04, type: "sine", gain: 0.15 }); },
    holdCancel() { tone({ freq: 500, to: 300, dur: 0.15, type: "triangle", gain: 0.2 }); },
  };

  // Zumbido de fondo del holograma: dos senos graves desafinados, muy bajo.
  function startHum() {
    if (hum) return;
    const g = ctx.createGain();
    g.gain.setValueAtTime(0, now());
    g.gain.linearRampToValueAtTime(0.035, now() + 2);
    const oscs = [55, 55.7, 110.3].map(f => {
      const o = ctx.createOscillator();
      o.frequency.value = f;
      o.connect(g);
      o.start();
      return o;
    });
    g.connect(master);
    hum = { g, oscs };
  }

  return {
    ctx,
    play(name) { if (!muted) sounds[name]?.(); },
    names: Object.keys(sounds),
    startHum,
    unlock() { if (ctx.state === "suspended") ctx.resume(); },
    toggleMute() {
      muted = !muted;
      master.gain.setTargetAtTime(muted ? 0 : VOLUME, now(), 0.05);
      return muted;
    },
  };
}
