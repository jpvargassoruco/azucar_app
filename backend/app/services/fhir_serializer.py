from datetime import datetime, timezone
import uuid
from typing import List

from fhir.resources.patient import Patient
from fhir.resources.observation import Observation, ObservationComponent
from fhir.resources.nutritionintake import NutritionIntake, NutritionIntakeConsumedItem
from fhir.resources.condition import Condition
from fhir.resources.bundle import Bundle, BundleEntry
from fhir.resources.extension import Extension

from app.models.user import User
from app.models.glucose import GlucoseReading
from app.models.meal import MealEntry
from app.models.fasting import FastingSession

def generate_urn_uuid() -> str:
    return f"urn:uuid:{uuid.uuid4()}"

def user_to_patient(user: User) -> Patient:
    patient = Patient(
        id=str(user.id),
        identifier=[{"system": "urn:ietf:rfc:3986", "value": f"mailto:{user.email}"}],
        name=[{"use": "usual", "text": user.name}]
    )
    return patient

def glucose_to_observation(reading: GlucoseReading, patient_ref: str) -> Observation:
    obs = Observation(
        status="final",
        category=[{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "laboratory"}]}],
        code={"coding": [{"system": "http://loinc.org", "code": "15074-8", "display": "Glucose [Moles/volume] in Blood"}]},
        subject={"reference": patient_ref},
        effectiveDateTime=reading.datetime.isoformat(),
        valueQuantity={
            "value": reading.value_mgdl,
            "unit": "mg/dL",
            "system": "http://unitsofmeasure.org",
            "code": "mg/dL"
        }
    )
    
    # Add component for condition (fasting vs postprandial)
    condition_code = "1558-6" if reading.condition == "ayunas" else "1521-4"
    condition_display = "Fasting glucose" if reading.condition == "ayunas" else "Postprandial glucose"
    
    obs.component = [
        ObservationComponent(
            code={"coding": [{"system": "http://loinc.org", "code": condition_code, "display": condition_display}]}
        )
    ]
    
    return obs

def meal_to_nutrition_intake(meal: MealEntry, patient_ref: str) -> NutritionIntake:
    analysis = meal.ai_analysis or {}
    items = analysis.get("food_items", [])
    calories = analysis.get("calories_estimated", 0)
    
    ni = NutritionIntake(
        status="completed",
        code={"coding": [{"system": "http://snomed.info/sct", "code": "226379006", "display": "Food intake"}]},
        subject={"reference": patient_ref},
        occurrenceDateTime=meal.datetime.isoformat()
    )
    
    if items or calories > 0:
        desc = ", ".join(items) if items else (meal.notes or "Meal")
        ni.consumedItem = [
            NutritionIntakeConsumedItem(
                type={"text": desc},
                amount={"value": calories, "unit": "kcal", "system": "http://unitsofmeasure.org", "code": "kcal"}
            )
        ]
        
    impact = analysis.get("glycemic_impact")
    if impact:
        # Custom extension for glycemic impact
        ni.extension = [
            Extension(
                url="http://azucar.aeisoftware.com/fhir/StructureDefinition/glycemic-impact",
                valueString=impact
            )
        ]
        
    return ni

def fasting_to_observation(session: FastingSession, patient_ref: str) -> Observation:
    obs = Observation(
        status="final" if session.completed else "preliminary",
        code={"coding": [{"system": "http://snomed.info/sct", "code": "61144006", "display": "Fasting"}]},
        subject={"reference": patient_ref},
        effectivePeriod={
            "start": session.start_time.isoformat()
        },
        note=[{"text": f"Protocol: {session.protocol}"}]
    )
    if session.end_time:
        obs.effectivePeriod.end = session.end_time.isoformat()
        
    return obs

def build_patient_bundle(user: User, readings: List[GlucoseReading], meals: List[MealEntry], fastings: List[FastingSession]) -> Bundle:
    bundle = Bundle(type="collection", entry=[])
    
    # 1. Patient
    patient = user_to_patient(user)
    patient_uuid = generate_urn_uuid()
    bundle.entry.append(BundleEntry(fullUrl=patient_uuid, resource=patient))
    
    # 2. Condition (Diabetes Type 2)
    condition = Condition(
        clinicalStatus={"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active"}]},
        code={"coding": [{"system": "http://snomed.info/sct", "code": "44054006", "display": "Diabetes mellitus type 2"}]},
        subject={"reference": patient_uuid}
    )
    bundle.entry.append(BundleEntry(fullUrl=generate_urn_uuid(), resource=condition))
    
    # 3. Glucose Readings
    for r in readings:
        obs = glucose_to_observation(r, patient_uuid)
        bundle.entry.append(BundleEntry(fullUrl=generate_urn_uuid(), resource=obs))
        
    # 4. Meals
    for m in meals:
        ni = meal_to_nutrition_intake(m, patient_uuid)
        bundle.entry.append(BundleEntry(fullUrl=generate_urn_uuid(), resource=ni))
        
    # 5. Fastings
    for f in fastings:
        obs = fasting_to_observation(f, patient_uuid)
        bundle.entry.append(BundleEntry(fullUrl=generate_urn_uuid(), resource=obs))
        
    return bundle
