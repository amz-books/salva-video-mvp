import { Container } from "@cloudflare/containers";

export class SalvaVideoContainer extends Container {
  defaultPort = 8000;
  sleepAfter = "10m";
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname.startsWith("/api/") && request.method !== "POST") {
      return new Response("Método não permitido", { status: 405 });
    }
    const container = env.SALVA_VIDEO.getByName("salva-video");
    return container.fetch(request);
  },
};
