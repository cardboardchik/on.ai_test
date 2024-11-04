from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, HttpUrl
from app.tasks import process_request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address


app = FastAPI()
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)

class WebhookRequest(BaseModel):
    message: str
    callback_url: HttpUrl

class CallbackRequest(BaseModel):
    generated_response: str

# Обработчик ошибок валидации
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": exc.body}
    )

@app.post("/webhook")
@limiter.limit("5/minute")
async def handle_webhook(request: Request, webhook_request: WebhookRequest):
    try:
        task = process_request.apply_async((webhook_request.message, str(webhook_request.callback_url)))
        return {"task_id": task.id, "status": "Processing"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обработки запроса: {str(e)}")


@app.post("/callback")
async def callback(request: CallbackRequest):
    try:
        return {"generated_response": request.generated_response, "status": status.HTTP_200_OK}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обработки запроса: {str(e)}")