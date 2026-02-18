"""
OpenAI function/tool schema definition for structured patient data extraction.
This ensures the LLM outputs valid JSON matching our Pydantic schema.
"""

PATIENT_EXTRACTION_TOOL = {
    "type": "function",
    "function": {
        "name": "extract_patient_data",
        "description": "Extract structured patient triage data from natural language description using SALT protocol",
        "parameters": {
            "type": "object",
            "properties": {
                "patient_id": {
                    "type": "null",
                    "description": "Patient ID (always set to null, will be auto-generated)"
                },
                "name": {
                    "type": "string",
                    "description": "Patient name (use 'Unknown' if not provided)"
                },
                "age": {
                    "type": "integer",
                    "description": "Patient age in years"
                },
                "gender": {
                    "type": "string",
                    "enum": ["Male", "Female", "Unknown"],
                    "description": "Patient gender"
                },
                "salt_assessment": {
                    "type": "object",
                    "properties": {
                        "can_walk": {
                            "type": "boolean",
                            "description": "SALT Sort: Can the patient walk when asked?"
                        },
                        "can_wave": {
                            "type": "boolean",
                            "description": "SALT Sort: Can the patient wave?"
                        },
                        "obeys_commands": {
                            "type": "boolean",
                            "description": "SALT Assess: Does the patient follow commands?"
                        },
                        "has_peripheral_pulse": {
                            "type": "boolean",
                            "description": "SALT Assess: Does the patient have a peripheral pulse?"
                        },
                        "in_respiratory_distress": {
                            "type": "boolean",
                            "description": "SALT Assess: Is the patient in respiratory distress?"
                        },
                        "hemorrhage_controlled": {
                            "type": "boolean",
                            "description": "SALT Assess: Is major hemorrhage controlled?"
                        },
                        "lifesaving_intervention_performed": {
                            "type": "string",
                            "description": "SALT LSI: Description of lifesaving interventions performed, or empty string if none"
                        }
                    }
                },
                "vital_signs": {
                    "type": "object",
                    "properties": {
                        "heart_rate": {
                            "type": "integer",
                            "description": "Heart rate in beats per minute"
                        },
                        "blood_pressure": {
                            "type": "object",
                            "properties": {
                                "systolic": {
                                    "type": "integer",
                                    "description": "Systolic blood pressure in mmHg"
                                },
                                "diastolic": {
                                    "type": "integer",
                                    "description": "Diastolic blood pressure in mmHg"
                                }
                            }
                        },
                        "respiratory_rate": {
                            "type": "integer",
                            "description": "Respiratory rate in breaths per minute"
                        },
                        "oxygen_saturation": {
                            "type": "integer",
                            "description": "Oxygen saturation percentage (0-100)"
                        },
                        "temperature": {
                            "type": "number",
                            "description": "Body temperature in Celsius"
                        }
                    }
                },
                "consciousness": {
                    "type": "object",
                    "properties": {
                        "eye_response": {
                            "type": "integer",
                            "description": "Glasgow Coma Scale eye response (1-4)",
                            "minimum": 1,
                            "maximum": 4
                        },
                        "verbal_response": {
                            "type": "integer",
                            "description": "Glasgow Coma Scale verbal response (1-5)",
                            "minimum": 1,
                            "maximum": 5
                        },
                        "motor_response": {
                            "type": "integer",
                            "description": "Glasgow Coma Scale motor response (1-6)",
                            "minimum": 1,
                            "maximum": 6
                        },
                        "total_score": {
                            "type": "integer",
                            "description": "Glasgow Coma Scale total score (3-15)",
                            "minimum": 3,
                            "maximum": 15
                        }
                    }
                },
                "acuity": {
                    "type": "string",
                    "enum": ["Dead", "Expectant", "Immediate", "Delayed", "Minimal", "Undefined"],
                    "description": "SALT triage category"
                },
                "injuries": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "locations": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["Head", "Neck", "Chest", "Back", "Pelvis", "Abdomen", "Limbs (Upper)", "Limbs (Lower)"]
                                },
                                "description": "Body locations affected by this injury"
                            },
                            "mechanisms": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["Blunt", "Penetrating", "Thermal", "Blast", "Drowning", "Chemical", "Radiation", "Electrical", "Hypothermia", "Other"]
                                },
                                "description": "Injury mechanisms"
                            },
                            "severity": {
                                "type": "string",
                                "enum": ["Dead", "Expectant", "Immediate", "Delayed", "Minimal"],
                                "description": "Injury severity level"
                            },
                            "description": {
                                "type": "string",
                                "description": "Detailed description of the injury"
                            }
                        },
                        "required": ["locations", "mechanisms", "severity", "description"]
                    },
                    "description": "Array of injuries"
                },
                "required_medical_capabilities": {
                    "type": "object",
                    "properties": {
                        "trauma_center": {"type": "boolean"},
                        "neurosurgical": {"type": "boolean"},
                        "orthopedic": {"type": "boolean"},
                        "ophthalmology": {"type": "boolean"},
                        "burn": {"type": "boolean"},
                        "pediatric": {"type": "boolean"},
                        "obstetric": {"type": "boolean"},
                        "cardiac": {"type": "boolean"},
                        "thoracic": {"type": "boolean"},
                        "vascular": {"type": "boolean"},
                        "ent": {"type": "boolean"},
                        "hepatobiliary": {"type": "boolean"}
                    },
                    "description": "Required medical capabilities for treating this patient"
                },
                "required_medical_resources": {
                    "type": "object",
                    "properties": {
                        "ward": {"type": "integer"},
                        "ordinary_icu": {"type": "integer"},
                        "operating_room": {"type": "integer"},
                        "ventilator": {"type": "integer"},
                        "prbc_unit": {"type": "integer"},
                        "isolation": {"type": "integer"},
                        "decontamination_unit": {"type": "integer"},
                        "ct_scanner": {"type": "integer"},
                        "oxygen_cylinder": {"type": "integer"},
                        "interventional_radiology": {"type": "integer"}
                    },
                    "description": "Required medical resources (quantities)"
                },
                "description": {
                    "type": "string",
                    "description": "Original or summarized patient description"
                },
                "predicted_death_timestamp": {
                    "type": "integer",
                    "description": "Unix timestamp of predicted death (0 if low risk)"
                },
                "status": {
                    "type": "string",
                    "enum": ["Unassigned", "Awaiting Transfer", "In-Transfer", "Arrived"],
                    "description": "Patient status"
                },
                "assigned_facility": {
                    "type": "string",
                    "description": "ID of assigned healthcare facility (empty string if none)"
                },
                "action_logs": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Log of actions taken for this patient"
                },
                "deceased": {
                    "type": "boolean",
                    "description": "Whether the patient is deceased"
                },
                "location": {
                    "type": "object",
                    "properties": {
                        "latitude": {"type": "number", "description": "Latitude coordinate"},
                        "longitude": {"type": "number", "description": "Longitude coordinate"}
                    },
                    "description": "Patient location coordinates"
                }
            },
            "required": ["description"]
        }
    }
}
