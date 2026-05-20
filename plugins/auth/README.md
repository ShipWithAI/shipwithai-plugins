# shipwithai-auth

**Production-ready authentication for your Next.js app — in under 45 minutes.**

[![License](https://img.shields.io/badge/license-MIT-blue)](https://github.com/ShipWithAI/shipwithai-plugins/blob/main/LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.0-green)](https://shipwithai.io/plugins/auth)
[![Plugin](https://img.shields.io/badge/claude%20code-plugin-blueviolet)](https://shipwithai.io)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)](https://github.com/ShipWithAI/shipwithai-plugins/issues)

[📖 Docs](https://shipwithai.io/plugins/auth) · [🐛 Report Bug](https://github.com/ShipWithAI/shipwithai-plugins/issues) · [💡 Request Feature](https://github.com/ShipWithAI/shipwithai-plugins/issues)

---

## What It Does

A Claude Code plugin with two skills:

- **`/shipwithai-auth:setup`** — Interactive wizard that installs your auth stack end-to-end: packages, config, database schema, middleware, UI pages, and a provider README with every env var sourced.
- **`/shipwithai-auth:doctor`** — Scans an existing auth setup across 22 checks (env vars, file structure, security, middleware, OAuth, database, dangerous code patterns). Produces a scored health report with actionable fixes.

No more reading three different docs and copy-pasting config snippets. One command, everything wired.

## Why This Plugin

**Zero boilerplate.** Login, register, forgot-password, reset-password, profile, and protected layout — all generated. UI components use your existing shadcn/ui theme or auto-select a preset if you're starting fresh.

**Battle-tested.** 61 production pitfalls documented and actively checked: module-scope SDK instantiation, wrong middleware patterns per provider, missing Suspense wrappers, CSRF misconfigs, and more. `/auth:doctor` catches them before they reach production.

**Your choice of provider.** Better Auth for full control and self-hosting. Firebase Auth for the Google ecosystem and mobile/KMP apps. The setup wizard detects your existing stack and adapts — it won't overwrite files without asking.

## Install

```bash
claude --plugin-dir ./shipwithai-auth
```

Then run the wizard:

```bash
/shipwithai-auth:setup
```

Or just describe what you need in chat:

```
> Set up Firebase Auth with Google login for my Next.js app
```

Claude uses the `auth-setup` skill automatically.

## Providers

| Provider | Cost | Best For | Status |
|----------|------|----------|--------|
| Better Auth | Free forever | Self-hosted, full control, no vendor lock-in | **Supported** |
| Firebase Auth | Free < 50K MAU | Google ecosystem, mobile + web (KMP) | **Supported** |
| Clerk | Free < 10K MAU | Fastest setup, pre-built UI | Coming soon |
| Auth.js | Free forever | Lightweight, educational | Coming soon |
| Supabase Auth | Free < 50K MAU | Postgres-native, row-level security | Coming soon |

Not sure which to pick? Run `/shipwithai-auth:setup` — the wizard walks you through it based on your project's needs.

## What Gets Generated

For each provider, setup generates the complete auth layer:

| What | Details |
|------|---------|
| **Config files** | Auth server, auth client, database adapter, env vars |
| **API routes** | Session endpoint with rate limiting and CSRF protection |
| **Middleware** | Route protection with the correct pattern for your provider |
| **Database schema** | Drizzle, Prisma, or Supabase SQL |
| **UI pages** | Login, register, forgot password, reset password, user profile |
| **Protected layout** | Server-side session verification on every protected route |
| **Provider README** | Step-by-step console setup, env var sources, pitfall cross-references |

## Supported Stack

- **Framework**: Next.js 14+ with App Router (Next.js 15 supported)
- **UI**: shadcn/ui + Tailwind CSS — auto-detects your existing theme
- **ORM**: Drizzle, Prisma, or Supabase SQL
- **Email**: Resend (recommended) or console logging for development
- **OAuth**: Google sign-in (GitHub and Apple coming soon)

## File Structure

```
shipwithai-auth/
├── .claude-plugin/plugin.json       # Plugin metadata
├── skills/
│   ├── auth-setup/
│   │   ├── SKILL.md                 # Setup wizard logic + provider decision framework
│   │   ├── references/              # Per-provider guides (Better Auth, Firebase, OAuth, pitfalls)
│   │   └── assets/                  # UI components, schemas, configs, themes
│   └── auth-doctor/
│       └── SKILL.md                 # Diagnostic logic — 8 categories, 22 checks
├── commands/
│   ├── setup.md                     # /shipwithai-auth:setup
│   └── doctor.md                    # /shipwithai-auth:doctor
└── README.md
```

## Roadmap

- [x] Better Auth — email/password, Google OAuth, Drizzle/Prisma schemas
- [x] Firebase Auth — email/password, Google OAuth, session cookies
- [x] Auth Doctor — 22-check health scan with auto-fix
- [x] Theme detection — Ocean/Sunrise presets, inherit from parent project
- [ ] Clerk support
- [ ] Auth.js / NextAuth v5 support
- [ ] Supabase Auth support
- [ ] GitHub OAuth
- [ ] Apple OAuth
- [ ] `/shipwithai-auth:add-oauth` — add social login to an existing setup

## Contributing

See [CLAUDE.md](https://github.com/ShipWithAI/shipwithai-plugins/blob/main/CLAUDE.md) for conventions and blueprint references. Before starting:

```bash
cp CLAUDE.local.md.example CLAUDE.local.md  # set your blueprint_path
```

New here? Check [open issues](https://github.com/ShipWithAI/shipwithai-plugins/issues) to find something to work on.

## Links

- Website: [shipwithai.io](https://shipwithai.io)
- Plugin page: [shipwithai.io/plugins/auth](https://shipwithai.io/plugins/auth)
- Author: Ethan (truongnguyenptit@gmail.com)

## License

MIT — see [LICENSE](https://github.com/ShipWithAI/shipwithai-plugins/blob/main/LICENSE).