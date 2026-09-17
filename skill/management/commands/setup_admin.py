from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Create or update superuser account automatically'

    def handle(self, *args, **options):
        User = get_user_model()
        username = 'charan'
        email = 'charanedamalapati2005@gmail.com'
        password = '2005'
        
        user, created = User.objects.get_or_create(username=username)
        user.email = email
        user.set_password(password)
        user.is_superuser = True
        user.is_staff = True
        user.is_active = True
        if hasattr(user, 'user_type'):
            user.user_type = 'user'
        user.save()
        
        if created:
            self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' successfully created!"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' updated successfully!"))
