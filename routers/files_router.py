from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from services.s3_service import s3_service

router = APIRouter(prefix="/files", tags=["files"])


@router.post("/upload")
async def upload_file_to_s3(
    file: UploadFile = File(...),
    folder: str | None = Query(default=None, description="Carpeta/prefijo opcional"),
):
    try:
        file_bytes = await file.read()

        if not file_bytes:
            raise HTTPException(status_code=400, detail="El archivo está vacío.")

        filename = Path(file.filename).name if file.filename else "archivo_sin_nombre"
        object_name = f"{folder.strip('/')}/{filename}" if folder else filename

        uploaded_key = s3_service.upload_bytes(
            data=file_bytes,
            object_name=object_name,
            content_type=file.content_type,
        )

        file_url = s3_service.generate_presigned_url(
            object_name=uploaded_key,
            expires_in=3600,
        )

        return {
            "message": "Archivo subido correctamente.",
            "bucket": s3_service.bucket_name,
            "object_name": uploaded_key,
            "content_type": file.content_type,
            "url": file_url,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error subiendo archivo: {str(e)}")


@router.get("/list", response_model=dict, description="Lista los archivos en el bucket, opcionalmente filtrados por un prefijo/carpetas")
def list_files(
    prefix: str = Query(default="", description="Prefijo/carpeta para filtrar"),
):
    try:
        files = s3_service.list_files(prefix=prefix)

        return {
            "bucket": s3_service.bucket_name,
            "prefix": prefix,
            "count": len(files),
            "files": files,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listando archivos: {str(e)}")