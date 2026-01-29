# Registro de Módulos / Module Registry

**ES:** Una superficie de recuperación única para todas las herramientas, capacidades y módulos.  
**EN:** A single recall surface for all tools, capabilities, and modules.

---

## Principio / Principle

> **ES:** Si puedes **verlo**, **nombrarlo**, **recuperarlo** y **aparcarlo** — deja de vivir en tu cabeza.  
> **EN:** If you can **see it**, **name it**, **retrieve it**, and **park it** — it stops living in your head.

---

## Estructura / Structure

```
module-registry/
├── dev/
│   ├── modules.json           # English-only (legacy)
│   └── modulos_BILINGUAL.json # Bilingual (ES/EN)
├── prod/
│   └── modules.json           # Production registry
├── schemas/
│   ├── module.schema.json     # English schema
│   └── modulo.schema.json     # Bilingual schema
├── scripts/
│   ├── validate.py
│   ├── promote.py
│   └── diff.py
├── docs/
│   └── BILINGUAL_STANDARD.md  # Documentation standard
├── pipeline.yaml
├── audit.log
└── README_BILINGUAL.md
```

---

## Esquema de Módulo / Module Schema

### Campos / Fields

| Campo ES | Campo EN | Tipo | Descripción |
|----------|----------|------|-------------|
| `nombre` | `name` | string | Nombre corto / Short name |
| `proposito` | `purpose` | string | Qué hace / What it does |
| `aplica_a` | `applies_to` | array | Contextos / Contexts |
| `estado` | `status` | enum | Estado / Status |
| `ultimo_uso` | `last_used` | date | Último uso / Last used |

### Estados / Status

| ES | EN |
|----|-----|
| Borrador | Draft |
| Activo | Active |
| Aparcado | Parked |
| Obsoleto | Deprecated |

### Contextos / Applies To

| ES | EN |
|----|-----|
| Cooperativa | Cooperative |
| Comunidad | Community |
| Municipal | Municipal |
| Personal | Personal |
| Empresa | Enterprise |
| Todos | All |

---

## Flujo de Trabajo / Workflow

```bash
# 1. Editar / Edit
vim dev/modulos_BILINGUAL.json

# 2. Validar / Validate
python3 scripts/validate.py dev/modulos_BILINGUAL.json dev

# 3. Comparar / Diff
python3 scripts/diff.py

# 4. Promover / Promote
python3 scripts/promote.py

# 5. Confirmar / Commit
git add . && git commit -m "Actualización de módulos / Module update" && git push
```

---

## Reglas / Rules

1. **ES:** Los módulos en borrador permanecen en dev — no se promueven a prod  
   **EN:** Draft modules stay in dev — they are not promoted to prod

2. **ES:** Prod es solo lectura — la UI lee de prod, las ediciones ocurren en dev  
   **EN:** Prod is read-only — UI reads from prod, edits happen in dev

3. **ES:** Todas las promociones se auditan — ver `audit.log`  
   **EN:** All promotions are audited — see `audit.log`

4. **ES:** Sin nombres duplicados — la validación fallará  
   **EN:** No duplicate names — validation will fail

5. **ES:** Sin campos extra — el esquema es estricto  
   **EN:** No extra fields — schema is strict

---

## Regla de Oro / Golden Rule

> **ES:** Si va a una cooperativa canaria, va en español primero.  
> **EN:** If it goes to a Canary Islands cooperative, it goes in Spanish first.
