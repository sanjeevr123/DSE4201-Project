"""
Literature verification, stage 1 (registry) and stage 2 (abstract). For each chosen DOI: fetch the Crossref record (publisher metadata) and the
OpenAlex record (open scholarly index: abstract, open-access location, page range), compare with the details claimed in docs/THESIS_PLAN.md 6.2,
and write notes/literature/registry_check.csv. Raw responses are cached in notes/literature/cache/ (not committed). Verification levels:
registry = the Crossref record matches title, authors, venue, year, volume, issue and pages; abstract = an abstract was retrieved and read. Neither
level supports a claim about findings beyond what the abstract states.   .venv/bin/python scripts/lit_verify.py
"""
import csv, json, re, sys, time, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "notes" / "literature" / "cache"
# key: (doi, first-author surname(s) claimed, year claimed, journal fragment, volume, issue, pages)
CLAIMS = {
 "ardia2018": ("10.1016/j.ijforecast.2018.05.004", "Ardia", 2018, "International Journal of Forecasting", "34", "4", "733-747"),
 "santos2013": ("10.1093/jjfinec/nbs015", "Santos", 2013, "Journal of Financial Econometrics", "11", "2", "400-441"),
 "fortin2023": ("10.1016/j.ijforecast.2021.11.010", "Fortin", 2023, "International Journal of Forecasting", "39", "1", "314-331"),
 "paolella2019": ("10.1016/j.jeconom.2019.07.002", "Paolella", 2019, "Journal of Econometrics", "213", "2", "493-515"),
 "pelletier2006": ("10.1016/j.jeconom.2005.01.013", "Pelletier", 2006, "Journal of Econometrics", "131", "1-2", "445-473"),
 "giacomini2006": ("10.1111/j.1468-0262.2006.00718.x", "Giacomini", 2006, "Econometrica", "74", "6", "1545-1578"),
 "diebold1995": ("10.1080/07350015.1995.10524599", "Diebold", 1995, "Journal of Business", "13", "3", "253-263"),
 "hln1997": ("10.1016/s0169-2070(96)00719-4", "Harvey", 1997, "International Journal of Forecasting", "13", "2", "281-291"),
 "newey1994": ("10.2307/2297912", "Newey", 1994, "Review of Economic Studies", "61", "4", "631-653"),
 "clark2001": ("10.1016/s0304-4076(01)00071-9", "Clark", 2001, "Journal of Econometrics", "105", "1", "85-110"),
 "clark2007": ("10.1016/j.jeconom.2006.05.023", "Clark", 2007, "Journal of Econometrics", "138", "1", "291-311"),
 "mccracken2020": ("10.3982/ecta17523", "McCracken", 2020, "Econometrica", "88", "4", "1753-1754"),
 "west1996": ("10.2307/2171956", "West", 1996, "Econometrica", "64", "5", "1067-1084"),
 "fissler2016": ("10.1214/16-aos1439", "Fissler", 2016, "Annals of Statistics", "44", "4", "1680-1707"),
 "patton2019": ("10.1016/j.jeconom.2018.10.008", "Patton", 2019, "Journal of Econometrics", "211", "2", "388-413"),
 "nolde2017": ("10.1214/17-aoas1041", "Nolde", 2017, "Annals of Applied Statistics", "11", "4", "1833-1874"),
 "hansen2005": ("10.1198/073500105000000063", "Hansen", 2005, "Journal of Business", "23", "4", "365-380"),
 "hansen2011": ("10.3982/ECTA5771", "Hansen", 2011, "Econometrica", "79", "2", "453-497"),
 "kupiec1995": ("10.3905/jod.1995.407942", "Kupiec", 1995, "Journal of Derivatives", "3", "2", "73-84"),
 "christoffersen1998": ("10.2307/2527341", "Christoffersen", 1998, "International Economic Review", "39", "4", "841-862"),
 "lakens2017": ("10.1177/1948550617697177", "Lakens", 2017, "Social Psychological and Personality Science", "8", "4", "355-362"),
 "hoenig2001": ("10.1198/000313001300339897", "Hoenig", 2001, "American Statistician", "55", "1", "19-24"),
 "nosek2018": ("10.1073/pnas.1708274114", "Nosek", 2018, "Proceedings of the National Academy of Sciences", "115", "11", "2600-2606"),
 "engle2002": ("10.1198/073500102288618487", "Engle", 2002, "Journal of Business", "20", "3", "339-350"),
 "bollerslev1990": ("10.2307/2109358", "Bollerslev", 1990, "Review of Economics and Statistics", "72", "3", "498-505"),
 "bollerslev1986": ("10.1016/0304-4076(86)90063-1", "Bollerslev", 1986, "Journal of Econometrics", "31", "3", "307-327"),
 "hamilton1989": ("10.2307/1912559", "Hamilton", 1989, "Econometrica", "57", "2", "357-384"),
 "angbekaert2002": ("10.1093/rfs/15.4.1137", "Ang", 2002, "Review of Financial Studies", "15", "4", "1137-1187"),
 "forbes2002": ("10.1111/0022-1082.00494", "Forbes", 2002, "Journal of Finance", "57", "5", "2223-2261"),
 "engle2006": ("10.1198/073500106000000017", "Engle", 2006, "Journal of Business", "24", "2", "238-253"),
 "pouliasis2018": ("10.1002/fut.21939", "Pouliasis", 2018, "Journal of Futures Markets", "38", "11", "1407-1439"),
 "chua2009": ("10.3905/jpm.2009.36.1.026", "Chua", 2009, "Journal of Portfolio Management", "36", "1", "26-35"),
 "kinlaw2021": ("10.3905/jpm.2021.1.273", "Kinlaw", 2021, "Journal of Portfolio Management", "47", "8", "124-137"),
 "kole2017": ("10.1093/jjfinec/nbx019", "Kole", 2017, "Journal of Financial Econometrics", "15", "4", "649-677"),
 "brooks2003": ("10.1002/for.841", "Brooks", 2003, "Journal of Forecasting", "22", "1", "1-22"),
 "mcaleer2008": ("10.1002/for.1054", "McAleer", 2008, "Journal of Forecasting", "27", "3", "217-235"),
 "baele2010": ("10.1093/rfs/hhq014", "Baele", 2010, "Review of Financial Studies", "23", "6", "2374-2428"),
 "campbell2020": ("10.1086/707766", "Campbell", 2020, "Journal of Political Economy", "128", "8", "3148-3185"),
 "campbell2017": ("10.1561/104.00000043", "Campbell", 2017, "Critical Finance Review", "6", "2", "263-301"),
 "connolly2005": ("10.1017/s0022109000001782", "Connolly", 2005, "Journal of Financial and Quantitative Analysis", "40", "1", "161-194"),
 "abadie2020": ("10.1257/aeri.20190252", "Abadie", 2020, "American Economic Review: Insights", "2", "2", "193-208"),
 "altman1995": ("10.1136/bmj.311.7003.485", "Altman", 1995, "BMJ", "311", "7003", "485"),
 "ioannidis2017": ("10.1111/ecoj.12461", "Ioannidis", 2017, "Economic Journal", "127", "605", "F236-F265"),
}


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "thesis-citation-check/1.0"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.load(r)


def abstract(oa):
    inv = oa.get("abstract_inverted_index")
    if not inv:
        return ""
    words = sorted(((p, w) for w, ps in inv.items() for p in ps))
    return " ".join(w for _, w in words)


def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower().replace("&amp;", "and"))


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    rows = []
    for key, (doi, au, yr, jr, vol, iss, pages) in CLAIMS.items():
        row = dict(key=key, doi=doi)
        try:
            cr = get("https://api.crossref.org/works/" + urllib.parse.quote(doi))["message"]
            (CACHE / f"crossref_{key}.json").write_text(json.dumps(cr))
        except Exception as e:
            row.update(registry="NOT FOUND in Crossref", note=str(e)[:60]); rows.append(row); continue
        try:
            oa = get("https://api.openalex.org/works/doi:" + urllib.parse.quote(doi))
            (CACHE / f"openalex_{key}.json").write_text(json.dumps(oa))
        except Exception:
            oa = {}
        a1 = (cr.get("author") or [{}])[0].get("family", "")
        issued = [(cr.get(k) or {}).get("date-parts", [[None]])[0][0] for k in ("issued", "published-print", "published-online")]
        yr_print = (cr.get("published-print") or {}).get("date-parts", [[None]])[0][0]
        pg = cr.get("page", "")
        bib = oa.get("biblio") or {}
        pg_oa = "-".join(x for x in (bib.get("first_page"), bib.get("last_page")) if x)
        checks = {"author": norm(au) in norm(a1), "year": yr in issued or yr == yr_print, "journal": norm(jr) in norm((cr.get("container-title") or [""])[0]),
                  "volume": str(cr.get("volume", "")) == vol, "issue": str(cr.get("issue", "")) == iss,
                  "pages": norm(pages) in (norm(pg), norm(pg_oa)) or (pg and norm(pages).startswith(norm(pg).split("-")[0]) and "-" not in pg)}
        ab = abstract(oa)
        row.update(title=(cr.get("title") or [""])[0], first_author=a1, container=(cr.get("container-title") or [""])[0], vol=cr.get("volume", ""),
                   issue=cr.get("issue", ""), page_crossref=pg, page_openalex=pg_oa, year_print=yr_print, year_online=issued[2], year_issued=issued[0],
                   corrections=";".join(u.get("DOI", "") for u in cr.get("update-to", []) + cr.get("updated-by", [])) if (cr.get("update-to") or cr.get("updated-by")) else "",
                   oa_status=(oa.get("open_access") or {}).get("oa_status", ""), oa_url=(oa.get("open_access") or {}).get("oa_url", ""),
                   abstract_chars=len(ab), **{f"ok_{k}": v for k, v in checks.items()})
        row["registry"] = "MATCH" if all(checks.values()) else "CHECK: " + ",".join(k for k, v in checks.items() if not v)
        rows.append(row)
        time.sleep(0.3)
    keys = sorted({k for r in rows for k in r}, key=lambda k: ["key", "doi", "registry"].index(k) if k in ("key", "doi", "registry") else 9)
    with open(ROOT / "notes" / "literature" / "registry_check.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(rows)
    for r in rows:
        if r.get("registry") != "MATCH":
            print(r["key"], r.get("registry"), "|", r.get("title", "")[:50], "|", r.get("container", ""), r.get("vol"), r.get("issue"), "cr:", r.get("page_crossref"), "oa:", r.get("page_openalex"), "yrs", r.get("year_print"), r.get("year_online"), r.get("year_issued"))
    print(f"\n{sum(r.get('registry') == 'MATCH' for r in rows)} of {len(rows)} match on author, year, journal, volume, issue and pages;",
          f"{sum(1 for r in rows if r.get('abstract_chars', 0) > 200)} have an abstract via OpenAlex;",
          f"{sum(1 for r in rows if r.get('oa_url'))} have an open-access URL")


if __name__ == "__main__":
    main()
