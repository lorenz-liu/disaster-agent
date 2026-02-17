"""
Patient Triage Agent - Main orchestrator for the hybrid LLM + rule-based system.
"""

from typing import Dict, Any, Optional
from pydantic import ValidationError

from schemas import PatientType
from .llm_extractor import LocalLLMExtractor
from .prompts import PATIENT_EXTRACTION_PROMPT
from .validation_rules import validate_patient_data
from .post_processors import post_process_patient_data


class PatientTriageAgent:
    """
    Hybrid agent for extracting structured patient data from natural language.

    Pipeline:
    1. LLM extraction (using local model)
    2. Post-processing (calculate derived fields)
    3. Validation (check medical logic and constraints)
    4. Pydantic validation (ensure schema compliance)
    """

    def __init__(self, model_path: str = "/models/gpt-oss-20b"):
        """
        Initialize the triage agent.

        Args:
            model_path: Path to the local LLM model
        """
        self.llm_extractor = LocalLLMExtractor(model_path=model_path)
        self.model_loaded = False

    def load_model(self):
        """Load the LLM model."""
        if not self.model_loaded:
            self.llm_extractor.load_model()
            self.model_loaded = True

    def unload_model(self):
        """Unload the LLM model to free memory."""
        if self.model_loaded:
            self.llm_extractor.unload_model()
            self.model_loaded = False

    def triage_patient(
        self,
        description: str,
        validate: bool = True,
        verbose: bool = False,
    ) -> Optional[PatientType]:
        """
        Extract structured patient data from natural language description.

        Args:
            description: Natural language patient description
            validate: Whether to run validation rules
            verbose: Whether to print detailed processing information

        Returns:
            PatientType object if successful, None if extraction fails
        """
        if verbose:
            print("=" * 80)
            print("PATIENT TRIAGE AGENT")
            print("=" * 80)
            print(f"\nInput Description:\n{description}\n")

        # Step 1: LLM Extraction
        if verbose:
            print("-" * 80)
            print("Step 1: LLM Extraction")
            print("-" * 80)

        self.load_model()
        raw_data = self.llm_extractor.extract_patient_data(
            description=description,
            prompt_template=PATIENT_EXTRACTION_PROMPT,
        )

        if raw_data is None:
            print("ERROR: LLM extraction failed")
            return None

        if verbose:
            print("✓ LLM extraction successful")

        # Step 2: Post-Processing
        if verbose:
            print("\n" + "-" * 80)
            print("Step 2: Post-Processing")
            print("-" * 80)

        processed_data = post_process_patient_data(raw_data)

        if verbose:
            print("✓ Post-processing complete")
            print(f"  - Acuity: {processed_data.get('acuity')}")
            print(f"  - GCS Total: {processed_data.get('consciousness', {}).get('total_score')}")
            print(f"  - Predicted Death: {processed_data.get('predicted_death_timestamp')}")

        # Step 3: Validation
        if validate:
            if verbose:
                print("\n" + "-" * 80)
                print("Step 3: Validation")
                print("-" * 80)

            is_valid, errors, warnings = validate_patient_data(processed_data)

            if not is_valid:
                print("ERROR: Validation failed")
                for error in errors:
                    print(f"  ✗ {error}")
                return None

            if verbose:
                print("✓ Validation passed")
                if warnings:
                    print("\nWarnings:")
                    for warning in warnings:
                        print(f"  ⚠ {warning}")

        # Step 4: Pydantic Validation
        if verbose:
            print("\n" + "-" * 80)
            print("Step 4: Schema Validation")
            print("-" * 80)

        try:
            patient = PatientType(**processed_data)
            if verbose:
                print("✓ Schema validation successful")
                print("\n" + "=" * 80)
                print("TRIAGE COMPLETE")
                print("=" * 80)
            return patient

        except ValidationError as e:
            print("ERROR: Pydantic validation failed")
            print(e)
            return None

    def triage_batch(
        self,
        descriptions: list[str],
        validate: bool = True,
        verbose: bool = False,
    ) -> list[Optional[PatientType]]:
        """
        Process multiple patient descriptions in batch.

        Args:
            descriptions: List of natural language patient descriptions
            validate: Whether to run validation rules
            verbose: Whether to print detailed processing information

        Returns:
            List of PatientType objects (None for failed extractions)
        """
        self.load_model()  # Load model once for batch processing

        results = []
        for i, description in enumerate(descriptions):
            if verbose:
                print(f"\n\nProcessing patient {i + 1}/{len(descriptions)}")

            patient = self.triage_patient(
                description=description,
                validate=validate,
                verbose=verbose,
            )
            results.append(patient)

        return results

    def __enter__(self):
        """Context manager entry."""
        self.load_model()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.unload_model()
