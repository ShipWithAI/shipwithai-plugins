# Marketplace version truth

What `.claude-plugin/marketplace.json` *claims* each plugin's version is, against
what that plugin's own manifest *actually* says.

This is a **report, not a correction**. No version in `marketplace.json` was
bumped to produce it. A `version` in the registry is a release claim about the
plugin it names, and bumping it is a release act that belongs to whoever owns
that plugin — not to the reconciliation that produced this file. The point of
writing the drift down is to turn the next bump from a discovery into a
decision.

---

## Measured 2026-08-09

Measured on branch `chore/reconcile-marketplace` (merge commit `28989b4`, the
six-plugin union of `develop` and `feat/absorb-mangalahq-marketplace`). Every
number below was read this session from the file named in its row.

| Entry | Registry claims | Plugin manifest says | Verdict |
|---|---|---|---|
| `shipwithai-auth` | `1.7.1` | `1.7.1` | **matching** |
| `shipwithai-design-toolkit` | `0.7.3` | `0.41.0` (see below) | **registry behind the plugin**, by a wide margin |
| `shipwithai-harness` | `2.0.0` | `2.0.0` | **matching** |
| `shipwithai-java-backend-toolkit` | `0.1.0` | `0.5.0` | **registry behind the plugin** |
| `shipwithai-mobile-ui-harness` | `0.1.0` | `0.1.0` | **matching** |
| `shipwithai-starter` | `1.0.0` | `2.4.0` | **registry behind the plugin** |

No row is *ahead* of its plugin: where the registry disagrees, it is always the
stale side. Three of six entries are stale.

**Where each "plugin manifest says" number came from.** For the five path-source
entries, `plugins/<dir>/.claude-plugin/plugin.json` on this branch:

- `plugins/auth/.claude-plugin/plugin.json`
- `plugins/harness/.claude-plugin/plugin.json`
- `plugins/java-backend-toolkit/.claude-plugin/plugin.json`
- `plugins/mobile-ui-harness/.claude-plugin/plugin.json`
- `plugins/starter/.claude-plugin/plugin.json`

### `shipwithai-design-toolkit` — measured from a sibling checkout

This entry is **not** vendored under `plugins/`. Its source is the github object
`{"source":"github","repo":"MangalaHQ/shipwithai-design-toolkit"}`, so its real
version cannot be read from this repository at all. The number above was read
from a separate clone on this machine:

- Checkout: `../shipwithai-design-toolkit`
  (`/Users/ethanai/Data/WorkspaceSWA/shipwithai-design-toolkit`)
- Remote: `git@github.com:MangalaHQ/shipwithai-design-toolkit.git` — the same
  repo the registry entry points at.
- `origin/master` (`4b9139d`, the remote default branch) → **`0.41.0`**
- `origin/develop` (`bf7fdc2`) → `0.41.0`
- That checkout's working tree is parked on an unrelated feature branch,
  `loop/install-contracts-w-fp` (`2bc9929`), whose `plugin.json` reads `0.35.0`.

The table uses `0.41.0` because `origin/master` is that repo's default branch and
therefore the closest thing to its released version. **Both numbers carry
staleness risk**: they are only as fresh as the last `git fetch` of a sibling
clone, and neither is a published-release check. Anyone acting on this row
should re-read the upstream repo rather than trusting this file.

### A third, disagreeing claim inside `plugins/auth`

`plugins/auth/.claude-plugin/marketplace.json` is a nested registry that arrived
with the MangalaHQ absorption. It claims `shipwithai-auth@1.7.0` — disagreeing
with both the root registry (`1.7.1`) and the plugin's own manifest (`1.7.1`).
`plugins/harness/.claude-plugin/marketplace.json` claims
`shipwithai-harness@2.0.0`, which agrees with both.

Recorded, not touched. Whether those nested files should exist in a monorepo
that already has a root registry is a question for the plugin owners.

---

## How to re-measure

```sh
jq -r '.plugins[] | "\(.name)\t\(.version)\t\(.source|tostring)"' \
  .claude-plugin/marketplace.json |
while IFS=$'\t' read -r name claim source; do
  case "$source" in
    ./plugins/*) disk=$(jq -r '.version // "NO version FIELD"' \
                    "${source#./}/.claude-plugin/plugin.json" 2>/dev/null \
                    || echo "NOT MEASURED") ;;
    *)           disk="(non-path source — read the upstream repo)" ;;
  esac
  printf '%-38s claim=%-8s disk=%s\n' "$name" "$claim" "$disk"
done
```

Rules for updating this file: every number in it must be one you measured
yourself, and dated. If a plugin's real version cannot be read — missing
checkout, unreadable or absent manifest — write `NOT MEASURED` and why. Never
infer a version from a changelog, a tag, or a neighbouring number.
