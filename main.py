# main.py
from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

import httpx
from fastapi import FastAPI, HTTPException, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from contextlib import asynccontextmanager

ALPHAFOLD_BASE = "https://alphafold.ebi.ac.uk"
UNIPROT_SEARCH_URL = "https://rest.uniprot.org/uniprotkb/search"
TIMEOUT_SECS = 20.0
RETRIES = 2

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.client = httpx.AsyncClient(timeout=TIMEOUT_SECS)
    try:
        yield
    finally:
        await app.state.client.aclose()

app = FastAPI(
    title="AlphaFold DB FastAPI Wrapper",
    version="1.2.0",
    description="FastAPI wrapper around alphafold.ebi.ac.uk with UniProt gene lookup.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

# ---------- MODELS ----------
class PredictedStructure(BaseModel):
    entryId: str
    uniprotAccession: str
    uniprotId: Optional[str] = None
    organismScientificName: Optional[str] = None
    uniprotStart: Optional[int] = None
    uniprotEnd: Optional[int] = None
    modelCreatedDate: Optional[str] = None
    pdbUrl: Optional[HttpUrl] = None
    cifUrl: Optional[HttpUrl] = None
    paeImageUrl: Optional[HttpUrl] = None
    pLDDT: Optional[float] = None

# ---------- HELPERS ----------
async def _get(client: httpx.AsyncClient, url: str, *, expect_json: bool = True, **params) -> Any:
    last_exc = None
    for attempt in range(RETRIES + 1):
        try:
            r = await client.get(url, params=params)
            r.raise_for_status()
            return r.json() if expect_json else r
        except httpx.HTTPError as exc:
            last_exc = exc
            await asyncio.sleep(0.25 * (attempt + 1))
    raise HTTPException(status_code=502, detail=f"Upstream error: {last_exc}")

# ---------- ROUTES ----------
@app.get("/alphafold/prediction/{uniprot_id}", response_model=List[PredictedStructure])
async def get_prediction(uniprot_id: str, request: Request):
    url = f"{ALPHAFOLD_BASE}/api/prediction/{uniprot_id}"
    data = await _get(request.app.state.client, url)
    if not isinstance(data, list) or len(data) == 0:
        raise HTTPException(status_code=404, detail=f"No prediction found for accession {uniprot_id}.")
    return [PredictedStructure.model_validate(item) for item in data]

@app.get("/alphafold/search/{query}")
async def search_by_gene(query: str, request: Request):
    """
    Cerca un gene o nome proteina su UniProt, ottiene l'accession, poi interroga AlphaFold.
    Esempio:
      /alphafold/search/SLC6A4
    """
    # 1️⃣ Cerca accession in UniProt
    params = {
        "query": query,
        "fields": "accession,gene_names,organism_name,protein_name",
        "format": "json",
        "size": 1
    }
    uni = await _get(request.app.state.client, UNIPROT_SEARCH_URL, **params)
    if not uni.get("results"):
        raise HTTPException(status_code=404, detail=f"No UniProt entry found for query '{query}'.")
    hit = uni["results"][0]
    accession = hit["primaryAccession"]
    gene_names = hit.get("genes", [{}])[0].get("geneName", {}).get("value", "")
    protein_name = hit.get("proteinDescription", {}).get("recommendedName", {}).get("fullName", {}).get("value", "")
    organism = hit.get("organism", {}).get("scientificName", "")

    # 2️⃣ Ottieni struttura AlphaFold
    pred_url = f"{ALPHAFOLD_BASE}/api/prediction/{accession}"
    data = await _get(request.app.state.client, pred_url)
    if not data:
        raise HTTPException(status_code=404, detail=f"No AlphaFold prediction for accession {accession}.")
    model = data[0]

    return {
        "query": query,
        "uniprot_accession": accession,
        "gene_name": gene_names,
        "protein_name": protein_name,
        "organism": organism,
        "pdbUrl": model.get("pdbUrl"),
        "cifUrl": model.get("cifUrl"),
        "pLDDT": model.get("pLDDT"),
        "source": "AlphaFold DB",
    }
