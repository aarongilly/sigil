This is a Repo for development on my Simple Interchange Grammar for Identity and Linking. 

It's an idea. We'll see if anything interesting comes of it.

---

> [!tldr] A homegrown system for organizing information

# SIGIL – Simple Interchange Grammar for Identity and Linking

**An interoperability substrate for small information systems.**

SIGIL gives things persistent identity and a small vocabulary for describing their data and relationships. It requires no universal database, ontology, or application.

SIGIL [on an index card](<Index Card Sized Notetaking>):
!Pasted image 20260829152013.png

## 1. Entities and identity

Anything worth identifying may be an entity: a note, record, file, person, project, event, physical object, or concept. Every entity MUST have exactly one permanent `_id`; it is the only required field.

```yaml
_id: K7x92p
```

The ID MUST remain stable as names, content, relationships, types, storage location, or representations change. It SHOULD carry no semantic information. IDs MUST NOT contain `@` or `.`, which are reserved for #6. Addressing entity states and properties|addressing; #5. Profiles and representations|profiles MAY reserve additional characters.

## 2. Logical model and interchange

An entity is a **flat** collection of named fields. Values are scalars or arrays of scalars; nested objects are outside the common model. Its canonical interchange form is a flat JSON object:

```json
{
  "_id": "K7x92p",
  "_name": "Puzzle Box",
  "_alias": ["2026 Puzzle", "Puzzle Project"],
  "status": "active",
  ">project": "P9m31q"
}
```

Collections MAY use JSONL, one entity per line. Native storage need not be JSON.

## 3. The core [sigils](sigils)

The first character of a field name identifies its role:

| Form     | Meaning                             |
| -------- | ----------------------------------- |
| `field`  | Asserted domain data                |
| `_field` | Metadata                            |
| `~field` | Derived or non-authoritative data   |
| `>field` | Authoritative outbound relationship |

Sigils identify roles; they do not define domain-specific field meanings. An assertion is part of the entity's authoritative stored state, but SIGIL does not claim it is objectively true.

### `_` metadata

| Field      | Meaning                                                                                                                                                                                            |
| ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `_id`      | Permanent identity; **required**.                                                                                                                                                                  |
| `_name`    | Preferred human-readable name.                                                                                                                                                                     |
| `_alias`   | Alternate names for lookup; neither unique nor identity assertions.                                                                                                                                |
| `_type`    | Primary operational kind, such as `note`, `file`, `person`, or `project`; tooling may use it to choose behavior. It may also convey what kind of thing the entity is, such as `event`, or `person` |
| `_schemas` | Ordered schema references describing the meaning or allowed values of ordinary fields. If definitions overlap, the first listed schema takes precedence.                                           |
| `_created` | Wall-clock time the entity was created.                                                                                                                                                            |
| `_updated` | Wall-clock time its authoritative logical state last changed.                                                                                                                                      |
| `_path`    | Location of its native representation or represented resource; not part of identity.                                                                                                               |

Additional metadata MAY be defined by future protocol versions or profiles. `_schemas` is optional: a record can be understood and exchanged without a schema registry. A schema may, for example, say that `length` means duration for an event and physical distance for another kind of entity.

### `~` derived fields

Ordinary fields contain asserted domain data. A `~` field contains data from calculation, inference, aggregation, lookup, or other derivation. Derived data is replaceable and SHOULD NOT by itself change `_updated`.

```yaml
_id: B8m21q
_type: event
_schemas:
  - race
  - timedActivity
duration: PT29M48S
kilometers: 5 
~pacePerMile: "9:35 min/mi"
```

### `>` relationships

`>predicate` asserts a directed relationship from the current entity to the entity IDs in its value. The current entity owns the authoritative assertion:

```yaml
_id: B8m21q
>containedBy: K7x92p
>about:
  - N2v84s
  - P9m31q
```

The target need not store an inverse assertion. Incoming relationships can be found by querying or indexing; a generated backlink is derived data, not another authoritative edge. Incoming relationships may be represented as a `~` derived field.

## 4. Relationships and reference resolution

Predicates are open-world: `>inspiredBy` can be a local label or a reference to a defined concept with its own `_id`. Ontologies, predicate registration, domain/range rules, and reasoning are optional. A predicate entity may itself use SIGIL or refer to an external vocabulary such as SKOS, RDF Schema, or OWL.

The canonical target of a relationship is another entity's `_id`. A profile MAY accept a native reference if it resolves unambiguously to an ID. For example:

```yaml
>containedBy: "Puzzle Box"
```

An Obsidian profile could resolve that Wikilink to `K7x92p`. Names, Wikilinks, paths, and native keys help locate entities; they do not replace identity.

## 5. Profiles and representations

A profile maps an environment such as Markdown, Obsidian, CSV, or an archive to and from the logical entity model. It may specify native reference syntax, arrays, escaping, scalar conversion, paths, additional metadata, and handling for content outside fields. A conforming profile MUST preserve core semantics and round-trip SIGIL-governed information without loss.

For example, a Markdown profile could map document text to a profile-defined `_body` field; `_body` is not required or defined by the core. A JPEG or physical object might use a separate entity record and `_path` to locate the resource. Paths may be relative to a portable root.

!Pasted image 20260923215326.png

Changing formatting, field order, serialization, or storage location does not create a new entity state. `_updated` SHOULD change only when authoritative logical content changes.

## 6. Addressing entity states and properties

An ID names the enduring entity. Adding `@` and an `_updated` value addresses a particular state; adding `.` and a field name addresses a property. For example:

```text
K7x92p@2026-08-26T11:14:00.length
```

Omit `@` to address the current entity or property; omit `.length` to address the entity or state itself. The version qualifier comes before the property. ISO 8601 timestamps are RECOMMENDED; timezone information MAY be included. Historical retention is optional. If an entity or property cannot be resolved, lookup tooling SHOULD return NULL.

## Scope

SIGIL defines the entity model and sigil roles. Profiles define how environments represent it. Tooling and repositories may add indexing, query, merge, version history, schema interpretation, or synchronization. A repository may keep tombstones for deleted IDs so that synchronization does not restore deleted entities. None of these facilities requires centralizing every entity in one store.

---

# Appendix A — SIGIL Profiles

*This appendix is non-normative.*

The SIGIL core describes the logical entity model. Profiles describe how that model is expressed in particular environments.

A profile might define conventions such as:

```text
SIGIL JSON Profile
SIGIL JSONL Profile
SIGIL Markdown Profile
SIGIL CSV Profile
SIGIL Obsidian Profile
SIGIL File Archive Profile
```

Profiles are expected to solve practical representation problems without expanding the core protocol.

For example, a CSV profile could specify that:

```text
one|two|three
```

represents an array of three strings, while:

```text
one\|two|three
```

represents:

```json
["one|two", "three"]
```

with `\` escaping the following character.

A Markdown profile could specify that frontmatter fields map to entity fields while Markdown content maps to `_body`.

An Obsidian profile could additionally permit Wikilinks as local shorthand for relationship targets, provided they can resolve to canonical `_id` values.

Profiles may also define scalar coercion, filename conventions, `_path` roots, or additional profile-specific metadata.

The important compatibility boundary is simple:

> **A conforming profile can import to and export from the canonical SIGIL entity model without losing protocol-defined information.**

# Appendix B — SIGIL Tooling and Repositories

*This appendix is non-normative.*

SIGIL intentionally does not define how collections of entities must be stored, synchronized, queried, merged, indexed, or reasoned over.

Those behaviors belong to tooling and repository layers built on top of the entity protocol.

Possible SIGIL-aware tooling may provide:

- entity lookup and resolution,
- property lookup,
- relationship and backlink queries,
- format conversion,
- indexing,
- search,
- derived-field generation,
- aggregation,
- validation,
- ontology resolution,
- reasoning,
- repository synchronization,
- replication,
- merge and conflict handling,
- entity forwarding or equivalence,
- views over entities,
- or archival/version retrieval.

These mechanisms are intentionally outside the SIGIL core.

****

# More

## Source

- self
