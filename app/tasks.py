import logging
from app.celery_worker import celery
import httpx
import asyncio
import requests
import json
from app.settings import API_KEY
from redis import Redis


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

redis_client = Redis(host='redis', port=6379, db=1)

@celery.task(bind=True)
def process_request(self, message, callback_url):
    logger.info(f"Началась обработка сообщения: {message}")

    # Генерация уникального идентификатора пользователя для отслеживания истории
    user_id = f"user:{callback_url}"
    logger.debug(f"Сгенерирован идентификатор пользователя: {user_id}")

    # Получение истории сообщений из Redis
    history = redis_client.get(user_id)
    if history:
        history = json.loads(history)
        logger.info(f"История для {user_id} получена.")
    else:
        history = []
        logger.info(f"История для {user_id} не найдена. Создается новая история.")

    # Добавление нового сообщения пользователя в историю
    history.append({"role": "user", "content": message})
    logger.debug(f"Обновленная история: {history}")

    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
            },
            data=json.dumps({
                "model": "openai/gpt-3.5-turbo-1106",
                "messages": history
            })
        )
        response.raise_for_status()
        response_content = response.json()['choices'][0]['message']['content']
        logger.info("Ответ от внешней службы получен.")

        history.append({"role": "assistant", "content": response_content})
        redis_client.set(user_id, json.dumps(history))
        logger.info(f"Обновленная история сохранена для {user_id}.")

        # Отправка ответа по callback URL
        response_data = {"generated_response": response_content}
        
        async def send_callback(response, callback_url):
            async with httpx.AsyncClient() as client:
                try:
                    resp = await client.post(callback_url, json=response)
                    resp.raise_for_status()
                    logger.info(f"Успешно отправлено на {callback_url}: {resp.status_code}")
                except httpx.HTTPStatusError as exc:
                    logger.error(f"HTTP ошибка при отправке на {callback_url}: {exc}")
                except httpx.RequestError as exc:
                    logger.error(f"Ошибка запроса при отправке на {callback_url}: {exc}")

        loop = asyncio.get_event_loop()
        loop.run_until_complete(send_callback(response_data, callback_url))

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при взаимодействии с внешней службой: {e}")
        raise