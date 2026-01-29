# Module Registry

A single recall surface for all tools, capabilities, and modules. Nothing is a bolt-on if it's recallable in one place.

## Principle

> If you can **see it**, **name it**, **retrieve it**, and **park it** — it stops living in your head.

## Structure

```
module-registry/
├── dev/
│   └── modules.json      # Draft and experimental modules
├── prod/
│   └── modules.json      # Stable modules (read by UI)
├── schemas/
│   └── module.schema.json
├── scripts/
│   ├── validate.py       # Schema and business rule validation
│   ├── promote.py        # Dev → Prod promotion with audit
│   └── diff.py           # Compare dev vs prod
├── pipeline.yaml         # Pipeline configuration
├── audit.log             # Promotion and validation history
└── README.md
```

## Module Schema (5 Fields Only)

| Field       | Type              | Description                          |
|-------------|-------------------|--------------------------------------|
| `name`      | string (1-64)     | Short, boring, recallable name       |
| `purpose`   | string (1-128)    | What it does in one line             |
| `applies_to`| array of strings  | Contexts: Cooperative, Community, Municipal, Personal, Enterprise, All |
| `status`    | enum              | Draft, Active, Parked, Deprecated    |
| `last_used` | date or null      | ISO 8601 date of last use            |

## Workflow

```
1. Edit dev/modules.json
2. Validate: python3 scripts/validate.py dev/modules.json dev
3. Diff:     python3 scripts/diff.py
4. Promote:  python3 scripts/promote.py
5. Commit to Git
```

## Commands

### Validate Dev
```bash
python3 scripts/validate.py dev/modules.json dev
```

### Validate Prod
```bash
python3 scripts/validate.py prod/modules.json prod
```

### Show Diff (What Would Change)
```bash
python3 scripts/diff.py
```

### Promote Dev → Prod
```bash
python3 scripts/promote.py
```

## Rules

1. **Draft modules stay in dev** — they are not promoted to prod
2. **Prod is read-only** — UI reads from prod, edits happen in dev
3. **All promotions are audited** — see `audit.log`
4. **No duplicate names** — validation will fail
5. **No extra fields** — schema is strict

## Status Lifecycle

```
Draft → Active → Parked → Deprecated
         ↑         ↓
         └─────────┘
```

- **Draft**: Work in progress, not visible in prod
- **Active**: In use, visible in UI dropdown
- **Parked**: Valid but not currently needed
- **Deprecated**: Scheduled for removal

## Integration

The UI reads `prod/modules.json` directly. The dropdown displays:

```
[ Modules ▾ ]
  ├── Governance Diagnostic
  ├── Legal Check
  ├── FX Converter
  └── Health Protocol
```

Filter by:
- Status (Active / Parked)
- Applies to (Coop / Community / Municipal)
- Purpose (search the one-liner)

## Git Workflow

```bash
# After making changes
cd module-registry
python3 scripts/validate.py dev/modules.json dev
python3 scripts/diff.py
python3 scripts/promote.py
git add .
git commit -m "Module registry update"
git push
```
