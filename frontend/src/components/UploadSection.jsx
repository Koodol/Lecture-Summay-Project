import React, { useState } from "react";
import axios from "axios";

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8080";

export default function UploadSection() {
  const [file, setFile] = useState(null);
  const [audience, setAudience] = useState("novice");          // 초심자 / intermediate
  const [purpose, setPurpose] = useState("understanding");     // 이해 / exam

  // 응답을 구조적으로 표시하기 위한 상태들
  const [summary, setSummary] = useState(null);     // { high_level, sections }
  const [terms, setTerms] = useState([]);           // glossary/terms 배열
  const [questions, setQuestions] = useState([]);   // 문제 배열
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false); // 제출 이후 결과 유무 표시용

  const handleSubmit = async () => {
    if (!file) return;
    setLoading(true);
    setSubmitted(true);
    // 이전 결과 초기화
    setSummary(null);
    setTerms([]);
    setQuestions([]);

    try {
      const form = new FormData();
      form.append("file", file);
      form.append("audience", audience);
      form.append("purpose", purpose);

      const res = await axios.post(`${API_URL}/upload`, form, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      // 백엔드 응답은 { meta, summary, glossary(=terms), questions }
      // 혹은 (구버전) { meta, result: { summary, glossary, questions } }
      const payload = res.data.result || res.data;
      // 디버깅: 콘솔에 길이 출력
      try {
        const cnt = payload.counts || {};
        console.log("[upload] counts:", cnt,
          "terms=", (payload.terms || payload.glossary || []).length,
          "questions=", (payload.questions || []).length
        );
      } catch (e) {}
      setSummary(payload.summary || null);
      setTerms(payload.terms || payload.glossary || []);
      setQuestions(payload.questions || []);
    } catch (err) {
      console.error(err);
      alert("요약 요청 중 오류가 발생했습니다. (백엔드 실행 및 로그 확인)");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: "grid", gap: 12, maxWidth: 720 }}>
      <input type="file" accept=".pdf,.ppt,.pptx" onChange={(e) => setFile(e.target.files[0])} />

      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        <strong>학습 대상:</strong>
        <button onClick={() => setAudience("novice")}            disabled={audience==="novice"}>초심자</button>
        <button onClick={() => setAudience("intermediate")}      disabled={audience==="intermediate"}>기본지식 있음</button>

        <strong style={{ marginLeft: 12 }}>목적:</strong>
        <button onClick={() => setPurpose("understanding")}       disabled={purpose==="understanding"}>이해 중심</button>
        <button onClick={() => setPurpose("exam")}                disabled={purpose==="exam"}>시험 대비</button>
      </div>

      <button disabled={!file || loading} onClick={handleSubmit}>
        {loading ? "생성 중..." : "요약 생성 시작"}
      </button>

      {/* 요약 결과 */}
      {summary && (
        <div>
          <h3>요약 결과</h3>
          {summary.high_level && (
            <div style={{ marginBottom: 12 }}>
              <strong>핵심 요약</strong>
              <p style={{ whiteSpace: "pre-wrap" }}>{summary.high_level}</p>
            </div>
          )}
          {Array.isArray(summary.sections) && summary.sections.length > 0 && (
            <div>
              <strong>섹션 요약</strong>
              <ul>
                {summary.sections.map((sec, idx) => (
                  <li key={idx} style={{ marginBottom: 8 }}>
                    <div><b>{sec.title || `섹션 ${idx + 1}`}</b></div>
                    {Array.isArray(sec.bullets) && (
                      <ul>
                        {sec.bullets.map((b, i) => (
                          <li key={i} style={{ whiteSpace: "pre-wrap" }}>{b}</li>
                        ))}
                      </ul>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* 용어 정리 (없어도 섹션을 보여 디버깅에 도움) */}
      {submitted && !loading && (
        <div>
          <h3>용어 정리</h3>
          {Array.isArray(terms) && terms.length > 0 ? (
            <ul>
              {terms.map((t, idx) => (
                <li key={idx} style={{ marginBottom: 6 }}>
                  <b>{t.term}</b>
                  {t.definition && <span>: {t.definition}</span>}
                  {t.importance && (
                    <div style={{ color: "#666" }}>중요도: {t.importance}</div>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <div style={{ color: "#888" }}>용어 결과 없음</div>
          )}
        </div>
      )}

      {/* 연습 문제 (없어도 섹션을 보여 디버깅에 도움) */}
      {submitted && !loading && (
        <div>
          <h3>연습 문제</h3>
          {Array.isArray(questions) && questions.length > 0 ? (
            <ol>
              {questions.map((q, idx) => (
                <li key={idx} style={{ marginBottom: 12 }}>
                  <div>
                    <b>[{q.type?.toUpperCase() || "Q"}]</b> {q.stem}
                  </div>
                  {Array.isArray(q.choices) && q.choices.length > 0 && (
                    <ul>
                      {q.choices.map((c, i) => (
                        <li key={i}>{c}</li>
                      ))}
                    </ul>
                  )}
                  {q.answer && (
                    <div><b>정답:</b> {q.answer}</div>
                  )}
                  {q.rationale && (
                    <div style={{ color: "#666" }}><b>해설:</b> {q.rationale}</div>
                  )}
                  {q.difficulty && (
                    <div style={{ color: "#666" }}>난이도: {q.difficulty}</div>
                  )}
                </li>
              ))}
            </ol>
          ) : (
            <div style={{ color: "#888" }}>문제 결과 없음</div>
          )}
        </div>
      )}
    </div>
  );
}
