from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, email, client, password=None):
        if not email:
            raise ValueError("Email обязателен")

        user = self.model(
            email=self.normalize_email(email),
            client=client
        )

        user.set_password(password)
        user.save()
        return user