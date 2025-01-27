from typing import Optional
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sys
from io import StringIO
import contextlib
import traceback

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"]
)

class ScriptRequest(BaseModel):
    guid: str
    script: str

@app.get("/")
def read_root():
    return {"message": "Hit /execute to run a script"}

@app.post("/execute")
async def execute_script(request: ScriptRequest):
    try:
        # Create string buffer to capture stdout
        output_buffer = StringIO()
        
        # Create a safe namespace for script execution
        namespace = {
            '__builtins__': {
                name: getattr(__builtins__, name)
                for name in ['abs', 'all', 'any', 'bin', 'bool', 'dict', 'float', 
                           'int', 'len', 'list', 'max', 'min', 'range', 'round', 
                           'str', 'sum', 'tuple', 'zip']
            }
        }

        # Capture stdout and execute script
        with contextlib.redirect_stdout(output_buffer):
            try:
                exec(request.script, namespace)
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": str(e),
                        "traceback": traceback.format_exc()
                    }
                )

        # Get stdout and output variable
        stdout = output_buffer.getvalue()
        script_output = namespace.get("output", None)

        return {
            "guid": request.guid,
            "stdout": stdout,
            "output": script_output,
            "success": True
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error occurred",
                "message": str(e)
            }
        )