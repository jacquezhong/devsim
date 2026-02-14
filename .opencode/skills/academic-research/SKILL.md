---
name: academic-research
description: Automates academic research processing and paper quality assurance. Generates interactive analysis and conducts comprehensive pre-submission reviews for research papers.
license: MIT
compatibility: opencode
metadata:
  category: academic-research
  version: 1.0.0
---

# Academic Research & Paper Review Skill

This skill streamlines the academic research and writing process by leveraging systematic workflows for paper analysis, quality assurance, and pre-submission review.

## When to Use This Skill

Use this skill when:
- Conducting literature reviews and synthesizing research
- Analyzing academic papers for key insights
- Preparing manuscripts for submission
- Performing pre-submission quality checks
- Evaluating paper relevance and quality
- Extracting and organizing research findings

## Core Capabilities

### 1. Literature Analysis

**Paper Screening Process**

Two-stage paper screening workflow:
1. **Abstract Scoring**: Quick assessment of relevance
   - Research question alignment
   - Methodology appropriateness
   - Result significance
   - Publication quality

2. **Deep Dive Analysis**: Detailed examination for specific data extraction
   - Theoretical framework
   - Methodological approach
   - Key findings and implications
   - Limitations and future work

**Analysis Framework**

For each paper, analyze:
- **Research Question**: What problem does it address?
- **Methodology**: How was the study conducted?
- **Key Findings**: What are the main results?
- **Contribution**: What does it add to the field?
- **Limitations**: What are the weaknesses?
- **Relevance**: How does it relate to your work?

### 2. Quality Assurance System

**Pre-Submission Review (7 Dimensions, 35-Point Scale)**

| Dimension | Weight | Criteria |
|-----------|--------|----------|
| Originality | 5 pts | Novel contribution to field |
| Argumentation | 5 pts | Logical coherence, evidence support |
| Literature | 5 pts | Comprehensive, current coverage |
| Methodology | 5 pts | Appropriate, rigorous approach |
| Clarity | 5 pts | Accessible, well-structured writing |
| Impact | 5 pts | Potential influence on field |
| Technical | 5 pts | Accuracy, proper citations |

**Threshold**: Papers scoring ≥28/35 are considered submission-ready.

### 3. Research Gap Identification

**Evidence-Based Gap Analysis**

Every identified research gap must be backed by 3-5 citations:
1. Review existing literature systematically
2. Identify what has been done
3. Pinpoint what's missing or insufficient
4. Justify why the gap matters
5. Position your work as filling the gap

**Gap Categories**
- **Theoretical gaps**: Missing conceptual frameworks
- **Methodological gaps**: Inadequate or outdated methods
- **Empirical gaps**: Lack of data in specific contexts
- **Practical gaps**: Limited real-world application

### 4. Platform-Specific Style Learning

**Venue Analysis Process**

For target venues (conferences, journals, archives):
1. Analyze 8-10 sample papers from the venue
2. Extract structural patterns
3. Identify stylistic conventions
4. Note citation and formatting requirements
5. Adapt your paper to match expectations

**Supported Platforms**
- PhilArchive (Philosophy)
- arXiv (Multiple disciplines)
- PhilSci-Archive (Philosophy of Science)
- PsyArXiv (Psychology)
- IEEE/ACM conferences
- Journal-specific requirements

## Workflow Phases

### Phase 1: Research Planning

1. **Define Scope**
   - Research question or hypothesis
   - Target venue and audience
   - Key literature to engage with
   - Methodological approach

2. **Literature Search**
   - Systematic database searches
   - Citation tracking
   - Snowball sampling
   - Grey literature inclusion

3. **Gap Analysis**
   - Map existing research
   - Identify limitations
   - Formulate research questions
   - Justify significance

### Phase 2: Quality Checkpoints

**Checkpoint 1: Outline Review**
- Clear research question
- Logical structure
- Sufficient literature coverage
- Appropriate methodology plan

**Checkpoint 2: Draft Review**
- Complete argumentation
- Adequate evidence
- Proper citations
- Clear writing

**Checkpoint 3: Pre-Submission**
- Full quality assessment
- Format compliance
- Language polishing
- Technical accuracy

### Phase 3: Submission Preparation

1. **Final Evaluation**
   - Run quality check scripts
   - Verify all requirements met
   - Check formatting consistency
   - Review supplementary materials

2. **Cover Letter/Statement**
   - Highlight key contributions
   - Explain significance
   - Address potential concerns
   - Suggest reviewers (if applicable)

## Best Practices

**Literature Review**
- Be systematic and comprehensive
- Use thematic organization
- Critically evaluate sources
- Maintain up-to-date coverage
- Note contradictory findings

**Quality Assessment**
- Be honest about limitations
- Check all claims have support
- Verify citation accuracy
- Ensure reproducibility
- Test all code/analyses

**Writing Quality**
- Use clear, precise language
- Define all technical terms
- Maintain consistent terminology
- Follow style guidelines
- Proofread thoroughly

## Common Issues to Check

**Structural Problems**
- Missing literature connections
- Weak argumentation
- Insufficient methodology detail
- Unsubstantiated claims

**Technical Issues**
- Incorrect citations
- Formatting inconsistencies
- Statistical errors
- Reproducibility problems

**Writing Issues**
- Ambiguous language
- Excessive jargon
- Passive voice overuse
- Poor paragraph structure

## Validation Scripts

When available, use these verification tools:
- `evaluate_samples.py`: Analyze sample papers for style extraction
- `gap_analysis.py`: Validate research gap claims
- `chapter_quality_check.py`: Per-section quality validation
- `final_evaluation.py`: Full manuscript assessment

## Output Formats

Generate analyses in these formats:
- **Structured summaries**: Key points organized by category
- **Comparative tables**: Side-by-side paper comparisons
- **Gap matrices**: Visual representation of research gaps
- **Quality reports**: Scored assessments with recommendations

## Tips for Effective Research

1. **Stay organized**: Use reference management tools
2. **Be systematic**: Follow consistent search and analysis procedures
3. **Take notes**: Document your thinking and insights
4. **Synthesize, don't summarize**: Connect ideas across papers
5. **Stay current**: Regularly update literature reviews
6. **Be critical**: Question assumptions and methods
7. **Seek feedback**: Get input from colleagues and mentors
