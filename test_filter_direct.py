"""Прямой тест фильтра strip_list_marker."""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HH.settings')
sys.path.insert(0, '/app')
django.setup()

from candidate_trainer.templatetags.trainer_filters import strip_list_marker

print("=== Тест фильтра strip_list_marker ===\n")

test_cases = [
    ('* Test item', 'Test item'),
    ('- Another test', 'Another test'),
    ('+ Plus item', 'Plus item'),
    ('*Test without space', 'Test without space'),
    ('  * Indented', 'Indented'),
    ('No marker', 'No marker'),
    ('  -  Multiple spaces', 'Multiple spaces'),
]

failed = 0
for input_text, expected in test_cases:
    result = str(strip_list_marker(input_text))
    status = "✓" if result == expected else "✗"
    print(f"{status} Input:    {repr(input_text)}")
    print(f"  Expected: {repr(expected)}")
    print(f"  Got:      {repr(result)}")
    if result != expected:
        failed += 1
    print()

if failed > 0:
    print(f"❌ Failed: {failed}/{len(test_cases)}")
    sys.exit(1)
else:
    print(f"✅ All {len(test_cases)} tests passed")
    sys.exit(0)
