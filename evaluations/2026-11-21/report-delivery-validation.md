# Report delivery correction checks

- Two repeated builds preserve the supplied zero-file count in both freshness JSON and prose.
- ED138 HTTP 400 is explicitly a failed query, not a successful empty history.
- All four formerly inaccessible appendices have standalone HTML files.
- The complete single-file report embeds all seven sections, the 74-observation CSV table, local evidence and selected JSON trial/provenance records.
- HTML parser validation checks every internal fragment target and rejects companion-file links or external resource dependencies. Internet source hyperlinks and embedded JSON/CSV downloads are allowed.
- Scientific observations, flux ratios and held-out numerical results are unchanged.
