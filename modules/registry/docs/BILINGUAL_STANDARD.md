# Estándar de Documentación Bilingüe / Bilingual Documentation Standard

**Contexto / Context:** Islas Canarias, España / Canary Islands, Spain  
**Idioma primario / Primary language:** Español (ES)  
**Idioma secundario / Secondary language:** English (EN)

---

## Principios / Principles

### ES — Español Primero
1. **El español es el idioma de trabajo.** Todos los documentos oficiales, comunicaciones con cooperativas y autoridades locales se redactan primero en español.
2. **El inglés es para referencia interna.** Se utiliza para documentación técnica, código y comunicación con sistemas externos.
3. **Consistencia sobre perfección.** Es mejor un documento bilingüe imperfecto que uno monolingüe perfecto.

### EN — English Second
1. **Spanish is the working language.** All official documents, communications with cooperatives and local authorities are drafted first in Spanish.
2. **English is for internal reference.** Used for technical documentation, code, and communication with external systems.
3. **Consistency over perfection.** A flawed bilingual document is better than a perfect monolingual one.

---

## Estructura de Archivos / File Structure

```
documento_ES.md          ← Versión principal (español)
documento_EN.md          ← Versión traducida (inglés)
documento_BILINGUAL.md   ← Versión combinada (ambos idiomas)
```

### Convención de Nombres / Naming Convention

| Tipo | Formato | Ejemplo |
|------|---------|---------|
| Solo español | `nombre_ES.md` | `hoja_intencion_ES.md` |
| Solo inglés | `nombre_EN.md` | `intent_sheet_EN.md` |
| Bilingüe | `nombre_BILINGUAL.md` | `governance_diagnostic_BILINGUAL.md` |
| Código/Config | Sin sufijo (inglés por defecto) | `validate.py`, `config.yaml` |

---

## Formato de Documento Bilingüe / Bilingual Document Format

```markdown
# Título en Español / Title in English

## Sección / Section

**ES:**
Contenido en español aquí.

**EN:**
English content here.

---
```

### Ejemplo / Example

```markdown
# Diagnóstico de Gobernanza / Governance Diagnostic

## Propósito / Purpose

**ES:**
Mapear la autoridad de decisión y el riesgo en estructuras de gobernanza.

**EN:**
Map decision authority and risk across governance structures.

---
```

---

## Campos del Registro de Módulos / Module Registry Fields

| Campo ES | Campo EN | Descripción |
|----------|----------|-------------|
| `nombre` | `name` | Nombre corto y recordable |
| `proposito` | `purpose` | Qué hace en una línea |
| `aplica_a` | `applies_to` | Contextos relevantes |
| `estado` | `status` | Borrador, Activo, Aparcado, Obsoleto |
| `ultimo_uso` | `last_used` | Fecha ISO del último uso |

### Estados / Status Values

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

## Prioridad de Traducción / Translation Priority

1. **Alta / High:** Documentos externos (cooperativas, autoridades)
2. **Media / Medium:** Documentación de usuario, guías
3. **Baja / Low:** Código, configuración, logs internos

---

## Herramientas / Tools

- **Traducción:** Manual para documentos críticos, asistida por IA para borradores
- **Validación:** Revisión humana obligatoria para comunicaciones externas
- **Almacenamiento:** Ambas versiones en el mismo directorio, versionadas en Git

---

## Regla de Oro / Golden Rule

> **Si va a una cooperativa canaria, va en español primero.**  
> **If it goes to a Canary Islands cooperative, it goes in Spanish first.**
