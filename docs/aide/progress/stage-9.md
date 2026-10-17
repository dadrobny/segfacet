> Stage 9's section, archived from [progress.md](../progress.md) by `aide progress archive`; `aide progress unarchive --stage 9`, run on the main or queue branch, moves it back.

## Stage 9 — Containerisation & XNAT Container Service Command (G5) — ✅

**Goal.** Package the completed pipeline as a Docker image with an XNAT command.

**Deliverables.**

- ✅ Dockerfile (CPU-only base), pinned deps, bundled/mounted reference data. *(Item 066)*
- ✅ XNAT Container Service `command.json` (inputs: session/scan + segmentation; outputs: report resources). *(Item 067)*
- ✅ Entry script mapping XNAT inputs → CLI → output resources. *(Item 068)*
- ✅ Local container smoke test + deployment docs. *(Items 069, 070)*

**Acceptance.** *(Both met as written — but note what they do **not** say: neither
requires an XNAT server. G5's outcome ("runs … on real session data") is
therefore **not** evidenced here — see the XNAT row in the verification table and
Stage 15.)*

- [X] Container runs the pipeline on a mounted case, producing JSON + human report. *(Item 070; `docker build` + `docker run` verified for real in CI — on a **local mounted case**, not an XNAT session.)*
- [X] `command.json` validates; install steps documented (**G5**). *(Item 070; the command definition validates and the install procedure is documented, but has **never been executed against a live XNAT server**.)*
