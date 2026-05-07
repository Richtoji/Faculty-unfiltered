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

# AUTO-CREATE SUPERUSER (Since Shell is disabled on Free Plan)
if [ "$ADMIN_USERNAME" ]; then
    echo "Creating superuser..."
    python manage.py shell -c "from django.contrib.auth.models import User; User.objects.filter(username='$ADMIN_USERNAME').exists() or User.objects.create_superuser('$ADMIN_USERNAME', 'admin@example.com', '$ADMIN_PASSWORD')"
fi
