# PowerPoint assembly guide

**Ready for manual assembly.** Use the [main copy and notes](final_slide_content.md), [appendix content](final_appendix_content.md), [evidence index](slide_evidence_map.md), and [visual kit](../exhibits/presentation/final_exhibits.md). The presentation runs 12:00, followed by about 3:00 for questions.

1. Create one widescreen 16:9 group PowerPoint. Copy the main-slide text and visual labels from the ten numbered sections. Put the speaking cues in presenter notes. Make the slide’s key point and the evidence intelligible when the deck is read without those notes.
2. Render the editable diagrams from Mermaid or recreate them as PowerPoint shapes. Preserve physical versus logical arrows and the implemented versus proposed architecture boundary. Insert the provided SVG as a vector image. Recreate the compact comparison and validation tables as native tables.
3. Use the [strategic](../site/strategic_acquisition.html) and [operational](../site/operational_campaigns.html) dashboards as layout masters. For slide 07, use the strategic cumulative contribution chart and give F1 most of the slide. If the data changes, rerun `src/build_dashboards.py` and `src/export_presentation_extracts.py` to refresh the extracts. Use the fixed SVG or PNG files under `exhibits/presentation/`; the [chart mapping](../exhibits/presentation/dashboard_chart_sources.md) identifies each one. The visual kit includes portable tables if an embedded screenshot would be too small. Keep metric labels, missing-plan status and maturity counts visible.
4. Add appendix A–F after slide 10. Include readable DDL columns and source rows and present selected expected/observed extracts directly inside the deck. Preserve source IDs, cutoff footers and the difference between cohort and full visible windows. Use detail pages for the audited totals and sensitivities.
5. Add compact source footers and a sources page. Cite the Assignment 1 deck by title and slide numbers. Embed readable evidence when a private repository, paid account or connected app would otherwise be required. Check the assembled deck offline and rehearse with the provided timings.

## Submission completeness

- [x] Ten slide drafts with Q1–Q5 mapping, Assignment 1 alignment, and 12-minute timing.
- [x] Representative evidence, physical schema, ELT, customer example, cohort and dashboard extracts.
- [x] Independent reconciliation, original failed probe, corrected regression and reproducibility evidence.
- [x] Appendix A–F copy and slide-level source index.
- [ ] Assemble and review one consolidated group PowerPoint.
- [ ] Confirm all five names and actual contribution statements.
- [ ] Confirm material AI use and the actual human verification performed.
- [ ] Embed the selected restricted-access excerpts and verify readability offline.
- [ ] Final rehearsal and review of exhibit crop, ratio labels and source footers.

Keep the source and analytical package available for supporting evidence. The deck’s performance figures illustrate synthetic calculations, history alignment and validation. Use the proposed labels on MMP and other production integrations.
