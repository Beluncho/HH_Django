# Generated manually for foto to photo rename

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('userapp', '0003_profile'),
    ]

    operations = [
        migrations.RenameField(
            model_name='websiteuser',
            old_name='foto',
            new_name='photo',
        ),
    ]
