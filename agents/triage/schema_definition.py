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
                    "type": ["string", "null"],
                    "description": "Patient ID (leave as null, will be auto-generated)"
                },
                "name": {
                    "type": ["string", "null"],
                    "description": "Patient name (use 'Unknown' if not provided)"
                },
                "age": {
                    "type": ["integer", "null"],
                    "description": "Patient age in years"
                },
                "gender": {
                    "type": ["string", "null"],
                    "enum": ["Male", "Female", "Unknown", None],
                    "description": "Patient gender"
                },
                "salt_assessment": {
                    "type": ["object", "null"],
                    "properties": {
                        "can_walk": {
                            "type": ["boolean", "null"],
                            "description": "SALT Sort: Can the patient walk when asked?"
                        },
                        "can_wave": {
                            "type": ["boolean", "null"],
                            "description": "SALT Sort: Can the patient wave?"
                        },
                        "obeys_commands": {
                            "type": ["boolean", "null"],
                            "description": "SALT Assess: Does the patient follow commands?"
                        },
                        "has_peripheral_pulse": {
                            "type": ["boolean", "null"],
                            "description": "SALT Assess: Does the patient have a peripheral pulse?"
                        },
                        "in_respiratory_distress": {
                            "type": ["boolean", "null"],
                            "description": "SALT Assess: Is the patient in respiratory distress?"
                        },
                        "hemorrhage_controlled": {
                            "type": ["boolean", "null"],
                            "description": "SALT Assess: Is major hemorrhage controlled?"
                        },
                        "lifesaving_intervention_performed": {
                            "type": ["string", "null"],
                            "description": "SALT LSI: Description of lifesaving interventions performed"
                        }
                    }
                },
                "vital_signs": {
                    "type": ["object", "null"],
                    "properties": {
                        "heart_rate": {
                            "type": ["integer", "null"],
                            "description": "Heart rate in beats per minute"
                        },
                        "blood_pressure": {
                            "type": ["object", "null"],
                            "properties": {
                                "systolic": {
                                    "type": ["integer", "null"],
                                    "description": "Systolic blood pressure in mmHg"
                                },
                                "diastolic": {
                                    "type": ["integer", "null"],
                                    "description": "Diastolic blood pressure in mmHg"
                                }
                            }
                        },
                        "respiratory_rate": {
                            "type": ["integer", "null"],
                            "description": "Respiratory rate in breaths per minute"
                        },
                        "oxygen_saturation": {
                            "type": ["integer", "null"],
                            "description": "Oxygen saturation percentage (0-100)"
                        },
                        "temperature": {
                            "type": ["number", "null"],
                            "description": "Body temperature in Celsius"
                        }
                    }
                },
                "consciousness": {
                    "type": ["object", "null"],
                    "properties": {
                        "eye_response": {
                            "type": ["integer", "null"],
                            "description": "Glasgow Coma Scale eye response (1-4)",
                            "minimum": 1,
                            "maximum": 4
                        },
                        "verbal_response": {
                            "type": ["integer", "null"],
                            "description": "Glasgow Coma Scale verbal response (1-5)",
                            "minimum": 1,
                            "maximum": 5
                        },
                        "motor_response": {
                            "type": ["integer", "null"],
                            "description": "Glasgow Coma Scale motor response (1-6)",
                            "minimum": 1,
                            "maximum": 6
                        },
                        "total_score": {
                            "type": ["integer", "null"],
                            "description": "Glasgow Coma Scale total score (3-15)",
                            "minimum": 3,
                            "maximum": 15
                        }
                    }
                },
                "acuity": {
                    "type": ["string", "null"],
                    "enum": ["Dead", "Expectant", "Immediate", "Delayed", "Minimal", "Undefined", None],
                    "description": "SALT triage category"
                },
                "injuries": {
                    "type": ["array", "null"],
                    "items": {
                        "type": "object",
                        "properties": {
                            "locations": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["Head", "Neck", "Chest", "Back", "Pelvis", "Abdomen", "Limbs (Upper)", "Limbs (Lower)"]
                                }
                            },
                            "mechanisms": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["Blunt", "Penetrating", "Thermal", "Blast", "Drowning", "Chemical", "Radiation", "Electrical", "Hypothermia", "Other"]
                                }
                            },
                            "severity": {
                                "type": "string",
                                "enum": ["Dead", "Expectant", "Immediate", "Delayed", "Minimal"]
                            },
                            "description": {
                                "type": "string"
                            }
                        },
                        "required": ["locations", "mechanisms", "severity", "description"]
                    }
                },
                "required_medical_capabilities": {
                    "type": ["object", "null"],
                    "properties": {
                        "trauma_center": {"type": ["boolean", "null"]},
                        "neurosurgical": {"type": ["boolean", "null"]},
                        "orthopedic": {"type": ["boolean", "null"]},
                        "ophthalmology": {"type": ["boolean", "null"]},
                        "burn": {"type": ["boolean", "null"]},
                        "pediatric": {"type": ["boolean", "null"]},
                        "obstetric": {"type": ["boolean", "null"]},
                        "cardiac": {"type": ["boolean", "null"]},
                        "thoracic": {"type": ["boolean", "null"]},
                        "vascular": {"type": ["boolean", "null"]},
                        "ent": {"type": ["boolean", "null"]},
                        "hepatobiliary": {"type": ["boolean", "null"]}
                    }
                },
                "required_medical_resources": {
                    "type": ["object", "null"],
                    "properties": {
                        "ward": {"type": ["integer", "null"]},
                        "ordinary_icu": {"type": ["integer", "null"]},
                        "operating_room": {"type": ["integer", "null"]},
                        "ventilator": {"type": ["integer", "null"]},
                        "prbc_unit": {"type": ["integer", "null"]},
                        "isolation": {"type": ["integer", "null"]},
                        "decontamination_unit": {"type": ["integer", "null"]},
                        "ct_scanner": {"type": ["integer", "null"]},
                        "oxygen_cylinder": {"type": ["integer", "null"]},
                        "interventional_radiology": {"type": ["integer", "null"]}
                    }
                },
                "description": {
                    "type": "string",
                    "description": "Original or summarized patient description"
                },
                "predicted_death_timestamp": {
                    "type": ["integer", "null"],
                    "description": "Unix timestamp of predicted death (null if low risk)"
                },
                "status": {
                    "type": "string",
                    "enum": ["Unassigned", "Awaiting Transfer", "In-Transfer", "Arrived"],
                    "description": "Patient status"
                },
                "assigned_facility": {
                    "type": ["string", "null"],
                    "description": "ID of assigned healthcare facility"
                },
                "action_logs": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Log of actions taken for this patient"
                },
                "deceased": {
                    "type": ["boolean", "null"],
                    "description": "Whether the patient is deceased"
                },
                "location": {
                    "type": ["object", "null"],
                    "properties": {
                        "latitude": {"type": ["number", "null"]},
                        "longitude": {"type": ["number", "null"]}
                    }
                }
            },
            "required": ["description"]
        }
    }
}
