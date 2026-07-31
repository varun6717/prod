# cache/ — mutable build state (never published, never frozen)

**Why this exists (D-A22).** The retired `onboarding_manifest.yaml` mixed a frozen registry
artifact with mutable build records (`repos[]` — `content_hash`, `last_built`): every map build
wanted to dirty a SHA-pinned file. Build state now lives here, **outside** the registry —
`registry_manifest.yaml` never includes `cache/`, and everything under this directory except
this README is gitignored.

## `cache/code_maps/index.yaml` — the 4-branch gate's lookup (D-A21, TASK-115)

One record per repo build. Contract (normative shape lands with TASK-115):

```yaml
repos:
  - repo: <name>                # e.g. merchant-routing-svc
    seal_id: <SEAL id>
    commit_sha: <sha>           # map-validity key, part 1
    profile_sha: <sha>          # map-validity key, part 2 (code_profiles/<repo>.profile.yaml)
    built_with_extractor_sha: <sha>
    map_dir: <path>             # the built code_map/{components,files}.json
    last_built: <iso8601>
```

Gate branches (§5.3 as amended): **1 onboard** (no profile) · **2 reuse** (both shas match —
no work) · **3 incremental** (commit moved — re-purpose changed files only) · **4 full
rebuild** (`profile_sha` changed). Per-file purpose cache is keyed on file **content hash**
and lives beside the map under `cache/code_maps/`.

The pre-pivot build record (the old `repos[]` entry for `merchant-routing-svc` @ `e94c70d`)
was **not** migrated: it describes a tagged, pre-profile map that no longer validates —
carrying it over would fake a cache hit. Git history (`add5aca^`) preserves it.
