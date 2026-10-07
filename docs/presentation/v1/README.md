# Local System One presentation

Twelve complete slide images generated with the built-in image generation tool, using Sift's v3 style/body/prompt structure and navy/amber design. Each slide has its own brief and prompt. No stock screenshots, API-generated text overlays or programmatically drawn illustrations were used.

- [PowerPoint](output/local-system-one.pptx)
- [PDF](output/local-system-one.pdf)
- [Offline gallery](index.html)
- [Presenter guide](PRESENTER-GUIDE.md)
- [Benchmark report](../../benchmark/REPORT.md)

`style.txt` adapts the supplied Sift v3 reference; `bodies/NN.txt` contains each exact content brief; `prompts/slide-NN.txt` combines style and body; `out/NN.png` contains the generated result. Follow-up edit prompts are saved for slides 06 and 09. Slide 06 adds the observed slow first request; slide 09 clarifies that shadow metrics never enter the verifier prompt.

The PNGs are 1672×941 pixels, close to 16:9. PowerPoint and PDF preserve each full image on a 16:9 canvas. Text, tables and diagrams inside the slides are raster images: edit the briefs and regenerate a slide to change its content. PowerPoint includes descriptive alt text and evidence/source notes for each slide. The individual PNGs are also available for direct sharing. This is a generated-slide deck as requested, not an editable chart deck.

`scripts/prepare_presentation.py` prepares the briefs from the supplied Sift style. `scripts/assemble_presentation.mjs` packages the slide images with the bundled Artifact Tool runtime. `scripts/package_slide_images.py` creates the PDF, gallery and image-hash manifest using bundled Python libraries. Packaging preserves the source images; it does not draw or edit slide contents. Runtime paths are environment-specific; the source scripts describe their inputs. Use a new final output filename when rebuilding a checked PowerPoint.

Reference: `Agentic-production/sift/docs/presentation/v3` at Sift commit `110a429a829ade6be1292e72bb79f9f6d31ce7b8`. The actual task evidence is local, frozen on 2026-10-01; source links and checkpoint caveats are in the report and speaker notes.
