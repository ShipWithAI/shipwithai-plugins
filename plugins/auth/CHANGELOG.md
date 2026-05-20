# Changelog — shipwithai-auth

All notable changes to this plugin are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.0.0] — 2026-04-26

### Added
- `auth-setup`: Set up production-ready auth for Next.js apps with Better Auth and Firebase Auth
  - Email/password authentication
  - Google OAuth social login
  - Session management and middleware
  - UI components (login, register, forgot password)
  - Auto-detects existing Tailwind/shadcn themes
  - Provider README with full config steps
- `auth-doctor`: Diagnose and fix issues in existing auth setups
  - Scans environment variables, config files, security patterns
  - Checks middleware, OAuth, database, and dangerous code patterns
  - Produces scored health report with actionable fixes