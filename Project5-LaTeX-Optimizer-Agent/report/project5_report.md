# Project 5 Report: AI Agent Pipeline for LaTeX Project Compression

## 1. Objective

The objective of this project was to design and implement an AI-agent-style pipeline for optimizing a LaTeX project. The goal was to reduce the total compressed project size while preserving the visual quality of the final compiled PDF.

The project had two main requirements for undergraduate students:

- Part 1: Reduce the full LaTeX project zip size to less than 50 MB.
- Part 2: Further optimize the compiled PDF so that the PDF size is less than 30 MB.

A key constraint was that the project should not minimize size at all costs. The final result needed to balance compression with visual clarity.

## 2. Initial Project State

The original LaTeX source project was downloaded from the provided Overleaf link as a zip file.

Initial measurements:

| Item | Size |
|---|---:|
| Original downloaded zip | 118 MB |
| Original unzipped LaTeX project | 119 MB |

The original project contained several large image files, backup files, and duplicate/unused figures.

## 3. Pipeline Design

I designed the workflow as a multi-step agent pipeline:

### Step 1: Analysis Agent

The analysis step inspected the LaTeX project folder and identified large files. It also searched the LaTeX source files for active `\includegraphics` commands to determine which images were actually used in the final PDF.

This step helped separate necessary figures from unused or backup figures.

### Step 2: Decision Agent

The decision step determined which files could be safely removed or moved outside the optimized project. Files were treated as removable if they were:

- backup files,
- duplicate figures,
- unused figures,
- old figure versions,
- not referenced by active LaTeX source code.

Instead of deleting files permanently, unused figures were moved into a separate folder. This made the process safer because files could be restored if compilation failed.

### Step 3: Action Agent

The action step performed the optimization. The main actions were:

- removed the `backups` folder from the optimized LaTeX project,
- removed accidental nested duplicate project folders,
- moved unused figure versions outside the final project,
- compressed remaining JPG images using moderate image compression,
- preserved images that were actively referenced in the LaTeX source.

The image compression was done using macOS `sips`, with a maximum image dimension and JPEG quality setting. The goal was to reduce image file sizes while keeping the figures visually readable.

### Step 4: Verification Agent

The verification step checked whether the optimized project satisfied the requirements.

I verified:

- the optimized source zip size,
- the compiled PDF size,
- whether the LaTeX project compiled successfully,
- whether figures were still visible and visually acceptable in the final PDF.

## 4. Implementation Details

The pipeline was implemented in Python in `code/project5_pipeline.py`.

The script performs the following tasks:

- computes project and file sizes,
- lists the largest files,
- scans `.tex` files for active `\includegraphics` references,
- identifies used image files,
- provides functions for moving unused files,
- provides functions for compressing JPG images,
- creates an optimized zip archive.

The script uses local deterministic steps for most of the pipeline. This reduces API cost and avoids unnecessary use of the OpenRouter budget.

## 5. Budget-Aware AI Strategy

Because the project provides a fixed API budget, my strategy was to avoid sending the entire LaTeX project or all images to a foundation model. Most file-size analysis and compression decisions can be handled locally using Python.

A budget-aware AI pipeline would use the API only for higher-value decisions, such as:

- checking a small sample of before/after figure screenshots,
- asking a vision-language model whether visual quality remains acceptable,
- helping decide whether additional compression is safe,
- summarizing optimization results for the report.

This avoids wasting API credits on tasks that deterministic code can already solve.

## 6. Final Results

After optimization, the final project satisfied both requirements.

| Item | Size |
|---|---:|
| Original downloaded zip | 118 MB |
| Optimized LaTeX source zip | 16 MB |
| Final compiled PDF | 17 MB |
| Required final zip size | < 50 MB |
| Required PDF size | < 30 MB |

The optimized source zip was reduced from 118 MB to 16 MB. The final compiled PDF was 17 MB, which is below the 30 MB requirement.

## 7. Visual Quality Check

After compiling the optimized LaTeX project, I opened and inspected the final PDF. I checked that:

- figures were not missing,
- image comparison tables remained visible,
- the main illustration figures were still readable,
- the layout was not corrupted,
- there were no severe compression artifacts.

Because the project emphasizes balancing compression and quality, I stopped further compression once the size requirements were safely met.

## 8. Conclusion

This project demonstrated how an agentic AI workflow can be applied to a practical document optimization task. The final pipeline followed an analysis, decision, action, and verification structure. The project also showed that not every part of an AI-agent pipeline needs to use an expensive model. Local tools can handle file analysis and compression, while foundation models can be reserved for judgment-based tasks such as visual quality evaluation.

The final optimized LaTeX project and compiled PDF satisfied the required size limits while preserving acceptable visual quality.