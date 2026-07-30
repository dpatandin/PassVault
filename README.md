# PassVault

**PassVault** is a self-hosted, minimalist, zero-knowledge
[pastebin](https://en.wikipedia.org/wiki/Pastebin). Data is encrypted and
decrypted **in the browser** using 256-bit AES in
[Galois Counter mode](https://en.wikipedia.org/wiki/Galois/Counter_Mode) — the
server only ever stores ciphertext and has no way to read your content.

PassVault is a lightly customized fork of
[PrivateBin](https://github.com/PrivateBin/PrivateBin) (itself a fork of ZeroBin
by [Sébastien Sauvage](https://github.com/sebsauvage/ZeroBin)), rebranded and
tuned for a specific deployment. See [Relationship to PrivateBin](#relationship-to-privatebin).

## Current state

| | |
|---|---|
| Upstream base | PrivateBin **2.0.5** |
| Runtime | **PHP 8.4** (FrankenPHP) |
| Front-end template | **Bootstrap 5** |
| Storage | Filesystem (`/app/data`, persistent volume) |
| Hosting | [Railway](https://railway.app) via [Railpack](https://railpack.com) + FrankenPHP/Caddy |
| Language | English only |

## Features (as configured)

- End-to-end encrypted documents; the server has zero knowledge of content.
- **Password protection** for documents (optional per document).
- **Burn-after-reading** (preselected by default).
- **Expiry** options: 1 hour, 1 day, **3 days**, 1 week (default: 1 week).
- Formats: Plain Text, Source Code (syntax highlighting), Markdown (with preview).
- QR code and e-mail sharing of document links.
- Rate limiting (10 s between posts per IP).

Disabled in this instance: discussions/comments, file uploads, language
selection, compression, and the URL shortener.

## Security

- Served over **HTTPS** with **HSTS** (`Strict-Transport-Security`).
- Strict **Content-Security-Policy** (`default-src 'none'`, `script-src 'self'`,
  `frame-ancestors 'none'`, sandboxed), `X-Frame-Options: deny`,
  `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`,
  `Secure` + `SameSite=Lax` cookies.
- A custom `Caddyfile` returns **404** for source/metadata paths
  (`*.md`, `composer.*`, `/vendor/*`, `/bin/*`, `/tst/*`, `/cfg/*`, …), since
  Caddy does not honor PrivateBin's `.htaccess` protections.
- Runs a current, supported PHP (8.4) and PrivateBin (2.0.5, which fixes
  CVE-2026-55891).

## Configuration

Runtime configuration lives in `cfg/conf.php`. Because Railpack/FrankenPHP's
working directory is not the app root, the config is located via the
**`CONFIG_PATH=/app/cfg`** environment variable (set in Railway), and the data
directory is pinned to the mounted volume with `dir = "/app/data"`.

Full reference: the [PrivateBin configuration
wiki](https://github.com/PrivateBin/PrivateBin/wiki/Configuration).

## Deployment

The Railway service auto-deploys on push to `master`:

```bash
git push origin master
```

Railpack detects PHP from `composer.json`, runs `composer install`, and serves
the app with FrankenPHP using the repository's custom `/Caddyfile`.

Notes for maintainers:
- **PHP version** is pinned in `composer.json` (`require.php` + `config.platform.php`)
  and `composer.lock` (`platform-overrides`). Use a single constraint like
  `^8.4` — Railpack's resolver cannot handle `||` (OR) constraints.
- The persistent data volume is mounted at `/app/data`; documents survive
  redeploys. Existing PrivateBin filesystem data is read as-is (no migration).

## Editing bundled assets (important)

Every bundled `js/` (and `css/`) file has a **Subresource Integrity** hash in
`lib/Configuration.php`. If you edit an asset without updating its hash, the
browser silently refuses to load the script and the app hangs on *"Loading…"*.
After changing any asset, regenerate the hashes:

```bash
python3 bin/update-sri.py          # rewrite stale hashes
python3 bin/update-sri.py --check  # verify (non-zero exit if stale) — good for CI
```

## Relationship to PrivateBin

PassVault tracks upstream PrivateBin and re-applies a small set of
customizations on upgrade:

- **Branding** — name "PassVault", rebranded icons/favicons, `manifest.json`;
  footer version number, tagline and info text removed.
- **Custom theme** — `css/bootstrap5/passvault.css` (smaller 14px base, monospace
  editor surface, tighter toolbar, soft theme-aware borders), linked from
  `tpl/bootstrap5.php` after `privatebin.css`.
- **Custom 3-day expiry** — a rewritten `Helper.durationToSeconds` in
  `js/privatebin.js` that parses plural units (so the `3days` expiry key works).
- **Asset cache-busting** — `lib/View.php` appends the file mtime to
  non-versioned assets so edits reload reliably.
- **Deployment glue** — `/Caddyfile` (HSTS + path blocking), `bin/update-sri.py`,
  PHP version pin, `robots.txt` opt-out of the public directory.
- **Trimmed** — English-only i18n; `symfony/polyfill-php80` dropped (inert on
  PHP 8+).

To upgrade the upstream base, re-base on a clean PrivateBin release and re-apply
the items above, then regenerate SRI hashes and redeploy.

## Credits & license

PassVault is built on [PrivateBin](https://github.com/PrivateBin/PrivateBin).
All credit for the underlying zero-knowledge pastebin design and implementation
goes to the PrivateBin authors and contributors. Distributed under the
[zlib/libpng license](LICENSE.md), the same license as PrivateBin.
