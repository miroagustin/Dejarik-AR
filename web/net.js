// WebSocket con Python (docs/protocol.md). Reintenta cada 1 s, salvo 4401/4409.

const CLOSE_MESSAGES = { 4401: "Link inválido", 4409: "Ya hay un jugador 1" };

export function connect(handlers) {
  const url = `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws${location.search}`;
  let ws = null;

  function open() {
    ws = new WebSocket(url);
    ws.binaryType = "arraybuffer";
    ws.onopen = () => handlers.onStatus?.("conectado");
    ws.onmessage = ev => {
      if (typeof ev.data === "string") {
        const msg = JSON.parse(ev.data);
        handlers[msg.type]?.(msg);
      } else {
        const view = new DataView(ev.data);
        const n = view.getUint32(0, false);
        const header = JSON.parse(new TextDecoder().decode(new Uint8Array(ev.data, 4, n)));
        handlers.frame?.(header, new Blob([new Uint8Array(ev.data, 4 + n)], { type: "image/jpeg" }));
      }
    };
    ws.onclose = ev => {
      if (CLOSE_MESSAGES[ev.code]) {
        handlers.onStatus?.(CLOSE_MESSAGES[ev.code]);
        return;
      }
      handlers.onStatus?.("reconectando…");
      setTimeout(open, 1000);
    };
  }

  open();
  return {
    send(obj) {
      if (ws?.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ v: 1, ...obj }));
    },
  };
}
