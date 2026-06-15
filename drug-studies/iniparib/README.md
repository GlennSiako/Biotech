# Iniparib Drug Failure Analysis

## Overview
This directory contains analysis and documentation of the iniparib drug failure case study.

## Drug Information
- **Drug Name**: Iniparib (BSI-201, SAR240550)
- **Target**: PARP1 (Poly [ADP-ribose] polymerase 1)
- **Indication**: Triple-negative breast cancer (TNBC), ovarian cancer
- **Status**: Clinical trial failure

## Key Findings
Iniparib progressed to Phase III clinical trials as a purported PARP1 inhibitor but showed lack of efficacy. Post-termination studies confirmed that **iniparib does not engage PARP1 in cells**, making it a notable case study in drug development failures and target validation.

## Phase History
- **Phase II**: Showed promising results in triple-negative breast cancer
- **Phase III**: Failed to demonstrate significant efficacy in expanded trials
- **Phase III (lung cancer)**: Failed to show significant results in squamous non-small cell lung cancer
- **Phase II (ovarian cancer)**: Failed in platinum-resistant ovarian cancer trials

## Contents
- `Iniparib_Failure_Analysis.ipynb` - Jupyter notebook with analysis using PubMed, PubChem, and AlphaFold data

## Analysis Tools & Methods
- **PubMed Search**: Identifies failed clinical trial articles
- **PubChem Integration**: Retrieves compound information
- **NLP Analysis**: Extracts failure reasons from abstracts using spaCy
- **AlphaFold Integration**: Retrieves and visualizes target protein structures

## Dependencies
- biopython
- py3Dmol
- spacy
- requests
- matplotlib
- numpy

## References
- Javle M, Curtin NJ. "The potential for poly (ADP-ribose) polymerase inhibitors in cancer therapy." Ther Adv Med Oncol. 2011 Nov;3(6):257-67.
- PMID: 22084640
- DOI: 10.1177/1758834011417039
