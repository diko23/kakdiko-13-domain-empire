import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error
from pathlib import Path

from build_monorepo import MANIFEST_PATH, build_all


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s-]+", "-", text)
    return text.strip("-")


def get_env_or_reg(key_name: str) -> str | None:
    val = os.environ.get(key_name)
    if val:
        return val
    try:
        import winreg
        reg_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment")
        val, _ = winreg.QueryValueEx(reg_key, key_name)
        winreg.CloseKey(reg_key)
        return val
    except Exception:
        return None


def call_llm_article_generator(domain_cfg: dict, topic: str) -> dict:
    """
    Attempts to call Gemini API (GEMINI_API_KEY) or OpenAI-compatible API (AGNES_API_KEY)
    to generate a structured SEO article JSON. Falls back to a deterministic domain-grounded
    synthesis if no external API key is reachable.
    """
    domain = domain_cfg["domain"]
    brand = domain_cfg["brand_name"]
    category = domain_cfg["category"]

    prompt = (
        f"Anda adalah editor ahli untuk properti digital '{brand}' ({domain}) di kategori {category}. "
        f"Buat 1 artikel SEO pilar berbahasa Indonesia tentang topik: '{topic}'. "
        "Kembalikan HANYA objek JSON murni dengan kunci: "
        '{"title": "...", "summary": "... (2-3 kalimat padat bernilai tinggi)", "read_time": "5 menit"}'
    )

    gemini_key = get_env_or_reg("GEMINI_API_KEY")
    if gemini_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"responseMimeType": "application/json"},
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                parsed = json.loads(raw_text)
                return {
                    "slug": slugify(parsed["title"]),
                    "title": parsed["title"],
                    "summary": parsed["summary"],
                    "read_time": parsed.get("read_time", "5 menit"),
                }
        except Exception as e:
            print(f"[i] Info: Gemini API call skipped ({e}), using local structured engine.")

    # Deterministic, domain-grounded synthesis when offline or no token needed
    clean_topic = topic.strip()
    return {
        "slug": slugify(f"{clean_topic}-{domain.split('.')[0]}"),
        "title": f"{clean_topic}: Panduan Strategis & Simulasi Data pada {brand}",
        "summary": (
            f"Analisis mendalam mengenai {clean_topic.lower()} yang dilengkapi kerangka evaluasi kuantitatif, "
            f"mitigasi risiko, dan langkah implementasi praktis menggunakan simulator interaktif {domain}."
        ),
        "read_time": "6 menit",
    }


def list_domains() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    print("=" * 88)
    print(f"{'No':<4} {'Domain':<22} {'Tier':<26} {'Articles':<10} {'Harga Akuisisi'}")
    print("=" * 88)
    for idx, d in enumerate(manifest["domains"], 1):
        price_str = d["acquisition"]["price_label"] if d["for_sale"] else "Aset Inti (Non-Resale)"
        print(f"{idx:<4} {d['domain']:<22} {d['tier']:<26} {len(d['articles']):<10} {price_str}")
    print("=" * 88)


def add_article(domain_name: str, topic: str) -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    target = None
    for d in manifest["domains"]:
        if d["domain"].lower() == domain_name.lower():
            target = d
            break

    if not target:
        print(f"[!] Error: Domain '{domain_name}' tidak ditemukan di manifest.")
        sys.exit(1)

    article = call_llm_article_generator(target, topic)
    # Prevent duplicate slugs
    existing_slugs = {a["slug"] for a in target["articles"]}
    if article["slug"] in existing_slugs:
        print(f"[i] Artikel dengan slug '{article['slug']}' sudah ada, memperbarui ringkasan.")
        for a in target["articles"]:
            if a["slug"] == article["slug"]:
                a.update(article)
    else:
        target["articles"].insert(0, article)

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    build_res = build_all()
    print(f"[OK] Artikel baru berhasil ditambahkan ke {domain_name}:")
    print(f"    Judul : {article['title']}")
    print(f"    Slug  : #{article['slug']}")
    print(f"[OK] Monorepo ({build_res['count']} domain) telah di-build ulang secara otomatis.")


def update_price(domain_name: str, price_idr: int, price_label: str | None = None) -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    updated = []
    for d in manifest["domains"]:
        if d["domain"].lower() == domain_name.lower() or domain_name.lower() in [
            b.lower() for b in d["acquisition"]["bundle_domains"]
        ]:
            d["acquisition"]["price_idr"] = price_idr
            if price_label:
                d["acquisition"]["price_label"] = price_label
            else:
                formatted = f"Rp {price_idr:,.0f}".replace(",", ".")
                d["acquisition"]["price_label"] = formatted
            updated.append(d["domain"])

    if not updated:
        print(f"[!] Error: Domain '{domain_name}' tidak ditemukan.")
        sys.exit(1)

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    build_all()
    print(f"[OK] Valuasi akuisisi diperbarui untuk {', '.join(updated)} -> Rp {price_idr:,.0f}".replace(",", "."))


def main():
    parser = argparse.ArgumentParser(description="AI Content & Valuation Manager for 13-Domain Static Monorepo")
    parser.add_argument("--list", action="store_true", help="Tampilkan daftar 13 domain beserta statusnya")
    parser.add_argument("--domain", type=str, help="Nama domain target (contoh: dividen.biz.id)")
    parser.add_argument("--topic", type=str, help="Topik artikel SEO baru yang ingin di-generate ke domain tersebut")
    parser.add_argument("--set-price", type=int, help="Ubah harga valuasi akuisisi domain (dalam Rupiah)")
    parser.add_argument("--price-label", type=str, help="Label harga kustom (opsional)")

    args = parser.parse_args()
    if args.list:
        list_domains()
    elif args.domain and args.topic:
        add_article(args.domain, args.topic)
    elif args.domain and args.set_price is not None:
        update_price(args.domain, args.set_price, args.price_label)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
