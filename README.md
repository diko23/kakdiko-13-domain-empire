# KakDiko 13-Domain AI-Driven Static Monorepo

Arsitektur **AI-Driven Static Monorepo** untuk mengelola, men-generate, dan menyajikan **13 properti domain nasional (`.web.id`, `.biz.id`, `.my.id`)** lengkap dengan **13 Interactive Micro-Tools**, logo SVG mandiri, skema SEO JSON-LD, serta sistem akuisisi domain terpadu dalam satu repositori ringan (`< 1 MB`, *Zero-Node-Modules*).

## Katalog 13 Properti Digital

| No | Domain | Brand | Micro-Tool Interaktif | Kontak Akuisisi |
| :--- | :--- | :--- | :--- | :--- |
| 1 | `kakdiko.web.id` | KakDiko Digital Venture | Simulator Valuasi & ROI Portofolio Domain | Aset Inti Pribadi |
| 2 | `ekuitas.biz.id` | Ekuitas Korporat & Valuasi | Kalkulator Graham Fair Value, ROE, PER & PBV | Paket 3-Domain Ekuitas |
| 3 | `ekuitas.web.id` | Pustaka Riset Ekuitas | Simulator Compounding Ekuitas & DCA Bulanan (CAGR) | Paket 3-Domain Ekuitas |
| 4 | `ekuitas.my.id` | EkuitasKu Portfolio Rebalancer | Kalkulator Rebalancing Portofolio Ritel | Paket 3-Domain Ekuitas |
| 5 | `dividen.biz.id` | Dividen IDX & Cashflow | Kalkulator Dividend Yield Bersih, Pajak & DRIP | Tersedia untuk Akuisisi |
| 6 | `obligasi.biz.id` | Obligasi & Simulator SBN | Simulator Kupon Bersih Bulanan SBN/FR vs Deposito | Tersedia untuk Akuisisi |
| 7 | `ventura.web.id` | Ventura & Cap Table Lab | Simulator Valuasi Pre/Post-Money & Dilusi Startup | Tersedia untuk Akuisisi |
| 8 | `tender.biz.id` | Tender & Pengadaan B2B | Kalkulator Penawaran HPS, DPP, PPN 11% & PPh | Tersedia untuk Akuisisi |
| 9 | `kodelab.my.id` | KodeLab Sandbox | Kalkulator Bandwidth API & Kompresi Brotli | Paket 2-Domain KodeLab |
| 10 | `kodelab.web.id` | KodeLab Cloud Architecture | Simulator Break-Even Serverless vs Cluster VPS | Paket 2-Domain KodeLab |
| 11 | `kanvasdigital.web.id` | KanvasDigital Studio | Kalkulator Resolusi Kanvas DPI & Efisiensi Vektor SVG | Tersedia untuk Akuisisi |
| 12 | `pustakaai.web.id` | PustakaAI Indonesia | Kalkulator Biaya Token API Multi-LLM & Routing | Tersedia untuk Akuisisi |
| 13 | `karsastudio.biz.id` | Karsa Studio Digital | Kalkulator Estimasi Biaya & Jam Kerja Proyek B2B | Tersedia untuk Akuisisi |

## Kontak Pemilik & Akuisisi
- **Pemilik**: Kak Diko (`kakdiko.web.id`)
- **WhatsApp**: [+62 823-2396-5780](https://wa.me/6282323965780)
- **Email**: [dickynoko23@gmail.com](mailto:dickynoko23@gmail.com)

## Perintah Build & Pengujian Lokal

```bash
python build_monorepo.py
python test_monorepo.py
python preview_server.py --port 8080
```

## Deployment ke Cloudflare Pages (Multi-Domain Edge)
1. Buka **Cloudflare Dashboard > Workers & Pages > Create > Pages > Connect to Git**.
2. Pilih repositori **`diko23/kakdiko-13-domain-empire`**.
3. Isi konfigurasi build:
   - **Build command**: `python build_monorepo.py`
   - **Build output directory**: `dist`
4. Setelah aktif, tambahkan ke-13 domain di tab **Custom Domains**. File `dist/_worker.js` otomatis merutekan pengunjung ke direktori domain yang sesuai berdasarkan `Host` header.
