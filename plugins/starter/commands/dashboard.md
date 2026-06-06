---
name: dashboard
description: >
  Show harness health across all projects on this machine.
  Scans for .claude/starter-context.json files and produces an aggregate report.
  Trigger phrases: "harness dashboard", "all projects health", "show all harnesses".
argument-hint: "[--path ~/code]"
---

# /dashboard

Scan for projects with a configured Claude Code harness and show aggregate health.

## Steps

### Step 1 — Find projects

Default search paths (in order):
1. `--path` argument if provided
2. Current directory's parent (e.g. if in `~/code/my-app`, scan `~/code/`)
3. `~/` as fallback — warn user this may be slow before scanning

Find command:
```bash
find <search_path> -maxdepth 4 -name "starter-context.json" -path "*/.claude/*" 2>/dev/null
```

If no projects found: "No harness-configured projects found in [search_path]. Run /shipwithai-starter:init in a project first."

### Step 2 — Collect health per project

For each found `starter-context.json`, read-only quick scan:

1. Read `version`, `tier`, `project.name` from the file
2. Check `CLAUDE.md` exists in the project root → populated / has-placeholder / missing
3. Count missing expected files for that tier:
   - All tiers: `.claude/settings.json`
   - Standard+: `.mcp.json`
   - Full: `docs/architecture.md`
4. Note `starter-context.json` last modified date

Health score = count of missing expected files for that tier:
- `0` missing → ✅ OK
- `1–2` missing → ⚠️ [count]
- `3+` missing → ❌ [count]

### Step 3 — Output table

```
## Harness Dashboard
Scanned: YYYY-MM-DD | [N] projects found in [search_path]

| Project          | Tier     | Schema  | Health | Last updated |
|------------------|----------|---------|--------|--------------|
| acme-api         | Standard | ✅ v1.2 | ✅ OK  | 3 days ago   |
| my-saas          | Full     | ⚠️ v1.1 | ⚠️ 1   | today        |
| old-project      | Essential| ⚠️ v1.0 | ❌ 3   | 45 days ago  |

[N] healthy, [M] need attention.
→ Run /shipwithai-starter:review in [project with most missing files] for details.
```

Schema status: ✅ if version == "1.2", ⚠️ with version shown if outdated.

## Failure Modes

- Don't scan `/` or `/usr` — only user home and explicitly provided paths
- Don't run full review per project — dashboard is read-only, quick scan only
- Don't modify any files
- Don't show projects outside the search path
- Warn before scanning `~/` (may be slow on large home directories)
