# Project TODOs

## Future Roadmap: SiteMigrationChecker
Based on `docs/網站遷移檢測專案規劃.md` (2025-11-11), a new tool for website migration quality assurance is planned.

### Phase 1: Core Engine (Planned)
- [ ] Implement 301 Redirect Checker
  - Check status codes (must be 301)
  - Verify target URLs
  - Detect redirect chains
- [ ] Implement Canonical Tag Checker
  - Verify existence and correctness
  - Check self-canonicalization
- [ ] Reuse `SitemapGen` crawler engine

### Phase 2: SEO & Content Analysis (Planned)
- [ ] SEO Element Checker (Title, Meta Description, H1)
- [ ] Problematic Page Detection
  - Empty product pages
  - Empty list pages
  - 404/500 errors
  - Duplicate content

### Phase 3: GUI & Reporting (Planned)
- [ ] Develop GUI for Migration Checker
- [ ] Implement Report Generation (Excel, HTML, JSON)

## Current Maintenance (SitemapGen)
- [ ] Review and sync documentation in `Custom-made/` with `docs/`
- [ ] Ensure `config.json` defaults match documented rules
