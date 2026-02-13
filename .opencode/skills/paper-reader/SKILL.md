---
name: paper-reader
description: Advanced academic paper analysis and comprehension skill for extracting key information, methodology, and insights from research papers
version: 1.0.0
author: OpenCode
---

# Paper Reader Skill

A comprehensive skill for reading, analyzing, and extracting insights from academic papers in PDF or text format.

## When to Use

Use this skill when you need to:
- Extract key information from academic papers
- Understand methodology and experimental design
- Summarize findings and conclusions
- Compare multiple papers
- Identify citations and references
- Extract technical details for implementation

## Paper Analysis Framework

### 1. Initial Assessment
Always start by identifying:
- **Title**: What is the paper about?
- **Authors**: Who conducted this research?
- **Publication**: Where and when was it published?
- **DOI/URL**: How to reference this work?

### 2. Core Content Extraction

#### Abstract Analysis
- Research objective/question
- Key methods used
- Main findings/results
- Significance/contribution

#### Introduction & Background
- Problem statement
- Literature review highlights
- Research gap addressed
- Proposed solution approach

#### Methodology
- Experimental design
- Materials/methods
- Simulation setup (for TCAD/software papers)
- Parameters and conditions
- Tools/software used

#### Results & Discussion
- Key findings with data
- Figures and tables interpretation
- Comparison with prior work
- Limitations acknowledged

#### Conclusion
- Summary of contributions
- Future work suggestions
- Practical implications

### 3. Technical Deep-Dive (for TCAD/Semiconductor Papers)

When analyzing device simulation papers like the HgCdTe nBn detector:

**Device Structure**:
- Layer materials and thicknesses
- Doping concentrations
- Bandgap energies
- Operating temperatures

**Physical Models**:
- Poisson equation
- Drift-diffusion equations
- Continuity equations
- Statistical models (Fermi-Dirac, etc.)
- Recombination mechanisms (Auger, SRH, radiative)

**Simulation Parameters**:
- Mesh/grid setup
- Boundary conditions
- Solver settings
- Convergence criteria

**Results Validation**:
- Comparison with experimental data
- Benchmarking (Rule 07 for IR detectors)
- Quantum efficiency calculations
- Dark current analysis

### 4. Context Mapping

Connect paper content to practical implementation:
- Which DEVSIM examples are relevant?
- What code modifications are needed?
- Are there missing implementation details?
- What validation can be performed?

## Usage Instructions

### Basic Paper Analysis
```
Use paper-reader skill to analyze [paper file path]
```

### Comparative Analysis
```
Compare [paper1] with [paper2] focusing on methodology
```

### Technical Implementation
```
Extract simulation parameters from [paper] for DEVSIM implementation
```

## Best Practices

1. **Always verify extracted data** by cross-referencing with figures/tables
2. **Note uncertainties** or approximations mentioned by authors
3. **Identify assumptions** in the methodology
4. **Check units** and convert if necessary for consistency
5. **Track citations** for further reading
6. **Note software versions** if specific tools are mentioned

## Output Format

Provide analysis in this structure:

```markdown
# Paper Analysis: [Title]

## Overview
[Summary of what the paper is about]

## Key Information
- **Authors**: 
- **Journal/Conference**: 
- **Year**: 
- **DOI**: 

## Abstract Summary
[Key points from abstract]

## Methodology
[Detailed methods section]

## Key Results
[Main findings with data]

## Technical Details
[Parameters, equations, models]

## Connection to Codebase
[How this relates to current project]

## References
[Important citations]

## Action Items
[What can be implemented or tested]
```

## Examples

### Example 1: TCAD Device Simulation Paper
Input: "Analyze the HgCdTe nBn detector paper in papers/JEM2025.pdf"

Output should include:
- Device layer structure (Table II)
- Material parameters
- DEVSIM equations used
- Comparison with Rule 07 benchmark
- Relevant DEVSIM examples (diode, capacitance)

### Example 2: Methodology Paper
Input: "Extract the numerical methods from [paper]"

Output should include:
- Discretization schemes
- Solver algorithms
- Convergence criteria
- Grid generation approach

## Limitations

- Cannot access paywalled content without user providing file
- PDF text extraction may have formatting issues
- Equations may need manual transcription
- Figures require visual interpretation
- Assumes standard academic paper structure

## Related Resources

- DEVSIM documentation: https://devsim.net
- TCAD best practices
- Semiconductor physics references
- Numerical methods literature

## Updates

v1.0.0 - Initial release
- Basic paper analysis framework
- TCAD-specific extraction guidelines
- DEVSIM integration pointers
