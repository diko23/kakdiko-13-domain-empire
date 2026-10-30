import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MANIFEST_PATH = BASE_DIR / "domains_manifest.json"
DIST_DIR = BASE_DIR / "dist"


def generate_svg_logo(icon_type: str, primary: str, accent: str, brand_name: str) -> str:
    """Generates a clean, scalable vector SVG logo tailored to each domain's icon_type."""
    shapes = {
        "hub": f"""
            <polygon points="32,6 54,19 54,45 32,58 10,45 10,19" fill="none" stroke="{primary}" stroke-width="3.5"/>
            <circle cx="32" cy="32" r="8" fill="{accent}"/>
            <line x1="32" y1="6" x2="32" y2="24" stroke="{accent}" stroke-width="2.5"/>
            <line x1="54" y1="19" x2="39" y2="28" stroke="{accent}" stroke-width="2.5"/>
            <line x1="54" y1="45" x2="39" y2="36" stroke="{accent}" stroke-width="2.5"/>
            <line x1="32" y1="58" x2="32" y2="40" stroke="{accent}" stroke-width="2.5"/>
            <line x1="10" y1="45" x2="25" y2="36" stroke="{accent}" stroke-width="2.5"/>
            <line x1="10" y1="19" x2="25" y2="28" stroke="{accent}" stroke-width="2.5"/>
        """,
        "equity": f"""
            <rect x="10" y="34" width="9" height="20" rx="2" fill="{primary}" opacity="0.7"/>
            <rect x="23" y="24" width="9" height="30" rx="2" fill="{primary}" opacity="0.85"/>
            <rect x="36" y="14" width="9" height="40" rx="2" fill="{accent}"/>
            <polyline points="12,26 27,16 41,10 54,6" fill="none" stroke="{accent}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>
            <circle cx="54" cy="6" r="4" fill="{primary}"/>
        """,
        "chart": f"""
            <path d="M8,52 L56,52" stroke="{primary}" stroke-width="3" stroke-linecap="round"/>
            <path d="M10,44 Q24,40 32,26 T54,10" fill="none" stroke="{accent}" stroke-width="4" stroke-linecap="round"/>
            <path d="M10,44 Q24,40 32,26 T54,10 L54,52 L10,52 Z" fill="{primary}" opacity="0.22"/>
            <circle cx="32" cy="26" r="4" fill="{accent}"/>
            <circle cx="54" cy="10" r="4.5" fill="{primary}"/>
        """,
        "pie": f"""
            <circle cx="30" cy="34" r="20" fill="none" stroke="{primary}" stroke-width="5"/>
            <path d="M30,34 L30,14 A20,20 0 0,1 50,34 Z" fill="{accent}"/>
            <path d="M34,30 L34,10 A20,20 0 0,1 54,30 Z" fill="{primary}" opacity="0.85"/>
        """,
        "dividend": f"""
            <circle cx="32" cy="32" r="22" fill="none" stroke="{primary}" stroke-width="3.5"/>
            <path d="M26,22 C26,18 38,18 38,24 C38,29 25,29 25,36 C25,42 38,42 38,37" fill="none" stroke="{accent}" stroke-width="3.5" stroke-linecap="round"/>
            <line x1="32" y1="15" x2="32" y2="49" stroke="{accent}" stroke-width="3" stroke-linecap="round"/>
            <polyline points="44,14 52,14 52,22" fill="none" stroke="{primary}" stroke-width="3" stroke-linecap="round"/>
        """,
        "bond": f"""
            <rect x="10" y="14" width="44" height="36" rx="5" fill="none" stroke="{primary}" stroke-width="3.5"/>
            <circle cx="32" cy="32" r="9" fill="none" stroke="{accent}" stroke-width="3"/>
            <line x1="16" y1="22" x2="22" y2="22" stroke="{accent}" stroke-width="3" stroke-linecap="round"/>
            <line x1="42" y1="22" x2="48" y2="22" stroke="{accent}" stroke-width="3" stroke-linecap="round"/>
            <line x1="16" y1="42" x2="22" y2="42" stroke="{accent}" stroke-width="3" stroke-linecap="round"/>
            <line x1="42" y1="42" x2="48" y2="42" stroke="{accent}" stroke-width="3" stroke-linecap="round"/>
        """,
        "venture": f"""
            <path d="M32,8 L46,28 L38,28 L38,50 L26,50 L26,28 L18,28 Z" fill="none" stroke="{accent}" stroke-width="3.5" stroke-linejoin="round"/>
            <circle cx="32" cy="22" r="3.5" fill="{primary}"/>
            <line x1="22" y1="56" x2="42" y2="56" stroke="{primary}" stroke-width="3.5" stroke-linecap="round"/>
        """,
        "tender": f"""
            <rect x="12" y="10" width="34" height="44" rx="4" fill="none" stroke="{primary}" stroke-width="3.5"/>
            <line x1="20" y1="22" x2="38" y2="22" stroke="{accent}" stroke-width="3" stroke-linecap="round"/>
            <line x1="20" y1="31" x2="38" y2="31" stroke="{accent}" stroke-width="3" stroke-linecap="round"/>
            <polyline points="20,41 25,46 36,36" fill="none" stroke="{accent}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>
        """,
        "code": f"""
            <polyline points="22,20 10,32 22,44" fill="none" stroke="{primary}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
            <polyline points="42,20 54,32 42,44" fill="none" stroke="{primary}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
            <line x1="36" y1="14" x2="28" y2="50" stroke="{accent}" stroke-width="3.5" stroke-linecap="round"/>
        """,
        "server": f"""
            <rect x="10" y="12" width="44" height="14" rx="3" fill="none" stroke="{primary}" stroke-width="3"/>
            <rect x="10" y="36" width="44" height="14" rx="3" fill="none" stroke="{accent}" stroke-width="3"/>
            <circle cx="18" cy="19" r="2.5" fill="{accent}"/>
            <circle cx="18" cy="43" r="2.5" fill="{primary}"/>
            <line x1="28" y1="19" x2="46" y2="19" stroke="{primary}" stroke-width="3" stroke-linecap="round"/>
            <line x1="28" y1="43" x2="46" y2="43" stroke="{accent}" stroke-width="3" stroke-linecap="round"/>
        """,
        "canvas": f"""
            <path d="M12,48 L32,12 L52,48 Z" fill="none" stroke="{primary}" stroke-width="3.5" stroke-linejoin="round"/>
            <circle cx="32" cy="34" r="7" fill="{accent}" opacity="0.85"/>
            <circle cx="48" cy="18" r="5" fill="none" stroke="{accent}" stroke-width="3"/>
        """,
        "ai": f"""
            <path d="M32,8 L37,25 L54,30 L37,35 L32,52 L27,35 L10,30 L27,25 Z" fill="none" stroke="{accent}" stroke-width="3.5" stroke-linejoin="round"/>
            <circle cx="32" cy="30" r="4" fill="{primary}"/>
        """,
        "studio": f"""
            <rect x="12" y="12" width="18" height="18" rx="4" fill="none" stroke="{primary}" stroke-width="3.5"/>
            <rect x="34" y="12" width="18" height="18" rx="4" fill="{accent}" opacity="0.85"/>
            <rect x="12" y="34" width="18" height="18" rx="4" fill="{primary}" opacity="0.4"/>
            <rect x="34" y="34" width="18" height="18" rx="4" fill="none" stroke="{accent}" stroke-width="3.5"/>
        """,
    }
    inner = shapes.get(icon_type, shapes["hub"])
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="44" height="44" role="img" aria-label="{brand_name} Logo">
  <rect width="64" height="64" rx="14" fill="#0f172a" stroke="{primary}" stroke-opacity="0.35" stroke-width="1.5"/>
  {inner}
</svg>"""


JS_FORMULA_ENGINE = r"""
function formatIDR(num) {
  if (!isFinite(num)) return "Rp 0";
  return "Rp " + Math.round(num).toLocaleString("id-ID");
}

function formatNum(num, decimals = 2) {
  if (!isFinite(num)) return "0";
  return Number(num).toLocaleString("id-ID", {
    minimumFractionDigits: 0,
    maximumFractionDigits: decimals
  });
}

function runMicroTool(formulaId) {
  const getVal = (id) => {
    const el = document.getElementById("input_" + id);
    return el ? parseFloat(el.value) || 0 : 0;
  };

  let cards = [];
  let insight = "";
  let healthPct = 75;

  if (formulaId === "empire_roi") {
    const count = getVal("domain_count");
    const cost = getVal("acq_cost");
    const visitors = getVal("avg_visitors");
    const salePrice = getVal("avg_sale_price");
    const sellRate = getVal("sell_through_rate") / 100;

    const totalVisitorsYear = count * visitors * 12;
    const expectedDomainsSold = Math.max(1, Math.round(count * sellRate));
    const grossFlipRevenue = expectedDomainsSold * salePrice;
    const totalPortfolioVal = count * salePrice;
    const netRoiMultiple = cost > 0 ? (grossFlipRevenue - cost) / cost : 0;

    cards = [
      { label: "Valuasi Katalog Penuh", value: formatIDR(totalPortfolioVal), sub: count + " Domain Aktif" },
      { label: "Proyeksi Penjualan Tahunan", value: formatIDR(grossFlipRevenue), sub: expectedDomainsSold + " Domain Terjual / Thn" },
      { label: "Total Trafik Organik / Thn", value: formatNum(totalVisitorsYear, 0) + " UV", sub: formatNum(count * visitors, 0) + " UV / Bulan" },
      { label: "Kelipatan ROI (Multiple)", value: formatNum(netRoiMultiple, 0) + "x Modal", sub: "Modal Awal: " + formatIDR(cost) }
    ];
    healthPct = Math.min(100, Math.max(20, sellRate * 180));
    insight = `Dengan modal akuisisi ${formatIDR(cost)} untuk ${count} domain, terjualnya ${expectedDomainsSold} domain saja pada harga rata-rata ${formatIDR(salePrice)} menghasilkan arus kas ${formatIDR(grossFlipRevenue)} (${formatNum(netRoiMultiple, 0)}x lipat modal awal).`;
  }
  else if (formulaId === "equity_valuation") {
    const price = getVal("stock_price");
    const eps = getVal("eps");
    const bvps = getVal("bvps");
    const der = getVal("total_debt_ratio");

    const per = eps > 0 ? price / eps : 0;
    const pbv = bvps > 0 ? price / bvps : 0;
    const roe = bvps > 0 ? (eps / bvps) * 100 : 0;
    const grahamFair = (eps > 0 && bvps > 0) ? Math.sqrt(22.5 * eps * bvps) : 0;
    const mos = grahamFair > 0 ? ((grahamFair - price) / grahamFair) * 100 : 0;

    cards = [
      { label: "Nilai Wajar Benjamin Graham", value: formatIDR(grahamFair), sub: mos >= 0 ? "Diskon (MoS): +" + formatNum(mos, 1) + "%" : "Premium: " + formatNum(mos, 1) + "%" },
      { label: "Return on Equity (ROE)", value: formatNum(roe, 2) + "%", sub: roe >= 15 ? "Profitabilitas Unggul (>=15%)" : "Profitabilitas Moderat" },
      { label: "Price to Earnings (PER)", value: formatNum(per, 2) + "x", sub: "EPS: " + formatIDR(eps) },
      { label: "Price to Book Value (PBV)", value: formatNum(pbv, 2) + "x", sub: "DER Neraca: " + formatNum(der, 0) + "%" }
    ];
    healthPct = Math.min(100, Math.max(15, 50 + mos));
    insight = mos > 15
      ? `Saham berada di bawah nilai intrinsik Graham (${formatIDR(grahamFair)}) dengan Margin of Safety ${formatNum(mos, 1)}% dan ROE ${formatNum(roe, 1)}%. Layak masuk daftar pantau akumulasi.`
      : `Harga pasar (${formatIDR(price)}) sudah mendekati atau melampaui estimasi Graham Number (${formatIDR(grahamFair)}). Pastikan pertumbuhan laba (EPS growth) mendukung valuasi premium ini.`;
  }
  else if (formulaId === "equity_cagr") {
    const initial = getVal("initial_capital");
    const monthly = getVal("monthly_topup");
    const rate = getVal("annual_return") / 100;
    const years = getVal("years");

    const months = years * 12;
    const monthlyRate = rate / 12;
    const fvInitial = initial * Math.pow(1 + monthlyRate, months);
    const fvSip = monthlyRate > 0 ? monthly * ((Math.pow(1 + monthlyRate, months) - 1) / monthlyRate) : monthly * months;
    const totalFv = fvInitial + fvSip;
    const totalPrincipal = initial + (monthly * months);
    const totalGain = totalFv - totalPrincipal;
    const gainPct = totalPrincipal > 0 ? (totalGain / totalPrincipal) * 100 : 0;

    cards = [
      { label: "Nilai Akhir Portofolio", value: formatIDR(totalFv), sub: "Horizon " + years + " Tahun" },
      { label: "Total Pokok Disetor", value: formatIDR(totalPrincipal), sub: "DCA: " + formatIDR(monthly) + "/bln" },
      { label: "Keuntungan Bunga Majemuk", value: formatIDR(totalGain), sub: "+" + formatNum(gainPct, 1) + "% di atas Modal Pokok" },
      { label: "Estimasi Return Bulanan di Akhir", value: formatIDR((totalFv * rate) / 12), sub: "Passive Yield @ " + formatNum(rate * 100, 1) + "% p.a." }
    ];
    healthPct = Math.min(100, Math.max(25, (totalGain / Math.max(1, totalFv)) * 100));
    insight = `Dalam ${years} tahun, porsi hasil compounding mencapai ${formatIDR(totalGain)} (${formatNum((totalGain / Math.max(1, totalFv)) * 100, 1)}% dari total kekayaan akhir), membuktikan efek bola salju ekuitas.`;
  }
  else if (formulaId === "rebalance_calc") {
    const eq = getVal("current_equity");
    const fix = getVal("current_fixed");
    const targetEqPct = getVal("target_equity_pct") / 100;
    const cashIn = getVal("new_cash_injection");

    const currentTotal = eq + fix;
    const newTotal = currentTotal + cashIn;
    const currentEqWeight = currentTotal > 0 ? (eq / currentTotal) * 100 : 0;
    const targetEqAmount = newTotal * targetEqPct;
    const targetFixAmount = newTotal * (1 - targetEqPct);
    const deltaEq = targetEqAmount - eq;
    const deltaFix = targetFixAmount - fix;

    cards = [
      { label: "Total Portofolio Baru", value: formatIDR(newTotal), sub: "Bobot Saat Ini: " + formatNum(currentEqWeight, 1) + "% Ekuitas" },
      { label: "Target Ideal Ekuitas", value: formatIDR(targetEqAmount), sub: "Target Bobot: " + formatNum(targetEqPct * 100, 0) + "%" },
      { label: "Aksi pada Ekuitas (Saham)", value: (deltaEq >= 0 ? "Beli " : "Jual ") + formatIDR(Math.abs(deltaEq)), sub: deltaEq >= 0 ? "Tambah Akumulasi Saham" : "Amankan Profit (Trimming)" },
      { label: "Aksi pada Obligasi / Kas", value: (deltaFix >= 0 ? "Tambah " : "Kurangi ") + formatIDR(Math.abs(deltaFix)), sub: "Target Defensif: " + formatIDR(targetFixAmount) }
    ];
    healthPct = Math.max(20, 100 - Math.abs(currentEqWeight - targetEqPct * 100) * 2);
    insight = deltaEq >= 0
      ? `Untuk mencapai bobot ideal ${formatNum(targetEqPct * 100, 0)}% ekuitas, alokasikan ${formatIDR(deltaEq)} ke saham dan ${formatIDR(deltaFix)} ke instrumen pendapatan tetap/kas.`
      : `Porsi saham Anda saat ini (${formatNum(currentEqWeight, 1)}%) melebihi target (${formatNum(targetEqPct * 100, 0)}%). Lakukan profit-taking saham sebesar ${formatIDR(Math.abs(deltaEq))} dan pindahkan ke instrumen defensif.`;
  }
  else if (formulaId === "dividend_calc") {
    const lots = getVal("lots");
    const shares = lots * 100;
    const buyPrice = getVal("avg_buy_price");
    const dps = getVal("dps");
    const taxRate = getVal("tax_rate") / 100;

    const capitalInvested = shares * buyPrice;
    const grossDiv = shares * dps;
    const taxAmount = grossDiv * taxRate;
    const netDiv = grossDiv - taxAmount;
    const grossYield = buyPrice > 0 ? (dps / buyPrice) * 100 : 0;
    const netYield = buyPrice > 0 ? ((dps * (1 - taxRate)) / buyPrice) * 100 : 0;
    const drip5Years = capitalInvested * Math.pow(1 + (netYield / 100), 5);

    cards = [
      { label: "Dividen Bersih Diterima / Thn", value: formatIDR(netDiv), sub: "Setara " + formatIDR(netDiv / 12) + " / bulan" },
      { label: "Net Dividend Yield", value: formatNum(netYield, 2) + "%", sub: "Gross Yield: " + formatNum(grossYield, 2) + "%" },
      { label: "Potongan Pajak PPh Dividen", value: formatIDR(taxAmount), sub: taxRate === 0 ? "Bebas Pajak (PMK Reinvestasi)" : "PPh Final " + formatNum(taxRate * 100, 0) + "%" },
      { label: "Proyeksi DRIP 5 Tahun", value: formatIDR(drip5Years), sub: "Modal Pokok: " + formatIDR(capitalInvested) }
    ];
    healthPct = Math.min(100, Math.max(20, netYield * 10));
    insight = `Dari ${formatNum(lots, 0)} lot (${formatNum(shares, 0)} lembar), Anda mengantongi dividen bersih ${formatIDR(netDiv)}/tahun (Net Yield ${formatNum(netYield, 2)}%). Jika digulung kembali (DRIP), modal ${formatIDR(capitalInvested)} tumbuh menjadi ${formatIDR(drip5Years)} dalam 5 tahun.`;
  }
  else if (formulaId === "bond_calc") {
    const principal = getVal("principal");
    const couponRate = getVal("coupon_rate") / 100;
    const depoRate = getVal("deposito_rate") / 100;
    const tenor = getVal("tenor_years");

    const grossAnnualBond = principal * couponRate;
    const netAnnualBond = grossAnnualBond * 0.90; // Pajak SBN/Obligasi 10%
    const netMonthlyBond = netAnnualBond / 12;

    const netAnnualDepo = (principal * depoRate) * 0.80; // Pajak Deposito 20%
    const diffAnnual = netAnnualBond - netAnnualDepo;
    const totalCouponTenor = netAnnualBond * tenor;

    cards = [
      { label: "Kupon Bersih / Bulan (SBN)", value: formatIDR(netMonthlyBond), sub: "Sudah Dipotong PPh 10%" },
      { label: "Total Kupon Bersih / Tahun", value: formatIDR(netAnnualBond), sub: "Effective Net Yield: " + formatNum(couponRate * 90, 2) + "%" },
      { label: "Keunggulan vs Deposito / Thn", value: "+" + formatIDR(diffAnnual), sub: "Deposito Bersih: " + formatIDR(netAnnualDepo) + "/thn" },
      { label: "Akumulasi Kupon " + tenor + " Tahun", value: formatIDR(totalCouponTenor), sub: "+ Kembalinya Pokok " + formatIDR(principal) }
    ];
    healthPct = Math.min(100, Math.max(30, couponRate * 1200));
    insight = `Dengan tarif pajak SBN yang hanya 10% (vs 20% pada deposito), Anda menerima cashflow pasif ${formatIDR(netMonthlyBond)} setiap bulan dan unggul ${formatIDR(diffAnnual)} per tahun dibanding deposito bank.`;
  }
  else if (formulaId === "vc_calc") {
    const preMoney = getVal("pre_money") * 1000000;
    const invest = getVal("investment_amount") * 1000000;
    const founderPrior = getVal("founder_prior_pct");
    const esopPct = getVal("esop_pool_pct");

    const postMoney = preMoney + invest;
    const investorPct = postMoney > 0 ? (invest / postMoney) * 100 : 0;
    const retentionFactor = Math.max(0, (100 - investorPct - esopPct) / 100);
    const founderPostPct = founderPrior * retentionFactor;
    const founderEquityValue = postMoney * (founderPostPct / 100);

    cards = [
      { label: "Valuasi Post-Money", value: formatIDR(postMoney), sub: "Pre-Money: " + formatIDR(preMoney) },
      { label: "Porsi Ekuitas Investor (VC)", value: formatNum(investorPct, 2) + "%", sub: "Suntikan: " + formatIDR(invest) },
      { label: "Kepemilikan Founder Pasca-Ronde", value: formatNum(founderPostPct, 2) + "%", sub: "Turun dari " + formatNum(founderPrior, 1) + "% (+ESOP " + esopPct + "%)" },
      { label: "Nilai Valuasi Saham Founder", value: formatIDR(founderEquityValue), sub: "Peningkatan Nilai Kertas Ekuitas" }
    ];
    healthPct = Math.min(100, Math.max(20, founderPostPct));
    insight = `Pendanaan ${formatIDR(invest)} pada valuasi Pre-Money ${formatIDR(preMoney)} menghasilkan Post-Money ${formatIDR(postMoney)}. Investor memegang ${formatNum(investorPct, 2)}% dan kepemilikan founder terdilusi menjadi ${formatNum(founderPostPct, 2)}% (senilai ${formatIDR(founderEquityValue)}).`;
  }
  else if (formulaId === "tender_calc") {
    const hps = getVal("hps_total");
    const bidPct = getVal("bid_pct_hps") / 100;
    const cogs = getVal("cogs_real");
    const pphRate = getVal("pph_rate") / 100;

    const bidGross = hps * bidPct;
    const dpp = bidGross * (100 / 111); // PPN 11%
    const ppn = bidGross - dpp;
    const pph = dpp * pphRate;
    const netCashReceived = dpp - pph;
    const netProfit = netCashReceived - cogs;
    const netMarginPct = dpp > 0 ? (netProfit / dpp) * 100 : 0;

    cards = [
      { label: "Nilai Penawaran Kontrak (Incl. PPN)", value: formatIDR(bidGross), sub: formatNum(bidPct * 100, 1) + "% dari Pagu HPS" },
      { label: "Nilai DPP (Excl. PPN 11%)", value: formatIDR(dpp), sub: "PPN 11%: " + formatIDR(ppn) },
      { label: "Kas Bersih Masuk (Setelah PPh)", value: formatIDR(netCashReceived), sub: "Potongan PPh: " + formatIDR(pph) },
      { label: "Laba Bersih Kontraktor", value: formatIDR(netProfit), sub: "Net Margin: " + formatNum(netMarginPct, 2) + "% terhadap DPP" }
    ];
    healthPct = Math.min(100, Math.max(15, netMarginPct * 3));
    const warn80 = (bidPct * 100) < 80 ? " [PERHATIAN: Penawaran di bawah 80% HPS wajib menyiapkan dokumen klarifikasi kewajaran harga!]" : " [Penawaran berada di zona aman >= 80% HPS]";
    insight = `Setelah dipotong PPN 11% (${formatIDR(ppn)}) dan PPh (${formatIDR(pph)}), kas bersih yang diterima rekening vendor adalah ${formatIDR(netCashReceived)}, menghasilkan laba bersih ${formatIDR(netProfit)} (${formatNum(netMarginPct, 1)}%).` + warn80;
  }
  else if (formulaId === "payload_calc") {
    const rawKb = getVal("json_kb");
    const compPct = getVal("compression_pct") / 100;
    const rps = getVal("avg_rps");
    const priceGb = getVal("egress_price_gb");

    const compressedKb = rawKb * (1 - compPct);
    const monthlyRequests = rps * 86400 * 30;
    const rawMonthlyGb = (monthlyRequests * rawKb) / (1024 * 1024);
    const compMonthlyGb = (monthlyRequests * compressedKb) / (1024 * 1024);
    const savedCostIdr = (rawMonthlyGb - compMonthlyGb) * priceGb;

    cards = [
      { label: "Ukuran Payload Terkompresi", value: formatNum(compressedKb, 2) + " KB", sub: "Dari Mentah " + formatNum(rawKb, 0) + " KB" },
      { label: "Total Request / Bulan", value: formatNum(monthlyRequests / 1000000, 1) + " Juta", sub: "Trafik Konstan " + rps + " RPS" },
      { label: "Bandwidth Bulanan (Brotli)", value: formatNum(compMonthlyGb, 1) + " GB", sub: "Tanpa Kompresi: " + formatNum(rawMonthlyGb, 1) + " GB" },
      { label: "Penghematan Biaya Egress", value: formatIDR(savedCostIdr) + "/bln", sub: "Biaya Aktif: " + formatIDR(compMonthlyGb * priceGb) }
    ];
    healthPct = Math.min(100, Math.max(20, compPct * 110));
    insight = `Kompresi Brotli/Gzip memangkas transfer data bulanan dari ${formatNum(rawMonthlyGb, 1)} GB menjadi ${formatNum(compMonthlyGb, 1)} GB pada beban ${rps} RPS, menghemat biaya bandwidth sebesar ${formatIDR(savedCostIdr)}/bulan.`;
  }
  else if (formulaId === "cloud_cost_calc") {
    const reqMillions = getVal("monthly_requests_m");
    const durationMs = getVal("avg_duration_ms");
    const memMb = getVal("memory_mb");
    const vpsIdr = getVal("vps_monthly_idr");

    const totalReqs = reqMillions * 1000000;
    const gbSeconds = totalReqs * (durationMs / 1000) * (memMb / 1024);
    // Standard serverless pricing ~ $0.00001667 per GB-s + $0.20 per 1M reqs (converted @ Rp16.200)
    const serverlessUsd = (gbSeconds * 0.00001667) + (reqMillions * 0.20);
    const serverlessIdr = serverlessUsd * 16200;
    const diffIdr = serverlessIdr - vpsIdr;

    cards = [
      { label: "Estimasi Tagihan Serverless", value: formatIDR(serverlessIdr) + "/bln", sub: formatNum(gbSeconds, 0) + " GB-seconds" },
      { label: "Biaya Cluster VPS Dedikasi", value: formatIDR(vpsIdr) + "/bln", sub: "Biaya Tetap (Flat-Rate)" },
      { label: "Selisih Efisiensi Bulanan", value: formatIDR(Math.abs(diffIdr)), sub: serverlessIdr < vpsIdr ? "Serverless Lebih Hemat" : "VPS Lebih Hemat" },
      { label: "Rekomendasi Arsitektur", value: serverlessIdr <= vpsIdr ? "Gunakan Serverless" : "Migrasi ke VPS", sub: "Berdasarkan beban " + reqMillions + "M req/bln" }
    ];
    healthPct = serverlessIdr <= vpsIdr ? 88 : 65;
    insight = serverlessIdr <= vpsIdr
      ? `Pada volume ${reqMillions} juta request/bulan (${durationMs}ms), arsitektur Serverless (${formatIDR(serverlessIdr)}) masih lebih hemat ${formatIDR(Math.abs(diffIdr))} dibanding menyewa cluster VPS.`
      : `Volume trafik Anda sudah melewati titik impas (break-even). Memindahkan beban kerja ke cluster VPS (${formatIDR(vpsIdr)}/bln) menghemat ${formatIDR(Math.abs(diffIdr))} setiap bulan.`;
  }
  else if (formulaId === "canvas_calc") {
    const wCm = getVal("width_cm");
    const hCm = getVal("height_cm");
    const dpi = getVal("dpi");
    const nodes = getVal("svg_nodes");

    const wPx = Math.round((wCm / 2.54) * dpi);
    const hPx = Math.round((hCm / 2.54) * dpi);
    const megapixels = (wPx * hPx) / 1000000;
    const rawRgbaMb = (wPx * hPx * 4) / (1024 * 1024);
    const svgKb = Math.max(2, (nodes * 48) / 1024);

    cards = [
      { label: "Resolusi Piksel Eksak", value: formatNum(wPx, 0) + " × " + formatNum(hPx, 0) + " px", sub: "Total: " + formatNum(megapixels, 2) + " MP @ " + dpi + " DPI" },
      { label: "Memori Kanvas Raster (RGBA)", value: formatNum(rawRgbaMb, 1) + " MB", sub: "Ukuran Bitmap Tak Terkompresi" },
      { label: "Estimasi Ukuran Vektor SVG", value: formatNum(svgKb, 1) + " KB", sub: nodes + " Kurva Bézier / Path" },
      { label: "Rasio Efisiensi Vektor", value: formatNum((rawRgbaMb * 1024) / svgKb, 0) + "x Lebih Ringan", sub: "Tajam Tanpa Batas Resolusi" }
    ];
    healthPct = 92;
    insight = `Bidang ${wCm}×${hCm} cm pada ${dpi} DPI membutuhkan kanvas raster ${formatNum(wPx, 0)}×${formatNum(hPx, 0)} piksel (${formatNum(rawRgbaMb, 1)} MB RAM). Dengan konversi vektor SVG (${nodes} node), ukuran file turun drastis menjadi ~${formatNum(svgKb, 1)} KB.`;
  }
  else if (formulaId === "llm_calc") {
    const daily = getVal("daily_prompts");
    const inWords = getVal("avg_input_words");
    const outWords = getVal("avg_output_words");
    const usdRate = getVal("usd_rate");

    const monthlyPrompts = daily * 30;
    const inTokensM = (monthlyPrompts * inWords * 1.35) / 1000000;
    const outTokensM = (monthlyPrompts * outWords * 1.35) / 1000000;

    // Flash Tier (~$0.15/1M in, $0.60/1M out) vs Flagship Pro Tier (~$2.50/1M in, $10.00/1M out)
    const flashCostIdr = ((inTokensM * 0.15) + (outTokensM * 0.60)) * usdRate;
    const proCostIdr = ((inTokensM * 2.50) + (outTokensM * 10.00)) * usdRate;
    const hybridCostIdr = (flashCostIdr * 0.85) + (proCostIdr * 0.15);

    cards = [
      { label: "Volume Token Bulanan", value: formatNum(inTokensM + outTokensM, 2) + " Juta Token", sub: "In: " + formatNum(inTokensM, 1) + "M | Out: " + formatNum(outTokensM, 1) + "M" },
      { label: "Biaya Model Tier Flash", value: formatIDR(flashCostIdr) + "/bln", sub: "Eksekusi Cepat & Massal" },
      { label: "Biaya Model Tier Flagship", value: formatIDR(proCostIdr) + "/bln", sub: "Deep Reasoning Penuh" },
      { label: "Biaya Multi-Model Routing (85/15)", value: formatIDR(hybridCostIdr) + "/bln", sub: "Hemat " + formatIDR(proCostIdr - hybridCostIdr) + "/bln" }
    ];
    healthPct = 90;
    insight = `Dengan merutekan 85% tugas rutin ke model kelas Flash dan 15% tugas arsitektur kompleks ke model Flagship, biaya API bulanan Anda hanya ${formatIDR(hybridCostIdr)} (hemat ${formatIDR(proCostIdr - hybridCostIdr)} dibanding memakai model Flagship terus-menerus).`;
  }
  else if (formulaId === "agency_calc") {
    const screens = getVal("screens_count");
    const apis = getVal("api_integrations");
    const rate = getVal("hourly_rate");
    const urgency = getVal("urgency_factor");

    const uiHours = screens * 10;
    const apiHours = apis * 18;
    const qaPmHours = Math.round((uiHours + apiHours) * 0.25);
    const totalHours = uiHours + apiHours + qaPmHours;
    const estWeeks = Math.max(2, Math.ceil((totalHours / 35) / urgency));
    const totalCost = totalHours * rate * urgency;

    cards = [
      { label: "Estimasi Investasi Proyek", value: formatIDR(totalCost), sub: "Termasuk QA, Deployment & Dokumentasi" },
      { label: "Total Beban Kerja Engineering", value: formatNum(totalHours, 0) + " Jam Kerja", sub: "UI/FE: " + uiHours + "j | Backend/API: " + apiHours + "j" },
      { label: "Estimasi Durasi Pengerjaan", value: estWeeks + " Minggu", sub: "Faktor Akselerasi: " + urgency + "x" },
      { label: "Termin Pembayaran Awal (DP 40%)", value: formatIDR(totalCost * 0.4), sub: "Pelunasan Bertahap per Milestone" }
    ];
    healthPct = 85;
    insight = `Proyek dengan ${screens} modul antarmuka dan ${apis} integrasi eksternal membutuhkan sekitar ${totalHours} jam kerja engineering (~${estWeeks} minggu) dengan nilai kontrak ${formatIDR(totalCost)}.`;
  }

  const gridEl = document.getElementById("tool_results_grid");
  if (gridEl) {
    gridEl.innerHTML = cards.map(c => `
      <div class="result-card">
        <div class="result-label">${c.label}</div>
        <div class="result-value">${c.value}</div>
        <div class="result-sub">${c.sub}</div>
      </div>
    `).join("");
  }

  const insightEl = document.getElementById("tool_insight_box");
  if (insightEl) {
    insightEl.innerHTML = `
      <div class="insight-header">
        <span>Analisis Otomatis & Rekomendasi Eksekusi</span>
        <span class="insight-score">Skor Efisiensi: ${Math.round(healthPct)}/100</span>
      </div>
      <div class="progress-track">
        <div class="progress-fill" style="width: ${Math.min(100, Math.max(10, Math.round(healthPct)))}%"></div>
      </div>
      <p class="insight-text">${insight}</p>
    `;
  }
}

function openAcquireModal() {
  const m = document.getElementById("acquire_modal");
  if (m) m.classList.add("active");
}

function closeAcquireModal() {
  const m = document.getElementById("acquire_modal");
  if (m) m.classList.remove("active");
}

function sendAcquisitionOffer(domainName, defaultPrice, waNumber, emailAddr, via) {
  const buyerName = (document.getElementById("offer_name")?.value || "Calon Pembeli").trim();
  const buyerOrg = (document.getElementById("offer_org")?.value || "Perusahaan / Individu").trim();
  const offerAmount = (document.getElementById("offer_price")?.value || defaultPrice).trim();
  const notes = (document.getElementById("offer_notes")?.value || "Tertarik mengakuisisi hak kepemilikan domain beserta aplikasi micro-tool di dalamnya.").trim();

  const msg = `Halo Kak Diko, saya ${buyerName} (${buyerOrg}). Saya mengajukan penawaran akuisisi untuk domain *${domainName}* dengan nominal *Rp ${Number(offerAmount).toLocaleString("id-ID")}*. Catatan: ${notes}`;

  if (via === "wa") {
    window.open(`https://wa.me/${waNumber}?text=${encodeURIComponent(msg)}`, "_blank", "noopener");
  } else {
    const subj = `Penawaran Akuisisi Domain ${domainName} - ${buyerName}`;
    window.location.href = `mailto:${emailAddr}?subject=${encodeURIComponent(subj)}&body=${encodeURIComponent(msg)}`;
  }
}
"""


def build_domain_page(domain_cfg: dict, all_domains: list, owner: dict) -> str:
    domain = domain_cfg["domain"]
    brand = domain_cfg["brand_name"]
    tagline = domain_cfg["tagline"]
    desc = domain_cfg["description"]
    theme = domain_cfg["theme"]
    acq = domain_cfg["acquisition"]
    tool = domain_cfg["tool"]
    for_sale = domain_cfg["for_sale"]
    bundle_list = acq.get("bundle_domains", [domain])

    svg_logo = generate_svg_logo(theme["icon_type"], theme["primary"], theme["accent"], brand)

    # Build Inputs HTML
    inputs_html = ""
    for inp in tool["inputs"]:
        inputs_html += f"""
        <div class="input-group">
          <label for="input_{inp['id']}">{inp['label']}</label>
          <input
            type="{inp['type']}"
            id="input_{inp['id']}"
            value="{inp['default']}"
            min="{inp['min']}"
            max="{inp['max']}"
            step="{inp['step']}"
            oninput="runMicroTool('{tool['formula_id']}')"
          />
        </div>
        """

    # Bundle Banner HTML if multi-domain bundle
    bundle_html = ""
    if len(bundle_list) > 1:
        badges = "".join(
            f'<a href="../{b}/" class="bundle-pill {"active-pill" if b == domain else ""}">{b}</a>'
            for b in bundle_list
        )
        bundle_html = f"""
        <div class="bundle-card">
          <div class="bundle-info">
            <span class="bundle-tag">DEFENSIVE BRAND BUNDLE ({len(bundle_list)} DOMAIN)</span>
            <h3>Proteksi Merek Penuh: Akuisisi Seluruh Ekstensi Sekaligus</h3>
            <p>{acq['scarcity_note']}</p>
            <div class="bundle-pills">{badges}</div>
          </div>
          <div class="bundle-cta">
            <div class="bundle-price">{acq['price_label']}</div>
            <button type="button" class="btn-primary" onclick="openAcquireModal()">Amankan Paket {len(bundle_list)} Domain</button>
          </div>
        </div>
        """

    # Special 13-Domain Portfolio Showcase Table for kakdiko.web.id
    empire_catalog_html = ""
    if domain == "kakdiko.web.id":
        rows = ""
        for d in all_domains:
            rows += f"""
            <tr>
              <td><a href="../{d['domain']}/" class="domain-link"><strong>{d['domain']}</strong></a></td>
              <td>{d['brand_name']}</td>
              <td><span class="cat-tag">{d['category']}</span></td>
              <td>{d['tool']['title']}</td>
              <td>{status_sale_or_core(d)}</td>
            </tr>
            """
        empire_catalog_html = f"""
        <section class="section" id="katalog-13-domain">
          <div class="section-header">
            <span class="eyebrow">PORTFOLIO JARINGAN ASET DIGITAL</span>
            <h2>Katalog 13 Domain Aktif & Micro-SaaS Ekosistem KakDiko</h2>
            <p>Seluruh properti digital di bawah ini dikelola secara terpusat melalui arsitektur AI-Driven Static Monorepo dan dilengkapi utilitas interaktif mandiri.</p>
          </div>
          <div class="table-wrap">
            <table class="empire-table">
              <thead>
                <tr>
                  <th>Domain</th>
                  <th>Nama Properti</th>
                  <th>Kategori</th>
                  <th>Micro-Tool Interaktif</th>
                  <th>Status & Valuasi Akuisisi</th>
                </tr>
              </thead>
              <tbody>
                {rows}
              </tbody>
            </table>
          </div>
        </section>
        """

    # Features HTML
    features_html = "".join(
        f"""
        <div class="feature-card">
          <div class="feature-dot"></div>
          <h3>{f['title']}</h3>
          <p>{f['desc']}</p>
        </div>
        """
        for f in domain_cfg["features"]
    )

    # Articles HTML
    articles_html = "".join(
        f"""
        <article class="article-card" id="{art['slug']}">
          <div class="article-meta">
            <span class="article-tag">{domain_cfg['category']}</span>
            <span class="article-time">⏱ {art['read_time']} baca</span>
          </div>
          <h3>{art['title']}</h3>
          <p>{art['summary']}</p>
          <div class="article-footer">
            <span>Terverifikasi Tim Riset {brand}</span>
            <a href="#micro-tool" class="article-cta">Coba Simulator →</a>
          </div>
        </article>
        """
        for art in domain_cfg["articles"]
    )

    # Sister domains footer links
    sister_links = "".join(
        f'<a href="../{d["domain"]}/" title="{d["brand_name"]}">{d["domain"]}</a>'
        for d in all_domains
    )

    # Top Acquisition Banner
    if for_sale:
        top_bar_html = f"""
        <div class="acq-topbar">
          <div class="acq-topbar-inner">
            <div class="acq-topbar-left">
              <span class="pulse-dot"></span>
              <strong>ASET DOMAIN PREMIUM DIJUAL:</strong>
              <span><code>{domain}</code> — {acq['price_label']}</span>
            </div>
            <div class="acq-topbar-right">
              <button type="button" class="btn-topbar" onclick="openAcquireModal()">Ajukan Penawaran / Akuisisi →</button>
            </div>
          </div>
        </div>
        """
    else:
        top_bar_html = f"""
        <div class="acq-topbar hub-bar">
          <div class="acq-topbar-inner">
            <div class="acq-topbar-left">
              <span class="pulse-dot"></span>
              <strong>PUSAT KOMANDO EKOSISTEM 13 DOMAIN:</strong>
              <span><code>{domain}</code> — Arsitektur AI-Driven Static Monorepo Aktif</span>
            </div>
            <div class="acq-topbar-right">
              <a href="#katalog-13-domain" class="btn-topbar">Lihat 13 Properti Digital →</a>
            </div>
          </div>
        </div>
        """

    # Schema.org JSON-LD
    schema_ld = {
        "@context": "https://schema.org",
        "@type": "WebApplication",
        "name": f"{brand} ({domain})",
        "url": f"https://{domain}/",
        "description": desc,
        "applicationCategory": "FinanceApplication" if "Financial" in domain_cfg["category"] else "BusinessApplication",
        "operatingSystem": "Web",
        "author": {
            "@type": "Person",
            "name": owner["name"],
            "url": f"https://{owner['primary_domain']}/"
        }
    }
    if for_sale:
        schema_ld["offers"] = {
            "@type": "Offer",
            "price": str(acq["price_idr"]),
            "priceCurrency": "IDR",
            "availability": "https://schema.org/InStock",
            "description": acq["price_label"]
        }

    default_price = acq["price_idr"] if acq["price_idr"] > 0 else 3500000

    return f"""<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{brand} — {tagline} | {domain}</title>
  <meta name="description" content="{desc}" />
  <link rel="canonical" href="https://{domain}/" />
  <meta property="og:title" content="{brand} — {tagline}" />
  <meta property="og:description" content="{desc}" />
  <meta property="og:url" content="https://{domain}/" />
  <meta property="og:type" content="website" />
  <meta name="theme-color" content="{theme['primary']}" />
  <script type="application/ld+json">{json.dumps(schema_ld, ensure_ascii=False)}</script>
  <style>
    :root {{
      --primary: {theme['primary']};
      --secondary: {theme['secondary']};
      --accent: {theme['accent']};
      --bg-dark: {theme['bg_dark']};
      --surface: #0f172a;
      --surface-2: #1e293b;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --border: rgba(148, 163, 184, 0.18);
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Inter, sans-serif;
      background: radial-gradient(circle at 15% 0%, rgba(255,255,255,0.05), transparent 45%), var(--bg-dark);
      color: var(--text-main);
      line-height: 1.65;
      min-height: 100vh;
    }}
    a {{ color: var(--accent); text-decoration: none; transition: opacity 0.2s; }}
    a:hover {{ opacity: 0.85; }}

    /* Top Acquisition Bar */
    .acq-topbar {{
      background: linear-gradient(90deg, var(--secondary), var(--primary));
      color: #020617;
      padding: 0.55rem 1.25rem;
      font-size: 0.88rem;
      position: sticky;
      top: 0;
      z-index: 100;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
    }}
    .acq-topbar-inner {{
      max-width: 1180px;
      margin: 0 auto;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
      flex-wrap: wrap;
    }}
    .acq-topbar-left {{
      display: flex;
      align-items: center;
      gap: 0.55rem;
      flex-wrap: wrap;
      font-weight: 500;
    }}
    .acq-topbar-left code {{
      background: rgba(2, 6, 23, 0.15);
      padding: 0.1rem 0.45rem;
      border-radius: 5px;
      font-weight: 700;
    }}
    .pulse-dot {{
      width: 9px;
      height: 9px;
      border-radius: 50%;
      background: #020617;
      display: inline-block;
    }}
    .btn-topbar {{
      background: #020617;
      color: #f8fafc !important;
      border: none;
      padding: 0.38rem 0.9rem;
      border-radius: 999px;
      font-weight: 600;
      font-size: 0.82rem;
      cursor: pointer;
    }}

    /* Header Navbar */
    .navbar {{
      max-width: 1180px;
      margin: 0 auto;
      padding: 1.25rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-bottom: 1px solid var(--border);
      flex-wrap: wrap;
      gap: 1rem;
    }}
    .brand-box {{
      display: flex;
      align-items: center;
      gap: 0.85rem;
    }}
    .brand-title {{
      font-size: 1.15rem;
      font-weight: 800;
      letter-spacing: -0.02em;
      color: var(--text-main);
    }}
    .brand-domain {{
      font-size: 0.78rem;
      color: var(--accent);
      font-family: monospace;
    }}
    .nav-links {{
      display: flex;
      align-items: center;
      gap: 1.25rem;
      font-size: 0.92rem;
    }}
    .nav-links a {{ color: var(--text-muted); font-weight: 500; }}
    .nav-links a:hover {{ color: var(--text-main); }}

    /* Container & Sections */
    .container {{
      max-width: 1180px;
      margin: 0 auto;
      padding: 0 1.25rem;
    }}
    .hero {{
      padding: 3.8rem 0 2.8rem;
      display: grid;
      grid-template-columns: 1.25fr 0.75fr;
      gap: 2.5rem;
      align-items: center;
    }}
    @media (max-width: 860px) {{
      .hero {{ grid-template-columns: 1fr; padding: 2.5rem 0 1.8rem; }}
    }}
    .badge-row {{
      display: flex;
      gap: 0.6rem;
      flex-wrap: wrap;
      margin-bottom: 1rem;
    }}
    .badge {{
      font-size: 0.75rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      padding: 0.28rem 0.75rem;
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.06);
      border: 1px solid var(--border);
      color: var(--accent);
    }}
    .hero h1 {{
      font-size: clamp(2rem, 4vw, 3.1rem);
      line-height: 1.15;
      font-weight: 800;
      letter-spacing: -0.03em;
      margin-bottom: 1.1rem;
    }}
    .hero p {{
      font-size: 1.08rem;
      color: var(--text-muted);
      margin-bottom: 1.75rem;
      max-width: 640px;
    }}
    .cta-row {{
      display: flex;
      gap: 0.9rem;
      flex-wrap: wrap;
    }}
    .btn-primary {{
      background: linear-gradient(135deg, var(--primary), var(--secondary));
      color: #020617;
      font-weight: 700;
      padding: 0.8rem 1.45rem;
      border-radius: 10px;
      border: none;
      cursor: pointer;
      font-size: 0.95rem;
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
    }}
    .btn-outline {{
      background: rgba(255, 255, 255, 0.04);
      color: var(--text-main);
      border: 1px solid var(--border);
      font-weight: 600;
      padding: 0.8rem 1.35rem;
      border-radius: 10px;
      cursor: pointer;
      font-size: 0.95rem;
    }}
    .hero-card {{
      background: rgba(15, 23, 42, 0.82);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 1.6rem;
      box-shadow: 0 20px 45px rgba(0, 0, 0, 0.35);
    }}
    .hero-card h3 {{
      font-size: 1rem;
      margin-bottom: 0.65rem;
      color: var(--accent);
    }}
    .meta-list {{
      list-style: none;
      font-size: 0.9rem;
    }}
    .meta-list li {{
      display: flex;
      justify-content: space-between;
      padding: 0.55rem 0;
      border-bottom: 1px solid var(--border);
    }}
    .meta-list li:last-child {{ border-bottom: none; }}
    .meta-key {{ color: var(--text-muted); }}
    .meta-val {{ font-weight: 700; color: var(--text-main); text-align: right; }}

    /* Micro-Tool Workspace */
    .tool-section {{
      background: linear-gradient(180deg, rgba(30, 41, 59, 0.72), rgba(15, 23, 42, 0.92));
      border: 1px solid var(--primary);
      border-radius: 20px;
      padding: 2.2rem;
      margin: 1.5rem 0 3rem;
      box-shadow: 0 24px 60px rgba(0, 0, 0, 0.45);
    }}
    .tool-header {{
      margin-bottom: 1.75rem;
    }}
    .eyebrow {{
      font-size: 0.76rem;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--accent);
      display: block;
      margin-bottom: 0.35rem;
    }}
    .tool-header h2 {{
      font-size: 1.65rem;
      font-weight: 800;
      margin-bottom: 0.4rem;
    }}
    .tool-header p {{ color: var(--text-muted); font-size: 0.96rem; }}

    .tool-grid {{
      display: grid;
      grid-template-columns: 1fr 1.35fr;
      gap: 2rem;
      align-items: start;
    }}
    @media (max-width: 900px) {{
      .tool-grid {{ grid-template-columns: 1fr; }}
    }}
    .inputs-panel {{
      background: rgba(2, 6, 23, 0.55);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 1.4rem;
    }}
    .input-group {{ margin-bottom: 1.1rem; }}
    .input-group:last-child {{ margin-bottom: 0; }}
    .input-group label {{
      display: block;
      font-size: 0.85rem;
      font-weight: 600;
      color: var(--text-muted);
      margin-bottom: 0.4rem;
    }}
    .input-group input {{
      width: 100%;
      padding: 0.7rem 0.9rem;
      background: #0f172a;
      border: 1px solid var(--border);
      border-radius: 8px;
      color: var(--text-main);
      font-size: 1rem;
      font-weight: 600;
    }}
    .input-group input:focus {{
      outline: none;
      border-color: var(--primary);
      box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.15);
    }}

    .results-grid {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 1rem;
      margin-bottom: 1.25rem;
    }}
    @media (max-width: 560px) {{
      .results-grid {{ grid-template-columns: 1fr; }}
    }}
    .result-card {{
      background: rgba(2, 6, 23, 0.65);
      border: 1px solid var(--border);
      border-left: 4px solid var(--primary);
      border-radius: 12px;
      padding: 1.1rem 1.2rem;
    }}
    .result-label {{
      font-size: 0.8rem;
      color: var(--text-muted);
      font-weight: 600;
      margin-bottom: 0.3rem;
    }}
    .result-value {{
      font-size: 1.38rem;
      font-weight: 800;
      color: var(--text-main);
      margin-bottom: 0.2rem;
    }}
    .result-sub {{
      font-size: 0.78rem;
      color: var(--accent);
    }}

    .insight-box {{
      background: rgba(2, 6, 23, 0.75);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1.2rem;
    }}
    .insight-header {{
      display: flex;
      justify-content: space-between;
      font-size: 0.85rem;
      font-weight: 700;
      margin-bottom: 0.55rem;
      color: var(--accent);
    }}
    .progress-track {{
      width: 100%;
      height: 8px;
      background: rgba(255, 255, 255, 0.08);
      border-radius: 999px;
      overflow: hidden;
      margin-bottom: 0.75rem;
    }}
    .progress-fill {{
      height: 100%;
      background: linear-gradient(90deg, var(--primary), var(--accent));
      border-radius: 999px;
      transition: width 0.3s ease;
    }}
    .insight-text {{
      font-size: 0.92rem;
      color: var(--text-main);
    }}

    /* Bundle Card */
    .bundle-card {{
      background: linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(30, 41, 59, 0.85));
      border: 1px solid var(--accent);
      border-radius: 16px;
      padding: 1.8rem;
      margin: 2.5rem 0;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1.5rem;
      flex-wrap: wrap;
    }}
    .bundle-tag {{
      font-size: 0.74rem;
      font-weight: 800;
      color: #020617;
      background: var(--accent);
      padding: 0.2rem 0.65rem;
      border-radius: 999px;
      display: inline-block;
      margin-bottom: 0.5rem;
    }}
    .bundle-info h3 {{ font-size: 1.3rem; margin-bottom: 0.35rem; }}
    .bundle-info p {{ color: var(--text-muted); font-size: 0.92rem; max-width: 680px; margin-bottom: 0.9rem; }}
    .bundle-pills {{ display: flex; gap: 0.6rem; flex-wrap: wrap; }}
    .bundle-pill {{
      padding: 0.35rem 0.85rem;
      border-radius: 8px;
      background: rgba(255, 255, 255, 0.06);
      border: 1px solid var(--border);
      font-family: monospace;
      font-size: 0.88rem;
      color: var(--text-main);
    }}
    .bundle-pill.active-pill {{
      border-color: var(--primary);
      background: rgba(56, 189, 248, 0.15);
      color: var(--accent);
      font-weight: 700;
    }}
    .bundle-price {{
      font-size: 1.05rem;
      font-weight: 800;
      color: var(--accent);
      margin-bottom: 0.6rem;
      text-align: right;
    }}

    /* Features & Articles */
    .section {{ padding: 2.5rem 0; }}
    .section-header {{ margin-bottom: 1.8rem; }}
    .section-header h2 {{ font-size: 1.75rem; font-weight: 800; margin-bottom: 0.4rem; }}
    .section-header p {{ color: var(--text-muted); }}

    .features-grid, .articles-grid {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 1.35rem;
    }}
    @media (max-width: 860px) {{
      .features-grid, .articles-grid {{ grid-template-columns: 1fr; }}
    }}
    .feature-card, .article-card {{
      background: rgba(15, 23, 42, 0.78);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 1.5rem;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }}
    .feature-dot {{
      width: 12px;
      height: 12px;
      border-radius: 4px;
      background: var(--primary);
      margin-bottom: 0.9rem;
    }}
    .feature-card h3, .article-card h3 {{
      font-size: 1.12rem;
      margin-bottom: 0.6rem;
      line-height: 1.35;
    }}
    .feature-card p, .article-card p {{
      color: var(--text-muted);
      font-size: 0.92rem;
    }}
    .article-meta {{
      display: flex;
      justify-content: space-between;
      font-size: 0.76rem;
      color: var(--accent);
      margin-bottom: 0.65rem;
      font-weight: 600;
    }}
    .article-footer {{
      margin-top: 1.2rem;
      padding-top: 0.85rem;
      border-top: 1px solid var(--border);
      display: flex;
      justify-content: space-between;
      font-size: 0.8rem;
      color: var(--text-muted);
    }}

    /* Empire Table on kakdiko.web.id */
    .table-wrap {{
      overflow-x: auto;
      background: rgba(15, 23, 42, 0.85);
      border: 1px solid var(--border);
      border-radius: 14px;
    }}
    .empire-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.9rem;
    }}
    .empire-table th, .empire-table td {{
      padding: 0.9rem 1.1rem;
      text-align: left;
      border-bottom: 1px solid var(--border);
    }}
    .empire-table th {{
      background: rgba(2, 6, 23, 0.6);
      color: var(--accent);
      font-size: 0.78rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}
    .cat-tag {{
      font-size: 0.75rem;
      padding: 0.2rem 0.55rem;
      border-radius: 6px;
      background: rgba(255, 255, 255, 0.06);
    }}
    .status-pill {{
      font-size: 0.78rem;
      font-weight: 700;
      padding: 0.25rem 0.65rem;
      border-radius: 999px;
      display: inline-block;
    }}
    .status-pill.sale {{ background: rgba(16, 185, 129, 0.18); color: #34d399; }}
    .status-pill.core {{ background: rgba(56, 189, 248, 0.18); color: #38bdf8; }}

    /* Footer */
    .footer {{
      margin-top: 4rem;
      border-top: 1px solid var(--border);
      padding: 2.5rem 0;
      background: rgba(2, 6, 23, 0.7);
      font-size: 0.88rem;
      color: var(--text-muted);
    }}
    .sister-grid {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.65rem;
      margin: 1rem 0 1.5rem;
    }}
    .sister-grid a {{
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid var(--border);
      padding: 0.3rem 0.7rem;
      border-radius: 6px;
      font-family: monospace;
      font-size: 0.8rem;
      color: var(--text-muted);
    }}
    .sister-grid a:hover {{
      color: var(--accent);
      border-color: var(--accent);
    }}

    /* Modal */
    .modal-backdrop {{
      position: fixed;
      inset: 0;
      background: rgba(2, 6, 23, 0.82);
      backdrop-filter: blur(6px);
      display: none;
      align-items: center;
      justify-content: center;
      z-index: 999;
      padding: 1rem;
    }}
    .modal-backdrop.active {{ display: flex; }}
    .modal-card {{
      background: #0f172a;
      border: 1px solid var(--primary);
      border-radius: 18px;
      max-width: 520px;
      width: 100%;
      padding: 1.8rem;
      box-shadow: 0 25px 70px rgba(0, 0, 0, 0.65);
    }}
    .modal-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1rem;
    }}
    .modal-close {{
      background: transparent;
      border: none;
      color: var(--text-muted);
      font-size: 1.4rem;
      cursor: pointer;
    }}
  </style>
</head>
<body>
  {top_bar_html}

  <header class="navbar">
    <a href="./" class="brand-box">
      {svg_logo}
      <div>
        <div class="brand-title">{brand}</div>
        <div class="brand-domain">{domain}</div>
      </div>
    </a>
    <nav class="nav-links">
      <a href="#micro-tool">Simulator Interaktif</a>
      <a href="#riset-pilar">Riset & Panduan</a>
      <a href="../kakdiko.web.id/">Ekosistem 13 Domain</a>
      <a href="../" title="Empire Command Center">Command Center</a>
    </nav>
  </header>

  <main class="container">
    <section class="hero">
      <div>
        <div class="badge-row">
          <span class="badge">{domain_cfg['tier']}</span>
          <span class="badge">{domain_cfg['category']}</span>
          <span class="badge">RDAP Verified</span>
        </div>
        <h1>{tagline}</h1>
        <p>{desc}</p>
        <div class="cta-row">
          <a href="#micro-tool" class="btn-primary">Buka {tool['title']} ↓</a>
          <button type="button" class="btn-outline" onclick="openAcquireModal()">
            {"Ajukan Akuisisi Domain" if for_sale else "Hubungi Kak Diko"}
          </button>
        </div>
      </div>

      <aside class="hero-card">
        <h3>Spesifikasi Properti Digital</h3>
        <ul class="meta-list">
          <li><span class="meta-key">Nama Domain</span><span class="meta-val"><code>{domain}</code></span></li>
          <li><span class="meta-key">Klasifikasi Aset</span><span class="meta-val">{domain_cfg['tier']}</span></li>
          <li><span class="meta-key">Status Akuisisi</span><span class="meta-val">{acq['status']}</span></li>
          <li><span class="meta-key">Valuasi / Harga</span><span class="meta-val">{acq['price_label']}</span></li>
          <li><span class="meta-key">Mesin Aplikasi</span><span class="meta-val">Client-Side ES6 + JSON-LD</span></li>
        </ul>
      </aside>
    </section>

    <section class="tool-section" id="micro-tool">
      <div class="tool-header">
        <span class="eyebrow">INTERACTIVE MICRO-TOOL • {domain.upper()}</span>
        <h2>{tool['title']}</h2>
        <p>{tool['subtitle']}</p>
      </div>

      <div class="tool-grid">
        <div class="inputs-panel">
          {inputs_html}
        </div>
        <div>
          <div class="results-grid" id="tool_results_grid"></div>
          <div class="insight-box" id="tool_insight_box"></div>
        </div>
      </div>
    </section>

    {bundle_html}

    {empire_catalog_html}

    <section class="section">
      <div class="section-header">
        <span class="eyebrow">KEUNGGULAN ARSITEKTUR & NILAI ASET</span>
        <h2>Mengapa {brand} ({domain}) Bernilai Strategis?</h2>
        <p>Dirancang dengan standar produksi tinggi untuk konversi organik, kecepatan ekstrem, dan otoritas merek.</p>
      </div>
      <div class="features-grid">
        {features_html}
      </div>
    </section>

    <section class="section" id="riset-pilar">
      <div class="section-header">
        <span class="eyebrow">PUSTAKA RISET & ARTIKEL PILAR SEO</span>
        <h2>Panduan & Analisis Mendalam {brand}</h2>
        <p>Referensi terstruktur untuk mendukung pengambilan keputusan finansial, teknis, dan bisnis Anda.</p>
      </div>
      <div class="articles-grid">
        {articles_html}
      </div>
    </section>
  </main>

  <footer class="footer">
    <div class="container">
      <strong>Jaringan 13 Properti Digital KakDiko Monorepo:</strong>
      <div class="sister-grid">
        {sister_links}
      </div>
      <p>© {datetime.now().year} <strong>{brand} ({domain})</strong> — Dikelola oleh <a href="../kakdiko.web.id/">{owner['name']}</a> (<a href="mailto:{owner['email']}">{owner['email']}</a> | WA: <a href="https://wa.me/{owner['whatsapp']}">+{owner['whatsapp']}</a>) menggunakan Arsitektur AI-Driven Static Monorepo.</p>
    </div>
  </footer>

  <!-- Modal Akuisisi Domain / Kemitraan -->
  <div class="modal-backdrop" id="acquire_modal">
    <div class="modal-card">
      <div class="modal-header">
        <h3>{"Formulir Penawaran Akuisisi Domain" if for_sale else "Hubungi Kak Diko — Kolaborasi & Akuisisi"}</h3>
        <button type="button" class="modal-close" onclick="closeAcquireModal()">×</button>
      </div>
      <p style="color: var(--text-muted); font-size: 0.88rem; margin-bottom: 1rem;">
        {acq['scarcity_note']}
      </p>
      <div class="input-group">
        <label for="offer_name">Nama Lengkap Anda</label>
        <input type="text" id="offer_name" placeholder="Contoh: Budi Santoso" />
      </div>
      <div class="input-group">
        <label for="offer_org">Perusahaan / Instansi</label>
        <input type="text" id="offer_org" placeholder="Contoh: PT Nusantara Kapital" />
      </div>
      <div class="input-group">
        <label for="offer_price">Nominal Penawaran Akuisisi (Rp)</label>
        <input type="number" id="offer_price" value="{default_price}" step="250000" />
      </div>
      <div class="input-group">
        <label for="offer_notes">Pesan / Rencana Penggunaan</label>
        <input type="text" id="offer_notes" value="Saya tertarik mengakuisisi {domain} beserta kode micro-tool di dalamnya." />
      </div>
      <div class="cta-row" style="margin-top: 1.25rem;">
        <button type="button" class="btn-primary" onclick="sendAcquisitionOffer('{domain}', '{default_price}', '{owner['whatsapp']}', '{owner['email']}', 'wa')">
          Kirim via WhatsApp
        </button>
        <button type="button" class="btn-outline" onclick="sendAcquisitionOffer('{domain}', '{default_price}', '{owner['whatsapp']}', '{owner['email']}', 'email')">
          Kirim via Email
        </button>
      </div>
    </div>
  </div>

  <script>
    {JS_FORMULA_ENGINE}
    document.addEventListener("DOMContentLoaded", function() {{
      runMicroTool("{tool['formula_id']}");
    }});
  </script>
</body>
</html>
"""


def status_sale_or_core(d: dict) -> str:
    if not d["for_sale"]:
        return '<span class="status-pill core">Aset Inti (Non-Resale)</span>'
    return f'<span class="status-pill sale">{d["acquisition"]["price_label"]}</span>'


def build_command_center(manifest: dict) -> str:
    domains = manifest["domains"]
    owner = manifest["owner"]

    # Calculate unique bundle valuation (avoiding triple-counting ekuitas and double-counting kodelab)
    seen_bundles = set()
    total_valuation = 0
    for d in domains:
        if d["for_sale"]:
            b_key = tuple(sorted(d["acquisition"]["bundle_domains"]))
            if b_key not in seen_bundles:
                seen_bundles.add(b_key)
                total_valuation += d["acquisition"]["price_idr"]

    cards_html = ""
    for idx, d in enumerate(domains, start=1):
        theme = d["theme"]
        svg_logo = generate_svg_logo(theme["icon_type"], theme["primary"], theme["accent"], d["brand_name"])
        cards_html += f"""
        <div class="cc-card" style="border-top: 4px solid {theme['primary']}">
          <div class="cc-card-top">
            <div class="cc-logo-wrap">
              {svg_logo}
              <div>
                <span class="cc-index">#{idx:02d} • {d['tier']}</span>
                <h3><a href="./{d['domain']}/">{d['domain']}</a></h3>
              </div>
            </div>
            <span class="cc-cat">{d['category']}</span>
          </div>
          <p class="cc-brand">{d['brand_name']} — {d['tagline']}</p>
          <div class="cc-tool-box">
            <strong>🛠 Micro-Tool:</strong> {d['tool']['title']}
          </div>
          <div class="cc-footer">
            <span class="cc-price">{d['acquisition']['price_label']}</span>
            <a href="./{d['domain']}/" class="cc-btn">Buka Situs →</a>
          </div>
        </div>
        """

    return f"""<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Empire Command Center — 13-Domain AI-Driven Static Monorepo</title>
  <style>
    :root {{
      --bg: #050811;
      --card: #0f172a;
      --border: rgba(148, 163, 184, 0.18);
      --text: #f8fafc;
      --muted: #94a3b8;
      --accent: #38bdf8;
      --green: #10b981;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Inter, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.6;
      padding-bottom: 4rem;
    }}
    .header {{
      background: linear-gradient(180deg, #0f172a, #050811);
      border-bottom: 1px solid var(--border);
      padding: 2.5rem 1.25rem;
    }}
    .container {{ max-width: 1240px; margin: 0 auto; padding: 0 1.25rem; }}
    .eyebrow {{
      color: var(--accent);
      font-size: 0.78rem;
      font-weight: 800;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }}
    h1 {{ font-size: clamp(1.8rem, 3.5vw, 2.6rem); margin: 0.4rem 0 0.75rem; font-weight: 800; }}
    .stats-bar {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 1rem;
      margin-top: 1.8rem;
    }}
    @media (max-width: 800px) {{ .stats-bar {{ grid-template-columns: repeat(2, 1fr); }} }}
    .stat-box {{
      background: rgba(30, 41, 59, 0.55);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1.1rem;
    }}
    .stat-label {{ font-size: 0.78rem; color: var(--muted); font-weight: 600; }}
    .stat-val {{ font-size: 1.45rem; font-weight: 800; color: var(--text); margin-top: 0.2rem; }}
    .stat-sub {{ font-size: 0.76rem; color: var(--green); }}

    .grid {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 1.25rem;
      margin-top: 2.2rem;
    }}
    @media (max-width: 980px) {{ .grid {{ grid-template-columns: repeat(2, 1fr); }} }}
    @media (max-width: 640px) {{ .grid {{ grid-template-columns: 1fr; }} }}
    .cc-card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 1.35rem;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      gap: 0.9rem;
    }}
    .cc-card-top {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 0.75rem; }}
    .cc-logo-wrap {{ display: flex; align-items: center; gap: 0.75rem; }}
    .cc-index {{ font-size: 0.72rem; color: var(--muted); display: block; }}
    .cc-card h3 a {{ color: var(--text); text-decoration: none; font-size: 1.12rem; font-family: monospace; }}
    .cc-card h3 a:hover {{ color: var(--accent); }}
    .cc-cat {{
      font-size: 0.7rem;
      background: rgba(255,255,255,0.06);
      padding: 0.2rem 0.55rem;
      border-radius: 999px;
      color: var(--accent);
      white-space: nowrap;
    }}
    .cc-brand {{ font-size: 0.88rem; color: var(--muted); }}
    .cc-tool-box {{
      background: rgba(2, 6, 23, 0.55);
      border: 1px solid var(--border);
      padding: 0.65rem 0.8rem;
      border-radius: 8px;
      font-size: 0.82rem;
    }}
    .cc-footer {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-top: 0.6rem;
      border-top: 1px solid var(--border);
      font-size: 0.8rem;
    }}
    .cc-price {{ font-weight: 700; color: var(--green); }}
    .cc-btn {{
      background: var(--accent);
      color: #020617;
      font-weight: 700;
      padding: 0.38rem 0.85rem;
      border-radius: 8px;
      text-decoration: none;
    }}
  </style>
</head>
<body>
  <header class="header">
    <div class="container">
      <span class="eyebrow">AI-DRIVEN STATIC MONOREPO • COMMAND CENTER</span>
      <h1>Dashboard Kendali 13 Domain & Micro-SaaS ({owner['name']})</h1>
      <p style="color: var(--muted); max-width: 780px;">
        Satu repositori statis melayani 13 custom domain melalui Cloudflare Pages Edge Router (<code>_worker.js</code>) dengan 13 kalkulator interaktif mandiri dan artikel SEO terstruktur.
      </p>
      <div class="stats-bar">
        <div class="stat-box">
          <div class="stat-label">Total Properti Aktif</div>
          <div class="stat-val">13 Domain</div>
          <div class="stat-sub">100% Terverifikasi RDAP PANDI</div>
        </div>
        <div class="stat-box">
          <div class="stat-label">Modal Akuisisi Promo</div>
          <div class="stat-val">Rp 2.600</div>
          <div class="stat-sub">@ Rp 200 / Domain (Tahun 1)</div>
        </div>
        <div class="stat-box">
          <div class="stat-label">Total Valuasi Katalog Akuisisi</div>
          <div class="stat-val">Rp {total_valuation:,.0f}</div>
          <div class="stat-sub">Termasuk Paket Bundle Ekuitas & KodeLab</div>
        </div>
        <div class="stat-box">
          <div class="stat-label">Biaya Server / Hosting Bulanan</div>
          <div class="stat-val">Rp 0 / bln</div>
          <div class="stat-sub">Cloudflare Pages Multi-Domain Edge</div>
        </div>
      </div>
    </div>
  </header>

  <main class="container">
    <div class="grid">
      {cards_html}
    </div>
  </main>
</body>
</html>
""".replace(",", ".")


def build_cloudflare_worker(domains: list, primary_domain: str) -> str:
    domain_names = [d["domain"] for d in domains]
    return f"""// Cloudflare Workers with Static Assets (worker.js)
// Automatically routes 13 custom domains from a single deployment based on the Host header.

const KNOWN_DOMAINS = new Set({json.dumps(domain_names)});
const DEFAULT_DOMAIN = "{primary_domain}";

export default {{
  async fetch(request, env) {{
    const url = new URL(request.url);
    const rawHost = (request.headers.get("host") || "").toLowerCase().split(":")[0];
    const cleanHost = rawHost.startsWith("www.") ? rawHost.slice(4) : rawHost;

    // 1. If accessed via one of the 13 custom domains:
    if (KNOWN_DOMAINS.has(cleanHost)) {{
      if (!url.pathname.startsWith(`/${{cleanHost}}/`)) {{
        const subPath = (url.pathname === "/" || url.pathname === "") ? "/index.html" : url.pathname;
        const targetPath = `/${{cleanHost}}${{subPath}}`;
        const rewrittenUrl = new URL(targetPath, url.origin);
        return env.ASSETS.fetch(new Request(rewrittenUrl.toString(), request));
      }}
    }}

    // 2. If accessed via *.workers.dev root (/), serve the Empire Command Center:
    if (url.pathname === "/" || url.pathname === "/index.html") {{
      const ccUrl = new URL("/command-center/index.html", url.origin);
      return env.ASSETS.fetch(new Request(ccUrl.toString(), request));
    }}

    return env.ASSETS.fetch(request);
  }}
}};
"""


def build_sitemap_and_robots(domain_dir: Path, domain_cfg: dict) -> None:
    domain = domain_cfg["domain"]
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://{domain}/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>
"""
    robots = f"""User-agent: *
Allow: /
Sitemap: https://{domain}/sitemap.xml
"""
    (domain_dir / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    (domain_dir / "robots.txt").write_text(robots, encoding="utf-8")


def build_all() -> dict:
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True, exist_ok=True)

    domains = manifest["domains"]
    owner = manifest["owner"]

    built_domains = []
    for d_cfg in domains:
        domain = d_cfg["domain"]
        d_dir = DIST_DIR / domain
        d_dir.mkdir(parents=True, exist_ok=True)

        # Write standalone SVG logo
        svg_str = generate_svg_logo(
            d_cfg["theme"]["icon_type"],
            d_cfg["theme"]["primary"],
            d_cfg["theme"]["accent"],
            d_cfg["brand_name"],
        )
        (d_dir / "logo.svg").write_text(svg_str, encoding="utf-8")

        # Write index.html
        html_str = build_domain_page(d_cfg, domains, owner)
        (d_dir / "index.html").write_text(html_str, encoding="utf-8")

        # Write sitemap.xml & robots.txt
        build_sitemap_and_robots(d_dir, d_cfg)
        built_domains.append(domain)

    # Write Master Command Center at dist/command-center/index.html
    # (Keeping root of dist/ free of index.html ensures Cloudflare Workers always invokes worker.js on '/')
    cc_dir = DIST_DIR / "command-center"
    cc_dir.mkdir(parents=True, exist_ok=True)
    (cc_dir / "index.html").write_text(build_command_center(manifest), encoding="utf-8")

    # Write Cloudflare Worker script at repo root (worker.js) for `npx wrangler deploy`
    (BASE_DIR / "worker.js").write_text(
        build_cloudflare_worker(domains, owner["primary_domain"]), encoding="utf-8"
    )

    # Write wrangler.toml configured for Cloudflare Workers with Static Assets (`npx wrangler deploy`)
    wrangler_cfg = """name = "kakdiko-13-domain-empire"
main = "worker.js"
compatibility_date = "2024-11-01"

[assets]
directory = "./dist"
binding = "ASSETS"
"""
    (BASE_DIR / "wrangler.toml").write_text(wrangler_cfg, encoding="utf-8")

    return {"count": len(built_domains), "domains": built_domains, "dist_dir": str(DIST_DIR)}


if __name__ == "__main__":
    res = build_all()
    print(f"[OK] Successfully built {res['count']} domains into {res['dist_dir']}:")
    for idx, dom in enumerate(res["domains"], 1):
        print(f"    {idx:02d}. {dom} -> dist/{dom}/index.html")
