import json
import re
import threading
import unittest
import urllib.request
import socketserver
from pathlib import Path

from build_monorepo import BASE_DIR, DIST_DIR, MANIFEST_PATH, build_all
from preview_server import MultiDomainRequestHandler

EXPECTED_13_DOMAINS = [
    "kakdiko.web.id",
    "ekuitas.biz.id",
    "ekuitas.web.id",
    "ekuitas.my.id",
    "dividen.biz.id",
    "obligasi.biz.id",
    "ventura.web.id",
    "tender.biz.id",
    "kodelab.my.id",
    "kodelab.web.id",
    "kanvasdigital.web.id",
    "pustakaai.web.id",
    "karsastudio.biz.id",
]


class TestDomainEmpireMonorepo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build_result = build_all()
        cls.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    def test_01_manifest_has_exact_13_domains(self):
        domains = [d["domain"] for d in self.manifest["domains"]]
        self.assertEqual(len(domains), 13)
        self.assertEqual(set(domains), set(EXPECTED_13_DOMAINS))

    def test_02_dist_artifacts_generated_for_all_13_domains(self):
        self.assertTrue((DIST_DIR / "command-center" / "index.html").exists(), "Command Center index.html missing")
        self.assertFalse((DIST_DIR / "_worker.js").exists(), "_worker.js must not be inside dist/ for Workers Assets")
        self.assertTrue((BASE_DIR / "worker.js").exists(), "Root worker.js missing")
        self.assertTrue((BASE_DIR / "wrangler.toml").exists(), "wrangler.toml missing")

        for dom in EXPECTED_13_DOMAINS:
            dom_dir = DIST_DIR / dom
            self.assertTrue((dom_dir / "index.html").exists(), f"{dom}/index.html missing")
            self.assertTrue((dom_dir / "logo.svg").exists(), f"{dom}/logo.svg missing")
            self.assertTrue((dom_dir / "sitemap.xml").exists(), f"{dom}/sitemap.xml missing")
            self.assertTrue((dom_dir / "robots.txt").exists(), f"{dom}/robots.txt missing")

    def test_03_json_ld_and_micro_tools_valid(self):
        for d_cfg in self.manifest["domains"]:
            dom = d_cfg["domain"]
            html = (DIST_DIR / dom / "index.html").read_text(encoding="utf-8")

            # Verify canonical link
            self.assertIn(f'<link rel="canonical" href="https://{dom}/" />', html)

            # Verify JSON-LD parses cleanly
            match = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
            self.assertIsNotNone(match, f"Missing JSON-LD in {dom}")
            ld_data = json.loads(match.group(1))
            self.assertEqual(ld_data["@type"], "WebApplication")
            self.assertEqual(ld_data["url"], f"https://{dom}/")

            # Verify all interactive inputs exist in HTML
            for inp in d_cfg["tool"]["inputs"]:
                self.assertIn(f'id="input_{inp["id"]}"', html, f"Missing input_{inp['id']} in {dom}")

            # Verify zero placeholders
            self.assertNotIn("TODO", html)
            self.assertNotIn("lorem ipsum", html.lower())
            self.assertIn("monetize-bar", html)

    def test_04_defensive_bundles_cross_linked(self):
        # Ekuitas 3-domain bundle check
        for eq_dom in ["ekuitas.biz.id", "ekuitas.web.id", "ekuitas.my.id"]:
            html = (DIST_DIR / eq_dom / "index.html").read_text(encoding="utf-8")
            self.assertIn("DEFENSIVE BRAND BUNDLE (3 DOMAIN)", html)
            self.assertIn("../ekuitas.biz.id/", html)
            self.assertIn("../ekuitas.web.id/", html)
            self.assertIn("../ekuitas.my.id/", html)
            self.assertIn("6282323965780", html)
            self.assertIn("dickynoko23@gmail.com", html)

        # KodeLab 2-domain bundle check
        for kl_dom in ["kodelab.my.id", "kodelab.web.id"]:
            html = (DIST_DIR / kl_dom / "index.html").read_text(encoding="utf-8")
            self.assertIn("DEFENSIVE BRAND BUNDLE (2 DOMAIN)", html)
            self.assertIn("../kodelab.my.id/", html)
            self.assertIn("../kodelab.web.id/", html)

    def test_05_http_preview_server_and_host_routing(self):
        socketserver.TCPServer.allow_reuse_address = True
        httpd = socketserver.TCPServer(("127.0.0.1", 0), MultiDomainRequestHandler)
        port = httpd.server_address[1]
        server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        server_thread.start()

        try:
            # 1. Test /api/domains endpoint
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/domains", timeout=5) as resp:
                self.assertEqual(resp.status, 200)
                api_data = json.loads(resp.read().decode("utf-8"))
                self.assertEqual(api_data["count"], 13)

            # 2. Test path-based routing for all 13 domains
            for dom in EXPECTED_13_DOMAINS:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/{dom}/", timeout=5) as resp:
                    self.assertEqual(resp.status, 200)
                    body = resp.read().decode("utf-8")
                    self.assertIn(dom, body)

            # 3. Test Host-header routing (simulating Cloudflare Edge request to https://dividen.biz.id/)
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/",
                headers={"Host": "dividen.biz.id"},
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                self.assertEqual(resp.status, 200)
                body = resp.read().decode("utf-8")
                self.assertIn("Kalkulator Dividend Yield Bersih", body)
        finally:
            httpd.shutdown()
            httpd.server_close()

    def test_06_vps_workhorse_router_and_farming_engine(self):
        from vps_engine.empire_workhorse import ThreadedWorkhorseServer, WorkhorseRequestHandler, init_db

        init_db()
        httpd = ThreadedWorkhorseServer(("127.0.0.1", 0), WorkhorseRequestHandler)
        port = httpd.server_address[1]
        server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        server_thread.start()

        try:
            # 1. Test Keep-Alive endpoint
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/keepalive", timeout=5) as resp:
                self.assertEqual(resp.status, 200)
                ka = json.loads(resp.read().decode("utf-8"))
                self.assertEqual(ka["status"], "ALIVE")

            # 2. Test Multi-LLM AI Router & SQLite Cache Hit
            chat_payload = json.dumps({"prompt": "Tes efisiensi dividen IDX 2026", "model": "auto"}).encode("utf-8")
            req1 = urllib.request.Request(
                f"http://127.0.0.1:{port}/api/v1/router/chat",
                data=chat_payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req1, timeout=10) as r1:
                d1 = json.loads(r1.read().decode("utf-8"))
                self.assertEqual(d1["status"], "success")

            req2 = urllib.request.Request(
                f"http://127.0.0.1:{port}/api/v1/router/chat",
                data=chat_payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req2, timeout=10) as r2:
                d2 = json.loads(r2.read().decode("utf-8"))
                self.assertTrue(d2["cached"], "Second identical prompt must be served from SQLite cache")

            # 3. Test Vector Asset Pack Factory
            vec_req = urllib.request.Request(
                f"http://127.0.0.1:{port}/api/v1/farm/vectors",
                data=json.dumps({"theme": "Unit Test Vector Pack"}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(vec_req, timeout=10) as rv:
                dv = json.loads(rv.read().decode("utf-8"))
                self.assertEqual(dv["count"], 6)
        finally:
            httpd.shutdown()
            httpd.server_close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
