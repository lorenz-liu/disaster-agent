import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Platform selection: "local" or "openrouter"
PLATFORM = "openrouter"

# Local model configuration (used when PLATFORM = "local")
LOCAL_MODEL_PATH = "./model"
LOCAL_MODEL_GPU_MEMORY_UTILIZATION = 0.9
LOCAL_MODEL_TENSOR_PARALLEL_SIZE = 1

# OpenRouter configuration (used when PLATFORM = "openrouter")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = "openai/gpt-oss-20b"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Generation parameters
GENERATION_MAX_TOKENS = 2048
GENERATION_TEMPERATURE = 0.1
GENERATION_TOP_P = 0.95
