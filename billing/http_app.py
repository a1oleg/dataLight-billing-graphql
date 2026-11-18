"""ASGI front end: GraphiQL at /, a plain console at /console, POST /graphql."""
from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.parse import parse_qs

from .schema import schema

WEB_DIR = Path(__file__).resolve().parent.parent / "web"

STATIC_TYPES = {
    "graphiql.min.js": "text/javascript; charset=utf-8",
    "graphiql.min.css": "text/css; charset=utf-8",
    "react.production.min.js": "text/javascript; charset=utf-8",
    "react-dom.production.min.js": "text/javascript; charset=utf-8",
}

GRAPHIQL_HTML = """<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>GraphiQL — DeepSeek billing</title>
<link rel="stylesheet" href="/static/graphiql.min.css">
<style>
  html, body, #graphiql { height: 100%; margin: 0; }
  body { background: #0f1115; }
</style>
</head>
<body>
<div id="graphiql">Загрузка GraphiQL…</div>
<script src="/static/react.production.min.js"></script>
<script src="/static/react-dom.production.min.js"></script>
<script src="/static/graphiql.min.js"></script>
<script>
  const defaultQuery = `{
  calculateRow(rowNumber: 5) {
    row { requestId rowNumber modelGroup modelName }
    recorded { components { code label amount } total }
    calculated { window { label tier } components { code tokens ratePerMillion amount } total }
    difference { components { code label amount } total }
    written { workbook calculatedWritten differenceWritten reasonWritten }
  }
}`;
  const fetcher = async (params) => {
    const response = await fetch('/graphql', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(params),
    });
    return response.json();
  };
  const root = ReactDOM.createRoot(document.getElementById('graphiql'));
  root.render(React.createElement(GraphiQL, { fetcher, defaultQuery }));
</script>
</body>
</html>
"""

INDEX_HTML = """<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>DeepSeek billing GraphQL</title>
<style>
  :root { color-scheme: dark; }
  body { margin: 0; font: 14px/1.45 ui-monospace, SFMono-Regular, Consolas, monospace;
         background: #0f1115; color: #d7dae0; }
  header { padding: 14px 20px; border-bottom: 1px solid #262a33; display: flex; gap: 12px; align-items: baseline; }
  h1 { font-size: 16px; margin: 0; font-weight: 600; }
  .muted { color: #8b93a1; font-size: 12px; }
  main { display: grid; grid-template-columns: 1fr 1fr; gap: 0; height: calc(100vh - 52px); }
  section { padding: 12px 16px; overflow: auto; }
  section + section { border-left: 1px solid #262a33; }
  textarea { width: 100%; height: 46vh; resize: vertical; background: #151922; color: #e6e9ef;
             border: 1px solid #2c313c; border-radius: 6px; padding: 10px; font: inherit; }
  button { background: #2563eb; color: white; border: 0; border-radius: 5px; padding: 7px 12px;
           font: inherit; cursor: pointer; margin: 6px 6px 6px 0; }
  button.ghost { background: #1c2230; color: #c7ccd6; }
  pre { white-space: pre-wrap; word-break: break-word; background: #151922; border: 1px solid #2c313c;
        border-radius: 6px; padding: 10px; min-height: 200px; }
</style>
</head>
<body>
<header>
  <h1>DeepSeek billing GraphQL</h1>
  <span class="muted">POST /graphql · схема и резолверы биллинга · <a href="/" style="color:#8ab4ff">GraphiQL</a></span>
</header>
<main>
  <section>
    <div class="muted">Запрос</div>
    <textarea id="q">{
  calculateRow(rowNumber: 5) {
    row { requestId rowNumber modelGroup }
    recorded { components { code label amount } total }
    calculated { window { label tier } components { code tokens ratePerMillion amount } total }
    difference { components { code label amount } total }
  }
}</textarea>
    <div>
      <button onclick="run()">Выполнить</button>
      <button class="ghost" onclick="ex('calculateRow')">calculateRow</button>
      <button class="ghost" onclick="ex('writeRow')">writeRow</button>
      <button class="ghost" onclick="ex('logRow')">logRow</button>
      <button class="ghost" onclick="ex('logRowByNumber')">rowNumber</button>
      <button class="ghost" onclick="ex('calculate')">calculate</button>
      <button class="ghost" onclick="ex('models')">models</button>
      <button class="ghost" onclick="ex('summary')">summary</button>
    </div>
    <div class="muted">Ctrl+Enter — выполнить</div>
  </section>
  <section>
    <div class="muted">Ответ</div>
    <pre id="out"></pre>
  </section>
</main>
<script>
const examples = {
  calculateRow: `{ calculateRow(rowNumber: 5) {
    row { requestId rowNumber modelGroup }
    recorded { components { code label amount } total }
    calculated { window { label tier } components { code tokens ratePerMillion amount } total }
    difference { components { code label amount } total }
  } }`,
  writeRow: `{ calculateRow(rowNumber: 9, writeCalculated: true, writeDifference: true, writeReason: true) {
    row { requestId rowNumber }
    recorded { total }
    calculated { total }
    difference { components { code amount } total }
    written { workbook calculatedWritten differenceWritten reasonWritten }
  } }`,
  logRow: `{ logRow(requestId: "06faa446-23f5-4386-9838-81d847e3405d") {
    requestId rowNumber startTime organizationId client modelGroup modelName status
    usage { promptTokens completionTokens cachedInputTokens reasoningTokens textTokens }
    recorded { input cachedInput output reasoning total }
    pythonCode
  } }`,
  logRowByNumber: `{ logRow(rowNumber: 5) {
    requestId rowNumber startTime client modelGroup
    usage { promptTokens completionTokens textTokens }
    recorded { total }
  } }`,
  calculate: `{ calculate(row: {
    requestId: "06faa446-23f5-4386-9838-81d847e3405d"
    startTime: "2026-10-13T00:00:27.467Z"
    model: DEEPSEEK_V4_FLASH
    usage: { promptTokens: 1020, completionTokens: 2621, cachedInputTokens: 128, reasoningTokens: 2030 }
  }) {
    model { name }
    window { label tier }
    lines { code tokens ratePerMillion amount }
    total
  } }`,
  models: `{ models { name slug windows { label tier kind startHour endHour inputPerMillion outputPerMillion } } }`,
  summary: `{ discrepancySummary {
    requests matchedRequests discrepantRequests
    groups { code title requests recordedTotal calculatedTotal differenceTotal sampleRequestIds }
  } }`,
  windowAt: `{ model(name: DEEPSEEK_FLASH) { slug windowAt(at: "2026-10-13T07:00:00Z") { label tier inputPerMillion outputPerMillion cacheReadPerMillion } } }`,
};
function ex(name) { document.getElementById('q').value = examples[name]; run(); }
async function run() {
  const out = document.getElementById('out');
  out.textContent = '…';
  try {
    const res = await fetch('/graphql', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ query: document.getElementById('q').value })
    });
    out.textContent = JSON.stringify(await res.json(), null, 1);
  } catch (e) { out.textContent = String(e); }
}
document.getElementById('q').addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) run();
});
</script>
</body>
</html>
"""


class GraphQLApp:
    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            return
        path = scope.get("path", "/")
        method = scope.get("method", "GET").upper()

        if path in ("/", "/graphiql"):
            return await self._send(send, 200, GRAPHIQL_HTML.encode("utf-8"), "text/html; charset=utf-8")
        if path == "/console":
            return await self._send(send, 200, INDEX_HTML.encode("utf-8"), "text/html; charset=utf-8")
        if path.startswith("/static/"):
            return await self._serve_static(path[len("/static/") :], send)
        if path == "/graphql":
            if method == "OPTIONS":
                return await self._send(send, 204, b"", "text/plain")
            try:
                query, variables = await self._read_request(scope, receive, method)
                result = schema.execute_sync(query, variable_values=variables)
                payload: dict = {"data": result.data}
                if result.errors:
                    payload["errors"] = [{"message": err.message} for err in result.errors]
                return await self._send(
                    send, 200, json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8"),
                    "application/json; charset=utf-8",
                )
            except Exception as exc:  # pragma: no cover - defensive
                payload = {"errors": [{"message": f"{type(exc).__name__}: {exc}"}]}
                return await self._send(
                    send, 400, json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                    "application/json; charset=utf-8",
                )
        await self._send(send, 404, b'{"errors":[{"message":"not found"}]}', "application/json")

    async def _serve_static(self, name: str, send) -> None:
        content_type = STATIC_TYPES.get(name)
        path = WEB_DIR / name
        if content_type is None or not path.is_file():
            return await self._send(send, 404, b"not found", "text/plain; charset=utf-8")
        data = path.read_bytes()
        return await self._send(send, 200, data, content_type)

    @staticmethod
    async def _read_request(scope, receive, method: str) -> tuple[str, dict | None]:
        if method == "GET":
            params = parse_qs(scope.get("query_string", b"").decode("utf-8"))
            query = params.get("query", [""])[0]
            variables = json.loads(params.get("variables", ["null"])[0] or "null")
            return query, variables
        body = b""
        while True:
            message = await receive()
            body += message.get("body", b"")
            if not message.get("more_body", False):
                break
        data = json.loads(body.decode("utf-8") or "{}")
        return data.get("query", ""), data.get("variables")

    @staticmethod
    async def _send(send, status: int, body: bytes, content_type: str) -> None:
        await send(
            {
                "type": "http.response.start",
                "status": status,
                "headers": [
                    (b"content-type", content_type.encode("ascii")),
                    (b"content-length", str(len(body)).encode("ascii")),
                    (b"cache-control", b"no-store"),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})
