import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HH.settings')
django.setup()

from candidate_trainer.templatetags.trainer_filters import strip_list_marker
from candidate_trainer.models import InterviewInsight

print("=== Testing strip_list_marker filter ===")
test_cases = [
    '* Test item',
    '- Another test',
    '+ Plus item',
    '*Test without space',
    '  * Indented',
    'No marker',
]

for test in test_cases:
    result = strip_list_marker(test)
    print(f"Input:  {repr(test)}")
    print(f"Output: {repr(str(result))}")
    print()

print("\n=== Checking actual data ===")
insights = InterviewInsight.objects.all()[:1]
if insights:
    insight = insights[0]
    print(f"Gaps type: {type(insight.gaps)}")
    print(f"Gaps: {insight.gaps}")
    if insight.gaps:
        print(f"\nFirst gap:")
        print(f"  Raw: {repr(insight.gaps[0])}")
        print(f"  Filtered: {repr(str(strip_list_marker(insight.gaps[0])))}")
else:
    print("No insights found in database")
