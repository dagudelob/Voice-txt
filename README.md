# Voice-Txt (Text-to-Voice application)

Voice-Txt es una aplicación ligera y rápida para transformar voz a texto y autocompletar en cualquier lugar del sistema. Graba tu voz presionando un atajo de teclado, procesa el audio usando un modelo de Speech-to-Text (STT), luego corrige y limpia el texto usando un Large Language Model (LLM), y finalmente lo inyecta directamente donde tengas el cursor escribiendo.

## ¿Cómo funciona la aplicación?

El flujo principal de la aplicación opera en 3 pasos:

1. **Grabación**: Cuando presionas el atajo de teclado configurado (por ejemplo, `Ctrl + Espacio`), la aplicación comienza a grabar el audio de tu micrófono. Al soltar la combinación de teclas, detiene la grabación y guarda temporalmente el archivo de audio.
2. **Transcripción (STT)**: El archivo de audio se transcribe a texto en bruto usando un modelo de reconocimiento de voz. Esto puede hacerse de manera local (usando el modelo Whisper original de OpenAI en tu computadora) o usando la **API de Groq** con el modelo super rápido `whisper-large-v3-turbo` en la nube.
3. **Corrección (LLM)**: El texto transcrito a menudo contiene muletillas, pausas o errores menores. La aplicación envía este texto crudo a un LLM configurado (ej. `gpt-4o-mini` de OpenAI, o un modelo local vía LM Studio/Ollama) junto con un *prompt* que le pide ser un "editor experto" y limpiarlo.
4. **Inyección**: Finalmente, la aplicación copia el texto corregido al portapapeles y simula un `Ctrl + V` para pegarlo automáticamente en tu ventana activa.

Además, cuenta con una interfaz web (Dashboard) desde donde podrás ver los logs, hacer pruebas de micrófono y monitorear el estado de la aplicación.

## Requisitos y Configuración Inicial

Para que Voice-Txt funcione, necesitas configurar un archivo llamado `.env` en la raíz del proyecto. Este archivo contendrá las configuraciones de modelo, atajos y, lo más importante, tus **API Keys**. Puedes basarte en el archivo `.env.example` proporcionado.

### Configuración de las API Keys

Debes colocar tus claves privadas en las siguientes variables del `.env`:

*   `OPENAI_API_KEY`: Tu clave privada de la API de OpenAI. Esta se utiliza por defecto para el servicio de **corrección LLM** (si configuras `LLM_MODEL=gpt-4o-mini`, u otro modelo de OpenAI). Si usas un LLM local y Groq Whisper, esta key no será consumida por OpenAI o puede ser un valor cualquiera.
*   `GROQ_API_KEY`: Tu clave privada de la API de Groq obtenida desde [Groq Console](https://console.groq.com/docs/overview). Esta se utilizará para acelerar drásticamente el reconocimiento de voz (STT) usando su modelo `whisper-large-v3-turbo`.

### Configuración de Modelos (STT y LLM)

La aplicación tiene dos etapas impulsadas por IA que puedes configurar a tu gusto.

**1. Modelo de Transcripción (STT - Speech to Text)**
La configuración del STT se controla mediante el parámetro `USE_GROQ_STT`:
*   Para usar **Groq API (Recomendado, muy rápido):**
    ```env
    USE_GROQ_STT=true
    GROQ_API_KEY=tu_clave_de_groq_aqui
    ```
    *Esto utilizará internamente el modelo `whisper-large-v3-turbo` en los servidores de Groq.*

*   Para usar **Whisper Local (En tu computadora, no requiere internet para STT):**
    ```env
    USE_GROQ_STT=false
    ```
    *Esto cargará el modelo local de Whisper en la RAM/VRAM la primera vez que inicies la app.*

**2. Modelo de Corrección y Limpieza (LLM)**
*   Para usar **OpenAI (Ej. gpt-4o-mini o gpt-4o):**
    ```env
    USE_LOCAL_MODEL=false
    OPENAI_API_KEY=tu_clave_de_openai_aqui
    LLM_MODEL=gpt-4o-mini
    ```

*   Para usar **Modelos Locales (Ej. Ollama o LM Studio):**
    ```env
    USE_LOCAL_MODEL=true
    LOCAL_API_BASE=http://127.0.0.1:1234/v1  # O el puerto que use tu servicio (ej. :11434 para Ollama)
    LLM_MODEL=qwen/qwen3-vl-4b               # O el nombre del modelo que tengas localmente
    OPENAI_API_KEY=sk-local                  # Variable temporal, no importa su valor real.
    ```

### Otras Configuraciones del `.env`

*   `HOTKEY`: Atajo que inicia y finaliza la grabación (Ej. `ctrl_l+space`).
*   `CORRECTION_PROMPT`: El comando que se le pasa al LLM para indicarle cómo debe actuar al corregir el texto bruto.
*   `DASHBOARD_PORT`: El puerto donde se levantará la interfaz local (ej. `8005`).

## Uso de la Aplicación

1.  Ejecuta la aplicación principal (ej. `python main.py`).
2.  Al iniciar, cargará los modelos si has optado por versiones locales. Aparecerá el icono en la barra de tareas.
3.  Mantén presionado tu `HOTKEY` (por defecto `Ctrl + Espacio`).
4.  Comienza a hablar.
5.  Suelta el atajo al terminar.
6.  Voice-Txt procesará el audio, corregirá el texto, y lo escribirá instantáneamente por ti en la caja de texto activa en tu pantalla.
