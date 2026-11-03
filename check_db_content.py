import os
import sys
import django

sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HH.settings')
django.setup()

from candidate_trainer.models import SkillExplanation

# Берём первое объяснение
exp = SkillExplanation.objects.first()
if exp:
    print(f"Skill: {exp.skill.canonical_name}")
    print(f"User: {exp.user}")
    print(f"\n=== Content (first 1000 chars) ===")
    print(exp.content[:1000])
    print("\n=== Content type ===")
    print(type(exp.content))
else:
    print("No explanations found")
