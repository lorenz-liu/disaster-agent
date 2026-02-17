import json
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from typing import Optional, Dict, Any


class LocalLLMExtractor:
    """Handles local LLM inference for patient data extraction."""

    def __init__(self, model_path: str = "/models/gpt-oss-20b"):
        """
        Initialize the local LLM.

        Args:
            model_path: Path to the local model directory
        """
        self.model_path = model_path
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.tokenizer = None

    def load_model(self):
        """Load the model and tokenizer."""
        print(f"Loading model from {self.model_path}...")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            device_map="auto"
        )
        print(f"Model loaded on {self.device}")

    def extract_patient_data(
        self,
        description: str,
        prompt_template: str,
        max_new_tokens: int = 2048,
        temperature: float = 0.1,
    ) -> Optional[Dict[str, Any]]:
        """
        Extract structured patient data from natural language description.

        Args:
            description: Natural language patient description
            prompt_template: Formatted prompt template
            max_new_tokens: Maximum tokens to generate
            temperature: Sampling temperature (lower = more deterministic)

        Returns:
            Extracted patient data as dictionary, or None if extraction fails
        """
        if self.model is None:
            self.load_model()

        # Format the prompt
        prompt = prompt_template.format(description=description)

        # Tokenize
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)

        # Generate
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                do_sample=temperature > 0,
                pad_token_id=self.tokenizer.eos_token_id,
            )

        # Decode
        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Extract JSON from response
        try:
            # Find JSON in the response (between first { and last })
            json_start = generated_text.find("{")
            json_end = generated_text.rfind("}") + 1

            if json_start == -1 or json_end == 0:
                print("No JSON found in response")
                return None

            json_str = generated_text[json_start:json_end]
            patient_data = json.loads(json_str)
            return patient_data

        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON: {e}")
            print(f"Generated text: {generated_text}")
            return None

    def unload_model(self):
        """Unload model to free memory."""
        if self.model is not None:
            del self.model
            del self.tokenizer
            torch.cuda.empty_cache()
            self.model = None
            self.tokenizer = None
