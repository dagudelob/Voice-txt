from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url=os.getenv("LOCAL_API_BASE"),
    api_key=os.getenv("OPENAI_API_KEY", "lm-studio")
)

try:
    response = client.chat.completions.create(
        model=os.getenv("LLM_MODEL"),
        messages=[{"role": "user", "content": "Hola, ¿estás funcionando?"}],
        max_tokens=10
    )
    print("SUCCESS: Conexión establecida con LM Studio.")
    print(f"Respuesta: {response.choices[0].message.content}")
except Exception as e:
    print(f"FAILURE: No se pudo conectar con LM Studio. Error: {e}")
