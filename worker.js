// Cloudflare Workers with Static Assets (worker.js)
// Automatically routes 13 custom domains from a single deployment based on the Host header.

const KNOWN_DOMAINS = new Set(["kakdiko.web.id", "ekuitas.biz.id", "ekuitas.web.id", "ekuitas.my.id", "dividen.biz.id", "obligasi.biz.id", "ventura.web.id", "tender.biz.id", "kodelab.my.id", "kodelab.web.id", "kanvasdigital.web.id", "pustakaai.web.id", "karsastudio.biz.id"]);
const DEFAULT_DOMAIN = "kakdiko.web.id";

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const rawHost = (request.headers.get("host") || "").toLowerCase().split(":")[0];
    const cleanHost = rawHost.startsWith("www.") ? rawHost.slice(4) : rawHost;

    // 1. If accessed via one of the 13 custom domains:
    if (KNOWN_DOMAINS.has(cleanHost)) {
      if (!url.pathname.startsWith(`/${cleanHost}/`)) {
        const subPath = (url.pathname === "/" || url.pathname === "") ? "/index.html" : url.pathname;
        const targetPath = `/${cleanHost}${subPath}`;
        const rewrittenUrl = new URL(targetPath, url.origin);
        return env.ASSETS.fetch(new Request(rewrittenUrl.toString(), request));
      }
    }

    // 2. If accessed via *.workers.dev root (/), serve the Empire Command Center:
    if (url.pathname === "/" || url.pathname === "/index.html") {
      const ccUrl = new URL("/command-center/index.html", url.origin);
      return env.ASSETS.fetch(new Request(ccUrl.toString(), request));
    }

    return env.ASSETS.fetch(request);
  }
};
