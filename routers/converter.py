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
            path = ('case.'+file.filename.rsplit('.', 1)[1].lower())

            async with aiofiles.open(path, 'wb') as out_file:
                content = await file.read()  # async read
                await out_file.write(content)  # async write
            converter.run(path)
            return FileResponse('events.json')

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