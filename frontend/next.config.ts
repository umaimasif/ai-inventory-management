import type { NextConfig } from "next";

// The production build is a static export: every route in this app is a client
// component that fetches from the API at runtime, so there is nothing to render
// on a server. FastAPI serves the exported files and the API from one origin
// (see backend/app/main.py `_mount_frontend`), which also removes CORS from the
// deployed setup entirely.
//
// `next dev` is unaffected — this only shapes `next build`.
const nextConfig: NextConfig = {
  output: "export",

  // Emit `/dashboard/index.html` instead of `/dashboard.html`, so a plain static
  // file server (Starlette's StaticFiles with html=True) resolves /dashboard/.
  trailingSlash: true,

  // ...but do NOT emit the automatic "add a trailing slash" redirect. On Vercel
  // that redirect also matches /api/*, so /api/health 308s to /api/health/,
  // which FastAPI then 307s back to /api/health — an infinite loop that makes
  // the whole API unreachable. Skipping the redirect keeps the file layout
  // above while letting /api/* reach the Python function untouched.
  skipTrailingSlashRedirect: true,

  // No image optimizer exists in a static export.
  images: { unoptimized: true },
};

export default nextConfig;
