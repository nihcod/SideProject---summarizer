import ResourcePanel from "./components/ResourcePanel.jsx";
import UrlSummaryPanel from "./components/UrlSummaryPanel.jsx";
import WikipediaPanel from "./components/WikipediaPanel.jsx";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export default function App() {
  return (
    <div className="app-shell">
      <header className="app-shell__header">
        <div>
          <p className="eyebrow">webProject_summary</p>
          <h1>Perplexity 기반 요약 & 리서치 허브</h1>
          <p className="lede">웹페이지 요약 · 위키 검색 · 키워드 리서치를 한 화면에서 빠르게 확인하세요.</p>
        </div>
      </header>

      <section className="panel-grid">
        <UrlSummaryPanel apiBase={API_BASE} />
        <WikipediaPanel apiBase={API_BASE} />
        <ResourcePanel apiBase={API_BASE} />
      </section>
    </div>
  );
}
