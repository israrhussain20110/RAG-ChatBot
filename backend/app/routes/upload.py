import uuid
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from ..services import ingestion

router = APIRouter()

@router.post("/api/v1/upload")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    try:
        content = await file.read()
        doc_id = str(uuid.uuid4())
        
        # Add the ingestion task to be run in the background
        background_tasks.add_task(ingestion.ingest_document, doc_id, file.filename, content)
        
        return {"doc_id": doc_id, "filename": file.filename, "status": "queued_for_ingestion"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {e}")