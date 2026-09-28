// Static file server: pages from public/ (built by build_site.py), images from images/.
const http = require("http");
const fs = require("fs");
const path = require("path");

const PORT = process.env.PORT || 3000;
const PUBLIC = path.join(__dirname, "public");
const IMAGES = path.join(__dirname, "images");
const TYPES = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".webp": "image/webp",
  ".txt": "text/plain; charset=utf-8",
  ".xml": "application/xml; charset=utf-8",
  ".svg": "image/svg+xml",
};

function resolve(p) {
  if (p.startsWith("/images/")) return path.join(IMAGES, p.slice("/images/".length));
  return path.join(PUBLIC, p.endsWith("/") ? p + "index.html" : p);
}

function send(req, res, file, status, st) {
  const ext = path.extname(file);
  res.writeHead(status, {
    "Content-Type": TYPES[ext] || "application/octet-stream",
    "Content-Length": st.size,
    "Cache-Control": ext === ".html" ? "public, max-age=300" : "public, max-age=86400",
  });
  if (req.method === "HEAD") return res.end();
  fs.createReadStream(file).pipe(res);
}

function notFound(req, res) {
  const file = path.join(PUBLIC, "404.html");
  fs.stat(file, (err, st) => {
    if (!err) return send(req, res, file, 404, st);
    res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
    res.end("Not found");
  });
}

http.createServer((req, res) => {
  let p;
  try { p = decodeURIComponent(new URL(req.url, "http://x").pathname); } catch { return notFound(req, res); }
  if (p.includes("\0") || p.split("/").includes("..")) return notFound(req, res);
  const file = resolve(p);
  if (!file.startsWith(PUBLIC + path.sep) && !file.startsWith(IMAGES + path.sep)) return notFound(req, res);
  fs.stat(file, (err, st) => {
    if (!err && st.isFile()) return send(req, res, file, 200, st);
    // /prompt/slug -> /prompt/slug/ when that directory has an index page
    if (!p.endsWith("/") && !path.extname(p)) {
      return fs.stat(path.join(PUBLIC, p, "index.html"), (e2, s2) => {
        if (e2 || !s2.isFile()) return notFound(req, res);
        const qs = req.url.includes("?") ? req.url.slice(req.url.indexOf("?")) : "";
        res.writeHead(301, { Location: p + "/" + qs });
        res.end();
      });
    }
    notFound(req, res);
  });
}).listen(PORT, "0.0.0.0", () => console.log(`listening on ${PORT}`));
