# AlphaFold-api
Access to AlphaFold Protein Structure Database via FastAPI

AlphaFold (Protein Structure Database) developed by Google DeepMind and EMBL-EBI is the first Ai that wins the 20024 Chemistry Nobel 
solving a 50-year-old grand challenge in biology — predicting a protein’s 3D structure directly from its amino acid sequence.
What once took years of laboratory experiments can now be done in minutes, with atomic-level accuracy.

Technically, AlphaFold2 works by combining:
- Massive databases of protein sequences and structures https://alphafold.ebi.ac.uk/
- Deep neural networks (transformers) that learn how amino acids co-evolve
- Geometry-aware modules that predict how residues fold into a stable 3D form

An AI system that accurately predicts the structure of nearly every known protein on Earth, opening new frontiers in drug design, enzyme engineering, and synthetic biology.

# 🔬 AlphaFold FastAPI Wrapper

A lightweight **FastAPI microservice** that wraps the public **AlphaFold DB** and **UniProt REST APIs**.

It lets you:
- Search by **gene or protein name** (e.g. `SLC6A4`, `TP53`, `ACE2`)  
- Automatically resolve the **UniProt accession**
- Fetch AlphaFold **3D structure metadata**
- Optionally download the predicted **PDB/mmCIF** file

---

## 🚀 Features
- `/alphafold/search/{query}` → search by gene/protein name (UniProt + AlphaFold)
- `/alphafold/prediction/{accession}` → direct AlphaFold prediction lookup
- `/alphafold/structure/{accession}` → download structure file (`.pdb` or `.cif`)
- Built-in retry logic and JSON error handling
- CORS enabled for front-end integration
- Simple, async architecture using `httpx`

---

## 🧰 Requirements
- Python ≥ 3.9  
- Works on Linux, macOS, or GCP VM

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Start FastAPI server
uvicorn main:app --host 0.0.0.0 --port 8000

An example to call the Insuline protein generating file JSON and PDB :

curl -s http://127.0.0.1:8000/alphafold/search/INS -o INS.json && \
( jq -r '.pdbUrl // empty' INS.json | xargs -r -I{} sh -c 'curl -L "{}" -o "$(basename "{}")"' )



