from fastapi import APIRouter,File, UploadFile,HTTPException,Form
from business import converter
from fastapi.responses import FileResponse
import aiofiles
import pandas as pd
from openpyxl import load_workbook
from io import BytesIO

ALLOWED_EXTENSIONS = set(['txt', 'xlsx'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

router = APIRouter()

@router.post("/convert")
async def convert(file: UploadFile = File(None), text: str = Form(None)):
    global rows
    rows = []

    if text and file:
        errors = {'message': "There can only be one request method. You can just use File or Text",
                  'status': False}
        raise HTTPException(status_code=500, detail=errors)
    elif text:
        rows.append(text)
        converter.event_parser(rows)
        return converter.events
    elif file:
        if file.filename and allowed_file(file.filename):
            try:
                converter.events.clear()

                contents = await file.read()
                if file.filename.endswith('.txt'):
                    rows = contents.decode('utf-8').splitlines()
                    rows = [row.split('\t')[0] for row in rows]
                    converter.event_parser(rows)
                elif file.filename.endswith('.xlsx'):
                    rows = converter.xl_to_list(BytesIO(contents))
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
    else:
        errors = {'message': "No Such File",
                  'status': False}
        raise HTTPException(status_code=500, detail=errors)