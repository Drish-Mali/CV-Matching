import httpx
from langchain.llms.base import LLM
from config.config import settings
from pydantic import ValidationError
from schemas.llm import PostData, Message
import os
from dotenv import load_dotenv
load_dotenv()
class LLMService(LLM):
    API_BASE_URL = "https://api.openai.com/v1"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
    }

    max_tokens_to_generate = settings.model_parameters.max_tokens_to_generate
    temperature = settings.model_parameters.temperature
    top_p_value = settings.model_parameters.top_p_value
    top_k_value = settings.model_parameters.top_k_value
    stopwords = settings.model_parameters.stopwords
    presence_penalty = settings.model_parameters.presence_penalty
    frequency_penalty = settings.model_parameters.frequency_penalty

    @property
    def _llm_type(self) -> str:
        return settings.default.model_name

    def _call(self, prompt, stop=None) -> str:
        raise NotImplementedError("Synchronous call not implemented")

    async def _acall(self, prompt, stop=None, **kwargs) -> str:
        stopwords = kwargs.get("stopwords") or self.stopwords
        if stop is not None:
            raise ValueError("Stop kwargs are not permitted.")

        print("THE INPUT PROMPT IS:", prompt)

        post_data = PostData(
            model=settings.default.model_name,
            messages=[Message(role="user", content=prompt)],
            max_tokens=self.max_tokens_to_generate,
            temperature=self.temperature,
            top_p=self.top_p_value,
            n=1,
            stop=stopwords,
            stream=False,
            presence_penalty=self.presence_penalty,
            frequency_penalty=self.frequency_penalty,
            logit_bias=None,
        )

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url=f"{self.API_BASE_URL}/chat/completions",
                    headers=self.headers,
                    data=post_data.json(),
                    timeout=120.0,
                )
                response.raise_for_status()
                result = response.json().get("choices")[0]["message"]["content"]
                print("Valid Result")
                print(result)

        except ValidationError as e:
            print(f"Validation error occurred: {e}")
            result = "Validation error occurred"
        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e.response.status_code}")
            result = "HTTP error occurred"
        except httpx.RequestError as e:
            print(f"Request error occurred: {e}")
            result = "Request error occurred"
        except Exception as e:
            print(f"An error occurred: {e}")
            result = "An error occurred"

        return result