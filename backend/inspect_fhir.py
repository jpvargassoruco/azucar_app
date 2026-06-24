from fhir.resources.nutritionintake import NutritionIntakeConsumedItem, NutritionIntake
from fhir.resources.codeablereference import CodeableReference
from fhir.resources.codeableconcept import CodeableConcept

print("NutritionIntakeConsumedItem fields:")
for field_name, field in NutritionIntakeConsumedItem.model_fields.items():
    print(f"  {field_name}: {field.annotation} (required: {field.is_required()})")

print("\nCodeableReference fields:")
for field_name, field in CodeableReference.model_fields.items():
    print(f"  {field_name}: {field.annotation} (required: {field.is_required()})")
