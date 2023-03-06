from fastapi import APIRouter,File, UploadFile,HTTPException
from business import converter
from fastapi.responses import FileResponse
import aiofiles


ALLOWED_EXTENSIONS = set(['txt', 'xlsx'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

router = APIRouter()

@router.post("/convert")
async def convert(file: UploadFile = File(...)):
    if file.filename and allowed_file(file.filename):
        try:
            global rows
            rows = []

            contents = await file.read()
            if file.filename.endswith('.txt'):
                # Dosya TXT ise
                rows = contents.decode('utf-8').splitlines()
                rows = [row.split('\t') for row in rows]
                converter.events.clear()
                converter.event_parser(rows)
            return converter.events

        except Exception as e:
            raise HTTPException(status_code=500, detail=e)
    elif not (file.filename):
        errors = {'message': "No Such File",
                  'status': False}
        raise HTTPException(status_code=500, detail=errors)
    elif not (allowed_file(file.filename)):
        errors = {'message': "Incorrect File Extension",
                  'status': False}
        raise HTTPException(status_code=500, detail=errors)