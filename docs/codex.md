# Codex integration


Copy or clone this repository on the machine where Codex can read your audio and predictions.
Ask Codex:

> Read this repository's AGENTS.md and README.md. Build the timestamp player from these
> prediction/reference files, select ten 2mix samples, and show it inline in this conversation.

The builder emits:

- `index.html`: a standalone offline player containing all selected samples.
- `inline-001.html`, etc.: HTML fragments, automatically split below 950,000 bytes.
- `selection.json`: reproducible sample IDs and excerpt ranges.

For inline display, build into a **durable directory explicitly writable and readable by the
current Codex conversation**, not a hardcoded directory from another workstation. The CLI prints
the exact content references. Codex should include each desired reference in its final response:

```text
visualize{"path":"/absolute/path/to/inline-001.html"}
```

This requires a Codex client with inline visualization support; plain CLI/other clients can open
`index.html` in a browser instead. Copying the repository cannot enable a missing host feature.
No host-provided wrapper or skill is needed to generate the files. If a visualization skill is
available to the agent, it should follow that skill's current rendering instructions.

If one recording alone exceeds the fragment size limit, the builder fails with a suggestion to
use a shorter excerpt (e.g. `--duration 30`). It never silently drops the recording.

