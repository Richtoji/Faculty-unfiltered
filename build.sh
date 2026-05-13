#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

# AUTO-LOAD DATA (Migration from local)
if [ -f feedback_data.json ]; then
    echo "Loading local data snapshot..."
    python manage.py loaddata feedback_data.json
fi

# AUTO-CREATE / RESET ADMIN SUPERUSER ON EVERY DEPLOY
echo "Ensuring admin superuser exists..."
python manage.py shell -c "
from django.contrib.auth.models import User
user, created = User.objects.get_or_create(username='admin')
user.set_password('admin123')
user.is_staff = True
user.is_superuser = True
user.is_active = True
user.save()
print('Admin user ready:', user.username)
"
