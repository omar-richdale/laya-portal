// Package the user's fully generated slide images. Each slide stays a complete raster image.
import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {Presentation, PresentationFile, FileBlob} from '@oai/artifact-tool';

const root = process.env.LAYA_PROJECT_ROOT;
const skill = process.env.SKILL_DIR;
const python = process.env.RUNTIME_PYTHON;
if (![root, skill, python].every(p => p && path.isAbsolute(p))) throw new Error('Configure absolute runtime/project paths.');
const deck = path.join(root, 'docs/presentation/v1');
const build = path.join(root, '.cache/presentation-build');
const finalPath = path.join(deck, 'output/local-system-one.pptx');
const {finalizePresentation} = await import(pathToFileURL(path.join(skill, 'container_tools/artifact_tool_utils.mjs')).href);
const notes = [
  'Local decision hints for the Richdale repositories. The fixed-choice model returns distributions; coding and evidence verification remain separate.',
  'Snapshot: 134 GhostShield and 99 TotalGuard open issues. Source scanner inventory: 196 dependency, 20 secret, 7 code, 10 business. Semantic investigation lanes move two SAST credential findings into the credential lane: 22 credential and 5 source-code issues.',
  'Classifier labels never grant permissions or prove a vulnerability. Existing tool allowlists, evidence validation, regression tests and human merge review remain authoritative.',
  'Clients share one FastAPI service and one serialized GPU worker. A request-specific checkpoint leaves the persisted default unchanged. Model switches unload the previous checkpoint. Offline reference PyTorch inference; no CPU fallback.',
  '247 decision cases consist of 233 issue-workflow cases, seven overlapping source-topic cases, and seven QA observations. Three repeats per checkpoint: 2,223 single predictions. Nine 32-state batches add 288 states. Three warmups per model excluded from timing. Constant choice order was not counterbalanced.',
  'Median/p95 are service times for resident inference, not total workflow time. HTTP medians are 64.36/54.40/66.32 ms. Separate first use after restart took 28.86 s; allocator readings in this table are observations after requests and not isolated peaks. Additional fresh-process startup/memory measurements are in the report.',
  'Numbers show agreement with routing metadata and evidence-audit references. The issue majority baseline is 196/233. Macro F1 for issue workflow is .7222/.6202/.6526. Seven security-topic cases and seven QA observations cannot establish production accuracy or confidence calibration.',
  'User confirmed the card requirement. The current website trial/start route returns card-required until setup. The captured QA profile still expected an automatic no-card trial. All checkpoints misclassified that audit case as PRODUCT_BUG. The explicit profile correction sets signupGrantsTrial=false; app-token security assertions remain.',
  'Sift emits topic advice only as operator shadow metrics after mechanical evidence validation. It does not enter the independent-verifier prompt or modify its result. Existing scanner classification, monotonic priority, suppressions and issue lifecycle continue unchanged.',
  'A read-only planner groups 196 dependency findings into 34 repository/package investigation groups; grouping does not fix vulnerabilities. Current Bugsmith policy forbids dependency upgrades. Its optional QA hints do not change selected/deferred/skipped findings. Historical automatic-trial reports need a contract-aware QA rerun before repair.',
  'QA keeps deterministic Playwright results and its existing assessment and notification decisions. Optional hints add report.json metadata only. TotalGuard app-token assertions observed valid=true after signout on two days; independently reproduce on the pinned deployed revision before changing production code.',
  'Optional adapters are local and disabled by default. The dataset supports further shadow evaluation, not automated security verdicts. No production deployment, issue mutation, credential rotation or credit-card operation occurred.'
];
const commonSources = 'Sources: local docs/benchmark/REPORT.md, corpus.json, results.json and integration-replay.json; https://huggingface.co/convaiinnovations/laya/blob/main/README.md; https://github.com/omar-richdale/sift; https://github.com/omar-richdale/vpn-bugsmith; https://github.com/omar-richdale/QA_Web_Testing_Agent. Snapshot 2026-10-01.';
const qaSources = 'QA evidence: https://vpnqa.richdalelab.com/reports/20260930-060000-9iy9o/index.html; https://vpnqa.richdalelab.com/reports/20260930-071000-9o49u/report.md; https://vpnqa.richdalelab.com/reports/20260929-071000-wzuvk/report.md.';
await fs.mkdir(build, {recursive:true});
await fs.mkdir(path.dirname(finalPath), {recursive:true});
const presentation = Presentation.create({slideSize:{width:1280,height:720}});
for (let i=1; i<=12; i++) {
  const number=String(i).padStart(2,'0');
  const slide=presentation.slides.add();
  slide.background.fill='#0B1326';
  slide.images.add({blob:new Uint8Array(await fs.readFile(path.join(deck,`out/${number}.png`))),contentType:'image/png',
    alt:notes[i-1],fit:'contain',position:{left:0,top:0,width:1280,height:720}});
  slide.speakerNotes.textFrame.setText(notes[i-1]+'\n\n'+commonSources+'\n'+qaSources);
}
const candidatePath=path.join(build,'candidate.pptx');
await (await PresentationFile.exportPptx(presentation)).save(candidatePath);
await finalizePresentation({workspaceDir:root,candidatePath,finalPath,pythonExecutable:python,
  integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
  layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
  layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit'],
  explicitTotalSlideCount:12,requiredNativeTableOwnerSlides:[],requiredNativeChartOwnerSlides:[],
  verifyArtifactToolImport:true,receiptPath:path.join(build,'final.validation.json')});
// Render the final package, rather than assuming that embedding preserved placement.
const final=await PresentationFile.importPptx(await FileBlob.load(finalPath));
for (let i=0; i<final.slides.items.length; i++) {
  const image=await final.export({slide:final.slides.items[i],format:'png',scale:1});
  await fs.writeFile(path.join(build,`render-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await image.arrayBuffer()));
}
const montage=await final.export({format:'png',montage:true,scale:.35});
await fs.writeFile(path.join(build,'montage.png'),new Uint8Array(await montage.arrayBuffer()));
console.log(finalPath);
