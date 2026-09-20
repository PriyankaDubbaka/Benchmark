from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import api_keys, models, documents, benchmarks, results
from .config import get_settings

app = FastAPI(
    title='BAM VLM PDF Extraction Benchmark',
    description='Benchmark open-source VLM models for PDF extraction on BAM certificates',
    version='1.0.0'
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5173', 'http://localhost:3000'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(api_keys.router, prefix='/api')
app.include_router(models.router, prefix='/api')
app.include_router(documents.router, prefix='/api')
app.include_router(benchmarks.router, prefix='/api')
app.include_router(results.router, prefix='/api')

@app.get('/api/health')
async def health():
    return {'status': 'ok', 'service': 'BAM VLM Benchmark'}
