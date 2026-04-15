---
name: clone-website
description: Reverse-engineer and clone one or more websites in one shot — extracts assets, CSS, and content section-by-section and proactively dispatches parallel builder agents in worktrees as it goes. Use this whenever the user wants to clone, replicate, rebuild, reverse-engineer, or copy any website. Also triggers on phrases like "make a copy of this site", "rebuild this page", "pixel-perfect clone". Provide one or more target URLs as arguments.
argument-hint: "<url1> [<url2> ...]"
user-invocable: true
---

# Clone Website

You are about to reverse-engineer and rebuild **$ARGUMENTS** as high-fidelity website clones.

When multiple URLs are provided, process each target independently and in parallel when possible. Keep all artifacts isolated per target host (for example, `docs/research/<hostname>/` and `docs/design-references/<hostname>/`).

Use a continuous extraction-and-build loop: inspect one section, write its spec file, dispatch a focused builder, then move to the next section while builders run in parallel.

## Scope Defaults

Unless the user overrides them:

- **Fidelity:** pixel-perfect visual and interaction parity
- **In scope:** layout, styles, component structure, interactions, responsive behavior, realistic mock data
- **Out of scope:** real backend/data services, auth flows, production SEO, accessibility audit
- **Customization:** none (strict emulation)

## Pre-Flight

1. Verify browser automation is available (prefer Chrome MCP, otherwise Playwright/Browserbase/Puppeteer MCP).
2. Parse and validate each URL in `$ARGUMENTS`; confirm it can be opened in browser MCP.
3. Detect the existing project stack and follow its current structure (framework, routing, styling system, component organization).
4. Verify a clean baseline build using the stack's existing build command.
5. Ensure artifact folders exist: `docs/research/`, `docs/research/components/`, `docs/design-references/`, `scripts/`, plus per-host subfolders.

## Generalization Rules (Current Structure First)

- Reuse the repository's current architecture. Do not force a framework-specific layout.
- Map global style updates to the project's existing global style entrypoint.
- Map root page/layout changes to the project's existing entry files.
- Place new clone components in the existing component/module structure.
- Keep naming and folder conventions consistent with what already exists.

## Core Principles

1. **Complete extraction over fast approximation.** Builders should never guess critical values.
2. **Small, focused builder scope.** If a spec is too large, split by sub-component.
3. **Real assets and real content.** Prefer extracted text/media over generated placeholders.
4. **Interaction parity matters.** Capture not only appearance, but triggers and transitions.
5. **All states are required.** Extract default, hover, active, scroll-driven, and responsive states.

## Phase 1: Reconnaissance

For each target URL:

1. Capture full-page screenshots at desktop and mobile.
2. Record page topology (ordered sections, overlays/sticky layers, dependencies).
3. Run behavior sweep:
   - scroll-driven changes
   - click-driven state changes
   - hover states
   - responsive breakpoints
4. Save findings:
   - `docs/research/<hostname>/BEHAVIORS.md`
   - `docs/research/<hostname>/PAGE_TOPOLOGY.md`

## Phase 2: Foundation (Stack-Aware)

Apply global setup within the detected project structure:

1. Configure fonts/tokens/global CSS variables in the existing global styling location.
2. Extract and store site assets (images/videos/icons/favicons) under `public/` using a scripted downloader (`scripts/download-assets.mjs`).
3. Add shared types/interfaces in the project's existing type location.
4. Validate build before moving to section builders.

## Phase 3: Spec-Driven Component Build

For each section (top to bottom):

1. Extract:
   - section screenshot
   - computed styles (exact values)
   - behavior triggers/transitions
   - verbatim text content
   - referenced assets
2. Write spec file: `docs/research/components/<component-name>.spec.md`
3. Dispatch builder agent(s):
   - simple section: one builder
   - complex section: split into sub-components + wrapper builder
4. Merge completed builders incrementally and re-run build checks.

Builder prompts must include full spec content inline (no "go read file" dependency).

## Phase 4: Assembly

Assemble all generated sections in the project's current page/module entry structure:

- wire section ordering from topology
- connect props/content
- implement page-level behaviors (scroll, transitions, observers, snap/smooth behavior if present)
- verify build passes

## Phase 5: Visual QA

Perform side-by-side comparison (desktop + mobile):

1. Compare each section visually and behaviorally.
2. If mismatch exists:
   - if spec is wrong, re-extract and update spec
   - if build output is wrong, fix implementation to match spec
3. Re-test interactions and responsive behavior.

## Pre-Dispatch Checklist

- [ ] Section spec file exists and is complete
- [ ] Styles are extracted from computed values, not guessed
- [ ] Interaction model is explicit (scroll/click/hover/time/static)
- [ ] Stateful content is fully extracted per state
- [ ] Asset mapping is complete, including layered assets
- [ ] Responsive behavior is documented
- [ ] Builder scope is small enough to avoid approximation

## Completion Report

When done, report:

- targets processed
- sections/components built
- spec files written
- assets downloaded
- build status
- visual QA results
- remaining known gaps
