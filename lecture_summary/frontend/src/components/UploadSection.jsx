import React, { useState } from "react";
import axios from "axios";

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8080";

export default function UploadSection() {
  const [file, setFile] = useState(null);
  const [audience, setAudience] = useState("novice");          // 초심자 / intermediate
  const [purpose, setPurpose] = useState("understanding");     // 이해 / exam
  const [summary, setSummary] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!file) return;
    setLoading(true);
    setSummary("");

    try {
      const form = new FormData();
      form.append("file", file);
      form.append("audience", audience);
      form.append("purpose", purpose);

      const res = await axios.post(`${API_URL}/upload`, form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setSummary(res.data.summary || JSON.stringify(res.data, null, 2));
    } catch (err) {
      console.error(err);
      alert("업로드/요약 요청 중 오류가 발생했어요. (백엔드 실행 확인)");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: "grid", gap: 12, maxWidth: 720 }}>
      <input type="file" accept=".pdf,.ppt,.pptx" onChange={(e) => setFile(e.target.files[0])} />

      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        <strong>이해 난이도:</strong>
        <button onClick={() => setAudience("novice")}            disabled={audience==="novice"}>초심자</button>
        <button onClick={() => setAudience("intermediate")}      disabled={audience==="intermediate"}>기본지식 있음</button>

        <strong style={{ marginLeft: 12 }}>용도:</strong>
        <button onClick={() => setPurpose("understanding")}       disabled={purpose==="understanding"}>내용 이해</button>
        <button onClick={() => setPurpose("exam")}                disabled={purpose==="exam"}>시험 대비</button>
      </div>

      <button disabled={!file || loading} onClick={handleSubmit}>
        {loading ? "생성 중..." : "요약 생성 시작"}
      </button>

      {summary && (
        <div>
          <h3>요약 결과</h3>
          <pre style={{ whiteSpace: "pre-wrap" }}>{summary}</pre>
        </div>
      )}
    </div>
  );
}
