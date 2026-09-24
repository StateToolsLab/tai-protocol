# Changelog

## 0.2.0-rc.1 — 2026-09-24

Release candidate for document-constrained, engine- and source-channel-independent
handoffs. Maintains the existing Git windows and bridge wire format.

### Added

- Engine-neutral Core specification, Task / Report / Recovery State templates.
- Explicit replaceability of Architect, Supervisor, and Worker; durable recovery state.
- Manual, mixed-engine, and agent-connected reference workflows with identical
  document, authority, and approval boundaries.
- Immutable issued-Task archives, including superseded and cancelled revisions.
- Standard-library Python archive helper and unit / temporary-Git tests.
- Independent evidence retrieval, original-text integrity checks, and migration guide.

### Changed

- Two manual transfers are an available profile, not a universal prohibition on automation.
- Durable documents, not private conversation memory, carry accepted state and decisions.
- Supervisor must not repair issued Task contents; invalid Tasks return to the issuer.
- Removed the conflicting Worker-only Report revision increment exception.
- Gate completion checks include archive/reset cleanup, not only the implementation merge.
- Task template keeps status: active and removes inline comments from model values.
- Standard Git display omits author/body fields; synchronization uses fetch plus an
  explicit ff-only merge. Neither change claims to sanitize all PII or eliminate all races.

### Compatibility and limits

- Existing task/report frontmatter, paths, carrier branches, notification keys, and
  Report return path are retained. No automatic migration of live project files.
- bridge-poll.sh and notify-architect.sh are unchanged. Their runtime behavior and
  permissions have not been certified against current cloud services in this update.
- No new multi-engine dispatcher, external-channel connector, distributed lock,
  budget enforcer, or end-to-end autonomy runtime is shipped.
- Cost reduction is not guaranteed. Evaluate accepted outcomes, total cost, and rework.
- No release tag, deployment, or main-branch merge is part of preparing this candidate.

## 0.1.0 — 2026-08-30

Original public baseline: 28a632ef89562519d9c82260c75f94658a30cde9.
Claude Code / Git handoff with protected manual transfers and a model-agnostic Architect.
