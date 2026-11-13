# Mind the Boundary: Survey and Interview Materials

This repository contains the materials for the paper *Mind the Boundary: Practices and Decision Rationales for Privacy Transformations in Data Pipelines* (under review).
The study follows an explanatory sequential design: an online survey of practitioners, followed by five semi-structured interviews.

## Research Questions

- **RQ1:** How do practitioners report implementing and placing privacy transformations in data-sharing pipelines?
- **RQ2:** How do practitioners explain privacy-related integration decisions in relation to downstream functions and existing pipeline conditions?
- **RQ3:** What forms of reuse and barriers do practitioners report for pipeline transformations?

## Repository Contents

| File | Content |
|------|---------|
| `exportSurvey.csv` | Survey responses exported from the survey platform |
| `eval.py` | Script for the survey analysis |
| `interview-questions.md` | Interview guide |
| `InterviewAnalysisMatrix_EN.xlsx` | Interview analysis matrix (English) |
| `InterviewanalyseMatrix.xlsx` | Interview analysis matrix (German) |

Since our original interview analysis matrix is in German, we used Opus 5.5 to provide an English translation for the benefit of all readers.

## Survey

- The questionnaire contains 29 questions in total.
- **Questions for RQ1:** Q8 asks which mechanisms respondents use to support privacy. Respondents who selected anonymization were directed to Q9–Q11 on the techniques they used, how they implemented them, and where they applied them in their pipelines.
- **Questions for RQ3:** Q12–Q15 cover what respondents consider reuse, how often transformation stages are duplicated, which reuse mechanisms exist, and what limits reuse.
- **Distribution:** before distribution, we tested the questionnaire and revised the wording and order of the questions. It ran on a self-hosted Formbricks instance and was distributed in September 2026 through university alumni mailing lists and professional forums.
- **Responses:** of 29 recorded responses, we excluded three respondents who selected anonymization in Q8 but have no recorded answers to Q9–Q11. The analysis therefore covers 29 responses, 13 of which answered Q9–Q11.
- **Reporting:** multiple-choice answers are reported in the questionnaire's categories. The category *anonymization* includes pseudonymization and encryption.

## Interviews

- We conducted five semi-structured interviews (P1–P5). They were held remotely and lasted approximately 20–35 minutes.
- **Participants:**
  - P1: a research team lead in healthcare
  - P2: a CTO in AI data tooling
  - P3: a project lead of a non-profit e-learning platform
  - P4: an engineer in metering
  - P5: a VP of engineering at an energy-management company
- **Interview guide:** `interview-questions.md` contains the guide. Interviewees' individual survey responses were not accessed or linked to their interviews. Survey results entered the interviews only as aggregated preliminary patterns.
- **Transcripts:** the recordings were transcribed locally with noScribe. Recordings and transcripts are not published.
- **Analysis matrix:** for each decision situation, it records the downstream task, the information that task needed, the reported constraint, the decision, and any reported or expected consequence.
- **LLM support:** the analysis was informed by Morgan's query-based approach and supported by ChatGPT and Claude. All interpretations were checked against the transcripts by the author.

## Running the Survey Analysis

```
python eval.py
```

## Privacy

- Respondents could provide an email address to volunteer for an interview. These addresses are not included in this repository.
- Interviewees are referred to only as P1–P5, and the names of their organizations are not included.
- To protect the Interviewees, we do not share the recorded audio or the transcript text of the interviews.

## Citation

The citation will be added after the review.