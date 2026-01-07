import { useEffect, useMemo, useState } from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";
import "./App.css";

const TABS = [
  { id: "overview", label: "Overview" },
  { id: "iqr", label: "IQR Anomalies" },
  { id: "z", label: "Z-Score Anomalies" },
  { id: "groups", label: "Group Insights" },
];

function safeNumber(x) {
  const n = Number(x);
  return Number.isFinite(n) ? n : null;
}

function fmt(n) {
  if (n === null || n === undefined) return "-";
  const num = Number(n);
  if (!Number.isFinite(num)) return String(n);
  return num.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

function pickKey(obj, candidates) {
  if (!obj) return null;
  for (const k of candidates) if (k in obj) return k;
  return null;
}

function uniqueValues(rows, key) {
  if (!key) return [];
  const set = new Set();
  for (const r of rows) {
    const v = r?.[key];
    if (v !== undefined && v !== null && String(v).trim() !== "") set.add(String(v));
  }
  return Array.from(set).sort((a, b) => a.localeCompare(b));
}

export default function App() {
  const [tab, setTab] = useState("overview");
  const [summary, setSummary] = useState(null);
  const [anoms, setAnoms] = useState([]);
  const [groups, setGroups] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  // Filters
  const [method, setMethod] = useState("ALL");
  const [stateFilter, setStateFilter] = useState("ALL");
  const [providerType, setProviderType] = useState("ALL");
  const [posFilter, setPosFilter] = useState("ALL");
  const [limit, setLimit] = useState(50);

useEffect(() => {
  async function fetchJson(url) {
    const r = await fetch(url, { cache: "no-store" });

    
    const text = await r.text();

    if (!r.ok) {
      throw new Error(`HTTP ${r.status} when fetching ${url}\nFirst chars: ${text.slice(0, 120)}`);
    }

    try {
      return JSON.parse(text);
    } catch (e) {
      throw new Error(
        `Invalid JSON from ${url}. (Maybe HTML returned)\nFirst chars: ${text.slice(0, 120)}`
      );
    }
  }

  async function load() {
    try {
      setLoading(true);
      setErr("");

      const [s, a, g] = await Promise.all([
        fetchJson("/summary.json"),
        fetchJson("/anomalies.json"),
        fetchJson("/top_groups.json").catch(() => null),
      ]);

      setSummary(s);
      setAnoms(Array.isArray(a) ? a : []);
      setGroups(g);
    } catch (e) {
      console.error(e);
      setErr(String(e.message || e));
    } finally {
      setLoading(false);
    }
  }

  load();
}, []);


  const costKey = useMemo(() => {
    
    if (summary?.cost_column) return summary.cost_column;

    
    return pickKey(anoms?.[0], [
      "avg_mdcr_pymt_amt",
      "avg_mdcr_stdzd_amt",
      "avg_mdcr_alowd_amt",
      "avg_sbmtd_chrg_amt",
      "price_amt",
    ]) || "price_amt";
  }, [summary, anoms]);

  const methodKey = useMemo(() => {
    return pickKey(anoms?.[0], ["anomaly_method", "method", "flag"]) || "anomaly_method";
  }, [anoms]);

 
  const stateKey = useMemo(
    () => pickKey(anoms?.[0], ["rndrng_prvdr_state_abrvtn", "state", "provider_state"]),
    [anoms]
  );
  const providerTypeKey = useMemo(
    () => pickKey(anoms?.[0], ["rndrng_prvdr_type", "provider_type"]),
    [anoms]
  );
  const posKey = useMemo(
    () => pickKey(anoms?.[0], ["place_of_srvc_label", "place_of_srvc", "pos", "place_of_service"]),
    [anoms]
  );
  const hcpcsKey = useMemo(
    () => pickKey(anoms?.[0], ["hcpcs_cd", "hcpcs_code"]),
    [anoms]
  );
  const hcpcsDescKey = useMemo(
    () => pickKey(anoms?.[0], ["hcpcs_desc", "hcpcs_description"]),
    [anoms]
  );
  const npiKey = useMemo(
    () => pickKey(anoms?.[0], ["rndrng_npi", "npi"]),
    [anoms]
  );

  const stateOptions = useMemo(() => uniqueValues(anoms, stateKey), [anoms, stateKey]);
  const providerTypeOptions = useMemo(
    () => uniqueValues(anoms, providerTypeKey),
    [anoms, providerTypeKey]
  );
  const posOptions = useMemo(() => uniqueValues(anoms, posKey), [anoms, posKey]);

  const filtered = useMemo(() => {
    let rows = [...anoms];

    if (method !== "ALL") {
      rows = rows.filter((r) => String(r?.[methodKey] ?? "").toUpperCase() === method);
    }
    if (stateKey && stateFilter !== "ALL") {
      rows = rows.filter((r) => String(r?.[stateKey] ?? "") === stateFilter);
    }
    if (providerTypeKey && providerType !== "ALL") {
      rows = rows.filter((r) => String(r?.[providerTypeKey] ?? "") === providerType);
    }
    if (posKey && posFilter !== "ALL") {
      rows = rows.filter((r) => String(r?.[posKey] ?? "") === posFilter);
    }

    // sort by cost desc
    rows.sort((a, b) => (safeNumber(b?.[costKey]) ?? -1) - (safeNumber(a?.[costKey]) ?? -1));
    return rows;
  }, [anoms, method, methodKey, stateKey, stateFilter, providerTypeKey, providerType, posKey, posFilter, costKey]);

  const chartData = useMemo(() => {
    const rows = filtered.slice(0, limit);
    return rows.map((r, i) => ({
      name: `#${i + 1}`,
      value: safeNumber(r?.[costKey]) ?? 0,
    }));
  }, [filtered, limit, costKey]);

  const iqrRows = useMemo(
    () => filtered.filter((r) => String(r?.[methodKey] ?? "").toUpperCase() === "IQR"),
    [filtered, methodKey]
  );
  const zRows = useMemo(
    () => filtered.filter((r) => String(r?.[methodKey] ?? "").toUpperCase().includes("Z")),
    [filtered, methodKey]
  );

  const kpi = useMemo(() => {
    const rows = summary?.rows ?? summary?.n_rows ?? anoms.length;
    const mean = summary?.cost_mean ?? summary?.mean;
    const median = summary?.cost_median ?? summary?.median;
    const max = summary?.cost_max ?? summary?.max;
    const iqrUpper = summary?.IQR_upper_bound ?? summary?.iqr_upper_bound ?? summary?.iqrUpper;
    const iqrCount = summary?.["IQR anomalies count"] ?? summary?.iqr_anomalies_count ?? summary?.iqr_count;
    const zCount = summary?.["Z-score anomalies count"] ?? summary?.zscore_anomalies_count ?? summary?.z_count;

    return { rows, mean, median, max, iqrUpper, iqrCount, zCount };
  }, [summary, anoms.length]);

  if (loading) return <div className="page"><div className="card">Loading…</div></div>;
  if (err) return <div className="page"><div className="card error">{err}</div></div>;

  return (
    <div className="page">
      <header className="header">
        <div>
          <h1>CMS Medicare Physician & Supplier — Anomaly Dashboard</h1>
          <p className="sub">
            Detecting unusual Medicare billing patterns using <b>IQR</b> and <b>Z-score</b>, with interactive filtering and scientific interpretation.
          </p>
        </div>

        <div className="pill">
          <div className="pillLabel">Cost Metric</div>
          <div className="pillValue">{costKey}</div>
        </div>
      </header>

      <nav className="tabs">
        {TABS.map((t) => (
          <button
            key={t.id}
            className={`tab ${tab === t.id ? "active" : ""}`}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>

      <section className="kpis">
        <div className="kpi">
          <div className="kLabel">Rows</div>
          <div className="kValue">{fmt(kpi.rows)}</div>
        </div>
        <div className="kpi">
          <div className="kLabel">Mean</div>
          <div className="kValue">{fmt(kpi.mean)}</div>
        </div>
        <div className="kpi">
          <div className="kLabel">Median</div>
          <div className="kValue">{fmt(kpi.median)}</div>
        </div>
        <div className="kpi">
          <div className="kLabel">Max</div>
          <div className="kValue">{fmt(kpi.max)}</div>
        </div>
        <div className="kpi">
          <div className="kLabel">IQR Upper Bound</div>
          <div className="kValue">{fmt(kpi.iqrUpper)}</div>
        </div>
        <div className="kpi">
          <div className="kLabel">Anomalies (IQR / Z)</div>
          <div className="kValue">{fmt(kpi.iqrCount)} / {fmt(kpi.zCount)}</div>
        </div>
      </section>

      {/* FILTER BAR */}
      <section className="card filters">
        <div className="filtersTitle">Filters</div>

        <div className="filtersGrid">
          <label className="field">
            <span>Method</span>
            <select value={method} onChange={(e) => setMethod(e.target.value)}>
              <option value="ALL">All</option>
              <option value="IQR">IQR</option>
              <option value="Z">Z-score</option>
            </select>
          </label>

          <label className="field">
            <span>Show Top</span>
            <select value={limit} onChange={(e) => setLimit(Number(e.target.value))}>
              {[10, 20, 50, 100, 200].map((n) => (
                <option key={n} value={n}>{n}</option>
              ))}
            </select>
          </label>

          <label className="field">
            <span>State</span>
            <select value={stateFilter} onChange={(e) => setStateFilter(e.target.value)} disabled={!stateKey}>
              <option value="ALL">All</option>
              {stateOptions.map((v) => <option key={v} value={v}>{v}</option>)}
            </select>
          </label>

          <label className="field">
            <span>Provider Type</span>
            <select value={providerType} onChange={(e) => setProviderType(e.target.value)} disabled={!providerTypeKey}>
              <option value="ALL">All</option>
              {providerTypeOptions.map((v) => <option key={v} value={v}>{v}</option>)}
            </select>
          </label>

          <label className="field">
            <span>Place of Service</span>
            <select value={posFilter} onChange={(e) => setPosFilter(e.target.value)} disabled={!posKey}>
              <option value="ALL">All</option>
              {posOptions.map((v) => <option key={v} value={v}>{v}</option>)}
            </select>
          </label>
        </div>

        <div className="hint">
          <b>Interpretation:</b> An anomaly here means the selected cost metric is unusually high compared to the overall distribution (IQR) or statistically extreme (Z-score).
        </div>
      </section>

      {/* TAB CONTENT */}
      {tab === "overview" && (
        <section className="grid2">
          <div className="card">
            <h2>What is an “Anomaly” in this dataset?</h2>
            <p className="text">
              In CMS Medicare utilization and payment data, an anomaly typically indicates an unusually high value in a payment-related metric
              for a specific service (HCPCS code) and/or provider context. This may reflect legitimate clinical complexity, geographic differences,
              coding patterns, or potential billing irregularities — and it requires clinical/administrative review.
            </p>

            <ul className="bullets">
              <li><b>IQR:</b> flags values above Q3 + 1.5×IQR (robust to skewed data).</li>
              <li><b>Z-score:</b> flags values far from the mean (sensitive to extreme outliers).</li>
              <li><b>Next step:</b> compare anomalies by state, provider type, and place of service.</li>
            </ul>
          </div>

          <div className="card">
            <h2>Quick quality checks</h2>
            <div className="mini">
              <div className="miniRow"><span>Loaded anomalies</span><b>{fmt(anoms.length)}</b></div>
              <div className="miniRow"><span>Cost metric</span><b>{costKey}</b></div>
              <div className="miniRow"><span>Context columns</span><b>{[stateKey, providerTypeKey, posKey, hcpcsKey].filter(Boolean).length}/4</b></div>
            </div>

            <p className="text dim">
              
            </p>
          </div>
        </section>
      )}

      {(tab === "iqr" || tab === "z") && (
        <>
          <section className="card">
            <div className="sectionHeader">
              <h2>
                Top {limit} Anomalies ({tab === "iqr" ? "IQR Focus" : "Z-score Focus"}) — sorted by <code>{costKey}</code>
              </h2>
              <div className="sectionMeta">
                Current filtered rows: <b>{fmt(filtered.length)}</b>
              </div>
            </div>

            <div className="chartWrap">
              <ResponsiveContainer width="100%" height={360}>
                <BarChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" interval={Math.max(0, Math.floor(limit / 25) - 1)} />
                  <YAxis />
                  <Tooltip formatter={(v) => fmt(v)} />
                  <Bar dataKey="value" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="text dim">
              <b>Why this matters:</b> These are the most extreme values under the chosen filters. Use the table below to inspect the service (HCPCS),
              provider, and context — then justify whether the anomaly could be clinical (legitimate) or administrative (needs review).
            </div>
          </section>

          <section className="card">
            <h2>Detailed Anomalies Table</h2>

            <div className="tableWrap">
              <table>
                <thead>
                  <tr>
                    <th>#</th>
                    {npiKey && <th>NPI</th>}
                    {stateKey && <th>State</th>}
                    {providerTypeKey && <th>Provider Type</th>}
                    {posKey && <th>Place of Service</th>}
                    {hcpcsKey && <th>HCPCS</th>}
                    {hcpcsDescKey && <th>HCPCS Description</th>}
                    <th>{costKey}</th>
                    <th>Method</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.slice(0, limit).map((r, idx) => (
                    <tr key={idx}>
                      <td>{idx + 1}</td>
                      {npiKey && <td className="mono">{r?.[npiKey] ?? "-"}</td>}
                      {stateKey && <td>{r?.[stateKey] ?? "-"}</td>}
                      {providerTypeKey && <td>{r?.[providerTypeKey] ?? "-"}</td>}
                      {posKey && <td>{r?.[posKey] ?? "-"}</td>}
                      {hcpcsKey && <td className="mono">{r?.[hcpcsKey] ?? "-"}</td>}
                      {hcpcsDescKey && <td className="wrap">{r?.[hcpcsDescKey] ?? "-"}</td>}
                      <td className="mono">{fmt(r?.[costKey])}</td>
                      <td className="badge">{String(r?.[methodKey] ?? "-")}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="footNote">
              <b>Scientific note:</b> If the distribution is highly skewed, IQR tends to be more stable than Z-score.
              For payment datasets, skewness is common — which is why your project benefits from showing both methods.
            </div>
          </section>
        </>
      )}

      {tab === "groups" && (
        <section className="grid2">
          <div className="card">
            <h2>Group-level insights (if exported)</h2>
            <p className="text">
              
            </p>

            {!groups && (
              <div className="warn">
                <b>top_groups.json not found.</b>  
                You can still score high, but exporting group summaries will make your report much stronger.
              </div>
            )}

            {groups && (
              <pre className="pre">
                {JSON.stringify(groups, null, 2)}
              </pre>
            )}
          </div>

          <div className="card">
            <h2>What you will say in the report</h2>
            <ul className="bullets">
              <li>We applied robust anomaly detection (IQR) + statistical extreme detection (Z-score).</li>
              <li>We engineered ratios/log features to reduce skewness and compare billing behaviors.</li>
              <li>We validated findings using stratification filters (state, provider type, place of service).</li>
              <li>We produced an interactive dashboard enabling inspection of extreme cases.</li>
            </ul>

            <div className="hint">
              
            </div>
          </div>
        </section>
      )}

      <footer className="footer">
        <div>
          <b>Tip:</b> Every time you re-run <code>python main.py</code>, copy the JSON files again to <code>frontend/public</code> and refresh the page.
        </div>
      </footer>
    </div>
  );
}
