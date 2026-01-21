# Phase 5: Pattern Guerrilla - Context

**Gathered:** 2026-01-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Generate email pattern guesses from a person's name and company domain, then verify them in parallel using async verification. Stop on first valid email. Handles nicknames, multi-part names, and catch-all domains.

</domain>

<decisions>
## Implementation Decisions

### Pattern Selection
- **Tier 1 (highest priority):** `{first}@{domain}`, `{first}.{last}@{domain}`, `{f}{last}@{domain}`
- **Tier 2:** `{first}{last}@{domain}`, `{first}{l}@{domain}`
- **Tier 3:** `{last}.{first}@{domain}`
- Try patterns in tier order — Tier 1 patterns are most common in business email

### Nickname Handling
- Build standard mapping for common English nicknames: Bob→Robert, Mike→Michael, Bill→William, etc.
- Include common international variants: Giuseppe→Joe, Guillermo→William, etc. (top 20-30)
- Generate patterns for BOTH provided name AND formal/informal variants
- Example: "Bob Smith" generates patterns for both "bob" and "robert"

### Verification Strategy
- Use `async_verifier.py` from Phase 1 for all verification
- **Short-circuit logic:** Verify all patterns in single async batch, but cancel remaining on first valid
- Stop immediately on first valid — no backup emails needed
- Single batch verification (10 patterns at once), not sequential

### Catch-all Handling
- When domain is catch-all, return highest-tier pattern guess (e.g., `first.last@domain`)
- Mark status as "Guessed" with warning flag
- Only SMTP 250 successes on non-catch-all domains get "Verified High Confidence"

### Name Parsing
- Full support for complex names:
  - Hyphenated last names: Smith-Jones → try both "smith-jones", "smith", "jones"
  - Middle names: Mary Anne Smith → first="mary", try middle="anne", last="smith"
  - Suffixes: John Smith Jr. → ignore suffix
- Generate multiple interpretations for ambiguous names

### Claude's Discretion
- Exact number of patterns per tier
- Specific nickname mappings beyond the common ones
- How to handle single-word names (mononyms)
- Async batch size optimization

</decisions>

<specifics>
## Specific Ideas

- "High-performance pattern generator" — optimize for speed
- Confidence levels: "Verified High Confidence" (SMTP 250) vs "Guessed" (catch-all)
- Create `execution/pattern_guerrilla.py` as the main module

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 05-pattern-guerrilla*
*Context gathered: 2026-01-20*
