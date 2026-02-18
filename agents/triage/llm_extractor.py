"""
LLM Extractor with support for local (vLLM) and OpenRouter platforms.
"""

import json
import os
from typing import Optional, Dict, Any


class LLMExtractor:
    """Handles LLM inference for patient data extraction."""

    def __init__(self, platform: str = "local", **kwargs):
        """
        Initialize the LLM extractor.

        Args:
            platform: "local" for vLLM or "openrouter" for API
            **kwargs: Platform-specific configuration
        """
        self.platform = platform.lower()

        if self.platform == "local":
            self._init_local(**kwargs)
        elif self.platform == "openrouter":
            self._init_openrouter(**kwargs)
        else:
            raise ValueError(f"Unknown platform: {platform}. Use 'local' or 'openrouter'")

    def _init_local(self, model_path: str = "/models/gpt-oss-20b", **kwargs):
        """Initialize local vLLM."""
        try:
            from vllm import LLM, SamplingParams
        except ImportError:
            raise ImportError(
                "vLLM is required for local inference. Install with: pip install vllm"
            )

        self.model_path = model_path
        self.llm = None
        self.sampling_params_class = SamplingParams
        self.gpu_memory_utilization = kwargs.get("gpu_memory_utilization", 0.9)
        self.tensor_parallel_size = kwargs.get("tensor_parallel_size", 1)

    def _init_openrouter(
        self,
        api_key: Optional[str] = None,
        model: str = "openai/gpt-oss-20b",
        base_url: str = "https://openrouter.ai/api/v1",
        **kwargs
    ):
        """Initialize OpenRouter API client."""
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "OpenAI SDK is required for OpenRouter. Install with: pip install openai"
            )

        # Get API key from parameter or environment
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenRouter API key required. Set OPENROUTER_API_KEY in config.py or environment"
            )

        self.model = model
        self.client = OpenAI(
            base_url=base_url,
            api_key=self.api_key,
        )

    def load_model(self):
        """Load the model (only needed for local platform)."""
        if self.platform == "local":
            if self.llm is None:
                from vllm import LLM

                print(f"Loading vLLM model from {self.model_path}...")
                self.llm = LLM(
                    model=self.model_path,
                    gpu_memory_utilization=self.gpu_memory_utilization,
                    tensor_parallel_size=self.tensor_parallel_size,
                )
                print("vLLM model loaded successfully")
        elif self.platform == "openrouter":
            print("Using OpenRouter API (no model loading required)")

    def extract_patient_data(
        self,
        description: str,
        prompt_template: str,
        max_new_tokens: int = 4096,
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
        # Format the prompt
        prompt = prompt_template.format(description=description)

        # Generate based on platform
        if self.platform == "local":
            generated_text = self._generate_local(prompt, max_new_tokens, temperature)
        elif self.platform == "openrouter":
            generated_text = self._generate_openrouter(prompt, max_new_tokens, temperature)
        else:
            return None

        if generated_text is None:
            return None

        # Extract JSON from response
        return self._extract_json(generated_text)

    def _generate_local(
        self, prompt: str, max_tokens: int, temperature: float
    ) -> Optional[str]:
        """Generate using local vLLM."""
        if self.llm is None:
            self.load_model()

        sampling_params = self.sampling_params_class(
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=0.95,
        )

        outputs = self.llm.generate([prompt], sampling_params)
        if outputs and len(outputs) > 0:
            return outputs[0].outputs[0].text
        return None

    def _generate_openrouter(
        self, prompt: str, max_tokens: int, temperature: float
    ) -> Optional[str]:
        """Generate using OpenRouter API."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=0.95,
            )

            if response.choices and len(response.choices) > 0:
                return response.choices[0].message.content
            return None

        except Exception as e:
            print(f"OpenRouter API error: {e}")
            return None

    def _extract_json(self, generated_text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from generated text."""
        try:
            # Find JSON in the response (between first { and last })
            json_start = generated_text.find("{")
            json_end = generated_text.rfind("}") + 1

            if json_start == -1 or json_end == 0:
                print("No JSON found in response")
                print(f"Generated text: {generated_text[:500]}...")
                return None

            json_str = generated_text[json_start:json_end]
            patient_data = json.loads(json_str)
            return patient_data

        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON: {e}")
            print(f"Generated text: {generated_text[:500]}...")
            return None

    def unload_model(self):
        """Unload model to free memory (only for local platform)."""
        if self.platform == "local" and self.llm is not None:
            del self.llm
            self.llm = None
            print("vLLM model unloaded")
