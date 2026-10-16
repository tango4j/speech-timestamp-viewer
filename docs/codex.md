# Codex integration

## Start a viewer in your conversation

Copy or clone this repository on the machine where Codex can read your audio and predictions.
Open it as a project or provide its absolute path. Python 3.10+ and FFmpeg with libmp3lame
are required; Codex can follow the [installation instructions](../README.md#use-in-a-regular-browser).

Copy the [Codex prompt in the README](../README.md#use-in-codex), replacing the prediction path.
Also provide a reference JSONL path if it supplies audio locations. For a first test without
private data, ask Codex to generate `examples/make_demo.py`'s synthetic demo and show it inline.

Codex needs access to both the manifests and audio on its execution machine. A path on your
laptop is not automatically available to a remote execution environment. Use path remapping
when necessary; see [usage](usage.md).

## Generated files

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

