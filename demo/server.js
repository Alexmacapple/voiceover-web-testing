// Serveur sans dépendance pour la page de connexion d’exemple.
// Lancer : node demo/server.js, puis ouvrir http://127.0.0.1:8080/sign-in
const http = require("node:http");
const fs = require("node:fs/promises");
const path = require("node:path");

const port = Number(process.env.PORT) || 8080;

// Chemins que les scénarios peuvent visiter, avec le fichier servi pour chacun.
const pages = {
  "/sign-in": "sign-in.html",
};

// Fichiers statiques (polices) servis sur /assets depuis demo/assets, non fourni.
const assetsDir = path.join(__dirname, "assets");
const assetTypes = {
  ".woff2": "font/woff2",
  ".svg": "image/svg+xml",
  ".css": "text/css; charset=utf-8",
};

const server = http.createServer(async (req, res) => {
  const { pathname } = new URL(req.url, `http://localhost:${port}`);

  if (pathname === "/") {
    res.writeHead(302, { Location: "/sign-in" });
    res.end();
    return;
  }

  if (pathname.startsWith("/assets/")) {
    const filePath = path.join(assetsDir, pathname.slice("/assets/".length));
    const type = assetTypes[path.extname(filePath)];
    // Refuser tout chemin hors du dossier assets ou tout type inconnu.
    if (!filePath.startsWith(assetsDir + path.sep) || !type) {
      res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
      res.end("Introuvable");
      return;
    }
    try {
      const body = await fs.readFile(filePath);
      res.writeHead(200, {
        "Content-Type": type,
        "Cache-Control": "public, max-age=31536000, immutable",
      });
      res.end(body);
    } catch {
      res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
      res.end("Introuvable");
    }
    return;
  }

  // Servir GET et POST de la même façon : sans JavaScript, l’envoi du
  // formulaire réaffiche la page au lieu d’une erreur 404.
  const file = pages[pathname.replace(/\/+$/, "")];
  if (!file) {
    res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
    res.end("Introuvable");
    return;
  }

  const html = await fs.readFile(path.join(__dirname, file));
  res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
  res.end(html);
});

// Écoute locale uniquement : la page n’est pas exposée au réseau.
server.listen(port, "127.0.0.1", () => {
  console.log(`Application d’exemple disponible sur http://127.0.0.1:${port}/sign-in`);
});
