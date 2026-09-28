// Minimal static file server for the generated site (index.html, prompts.html, images/).
const http = require("http");
const fs = require("fs");
const path = require("path");

const PORT = process.env.PORT || 3000;
const ROOT = __dirname;
const PUBLIC = new Set(["/index.html", "/prompts.html", "/robots.txt", "/sitemap.xml"]);
const TYPES = {
  ".html": "text/html; charset=utf-8",
  ".webp": "image/webp",
  ".txt": "text/plain; charset=utf-8",
  ".xml": "application/xml; charset=utf-8",
};

http.createServer((req, res) => {
  let p;
  try { p = decodeURIComponent(new URL(req.url, "http://x").pathname); } catch { p = "/"; }
  if (p === "/") p = "/index.html";
  const ok = PUBLIC.has(p) || (p.startsWith("/images/") && !p.includes(".."));
  const file = path.join(ROOT, p);
  if (!ok || !file.startsWith(ROOT)) return notFound(res);
  fs.stat(file, (err, st) => {
    if (err || !st.isFile()) return notFound(res);
    const ext = path.extname(file);
    res.writeHead(200, {
      "Content-Type": TYPES[ext] || "application/octet-stream",
      "Content-Length": st.size,
      "Cache-Control": ext === ".webp" ? "public, max-age=2592000, immutable" : "public, max-age=300",
    });
    if (req.method === "HEAD") return res.end();
    fs.createReadStream(file).pipe(res);
  });
}).listen(PORT, "0.0.0.0", () => console.log(`listening on ${PORT}`));

function notFound(res) {
  res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
  res.end("Not found");
}
