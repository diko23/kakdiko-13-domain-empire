// Cloudflare Pages Advanced Mode (_worker.js)
// Automatically routes 13 custom domains from a single static deployment based on the Host header.

const KNOWN_DOMAINS = new Set(["kakdiko.web.id", "ekuitas.biz.id", "ekuitas.web.id", "ekuitas.my.id", "dividen.biz.id", "obligasi.biz.id", "ventura.web.id", "tender.biz.id", "kodelab.my.id", "kodelab.web.id", "kanvasdigital.web.id", "pustakaai.web.id", "karsastudio.biz.id"]);
const DEFAULT_DOMAIN = "kakdiko.web.id";

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const rawHost = (request.headers.get("host") || "").toLowerCase().split(":")[0];
    const cleanHost = rawHost.startsWith("www.") ? rawHost.slice(4) : rawHost;

    // If accessed via one of the 13 custom domains on Cloudflare Pages:
    if (KNOWN_DOMAINS.has(cleanHost)) {
      // Avoid double-prefixing if path already starts with /<domain>/
      if (!url.pathname.startsWith(`/${cleanHost}/`)) {
        const targetPath = url.pathname === "/" ? `/${cleanHost}/index.html` : `/${cleanHost}${url.pathname}`;
        const rewrittenUrl = new URL(targetPath, url.origin);
        return env.ASSETS.fetch(new Request(rewrittenUrl.toString(), request));
      }
    }

    return env.ASSETS.fetch(request);
  }
};
