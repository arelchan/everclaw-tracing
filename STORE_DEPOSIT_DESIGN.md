# `memory.store` deposit loop — design

Close the `memory.store` node's output loop: show, per trace, **what everos actually
sedimented from this turn** — not just a single episode, but the whole derived family.
Verified against real data in `~/.everos/raven/...` on 2026-07-01.

## Contract (grounded in everos's real model)

One `store` call (one trace) → everos creates exactly **one memcell** (`mc_xxx`) from that
turn's messages → the memcell is async-distilled (~30s, everos's own cascade thread) into a
**family** of derived memories, each back-linked to the memcell by `parent_id`:

| Derived type | md file | per-turn link | notes |
|---|---|---|---|
| episode | `episodes/episode-YYYY-MM-DD.md` | `parent_id: mc_xxx` | event summary (1 per turn) |
| atomic_fact | `.atomic_facts/atomic_fact-*.md` | `parent_id: mc_xxx` | discrete facts (several per turn) |
| foresight | `.foresights/foresight-*.md` | `parent_id: mc_xxx` | predictions (several per turn) |
| agent_case | (lance / md when present) | `parent_id: mc_xxx` | task turns only |
| agent_skill | (lance / md when present) | `parent_id: mc_xxx` | task turns only |
| user_profile | `user.md` | **none** — merged running doc | see profile signal below |

`node = store call`, `input = this turn's messages`, `output = the derived family for this
turn's memcell` (grouped by type), or **null** if the memcell distilled nothing.

## Correlation key — (session_id, timestamp), NOT message_ids

- raven's stored `messages_slice` carries only `{role, content}` — no ids/timestamps. everos
  generates its own message ids at ingest, so **message_ids is not a usable key.**
- Each md entry header carries `session_id` + `timestamp` + `parent_id`. The store artifact's
  write-time (its filename ms prefix) matches the memcell/md `timestamp` **to the millisecond**
  (verified: artifact `120128262329` ↔ `mc_fea95931a5c6` @ `12:01:28.262000`).
- `session_id` alone is too coarse (many turns per session). The precise key is
  **(session_id, timestamp)**: filter md entries by `session_id`, match `timestamp` to the
  store's time (from the artifact filename ms prefix, or span `startTime`) within a small
  tolerance; all entries of that turn share one `parent_id` — expand by it to get the full family.

## Mechanism — plan C (viewer-side, at render)

Chosen: **viewer reads everos + joins at display time.** Consequences the user accepted:
永远显示库里最新态、零运行时开销、**不落进 span JSONL**(审计日志里 store 仍是空输出,展示时才拼).

- **Zero plugin change** — the store span already carries `session_id`, `startTime`, and the
  artifact ref (filename → ms timestamp). Everything needed is present.
- **Zero sqlite dependency** — the md entry headers carry `session_id`/`timestamp`/`parent_id`,
  so the viewer parses md text directly. `system.db`'s `memcell` table is an optional exact
  cross-check (content match), not required.
- **Profile signal** — `user.md` has no per-turn link, and under the everos backend the
  `memory.profile_refresh`/`extract`/`consolidate` probes never fire (they wrap raven's *built-in
  local* memory; everos distills the profile internally). So the deposit does not attribute
  profile changes per-turn — it shows episode/fact/foresight/(case/skill); `user.md` is a merged
  everos doc updated async.

### Implementation (all in `viewer/`)
1. New `everos-deposits.js`: given the everos root (`~/.everos/raven`), glob the md files, parse
   entries into `{type, session_id, timestamp, parent_id, id, subject/summary/fact/foresight}`,
   index by `session_id`.
2. `server.js` `buildSessions()`: for each `memory.store` span, resolve its deposit family by
   (session_id, store-time) and attach as a synthetic `memory.deposit` payload.
3. `ui/app.js` (`renderMemoryCard`): render every memory node as an **Input card + Output card**
   (mirroring the llm/tool cards, class `content-card wide-card` + `structured-pre`):
   - recall → Input = query (+scope/top_k/user_id), Output = recalled memories + hit count
   - store → Input = the stored messages, Output = the deposit family grouped by type
     (`null` → "not yet distilled"); profile note inline
   - feedback → Input = injected/used skill ids, Output = "everos no-op" (nothing consumed)
   The raw `Memory Recall`/`Memory Store` artifacts are suppressed from the generic dump.

## Honesty caveats (state in UI)
- **Eventual, not realtime** — deposit lags store by ~30s; a just-run turn may show null until
  the cascade finishes (refresh later).
- **Profile is merged** — not attributed per-turn (and `profile_refresh` doesn't fire under everos).
- everos root defaults to `~/.everos/raven`; user/project are matched via `session_id`, not path.
