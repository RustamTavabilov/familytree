from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    """Модель анкеты человека"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='profile')

    # Основные поля
    first_name = models.CharField(max_length=100, verbose_name="Имя")
    last_name = models.CharField(max_length=100, verbose_name="Фамилия")
    patronymic = models.CharField(max_length=100, verbose_name="Отчество", blank=True)
    birth_date = models.DateField(verbose_name="Дата рождения", null=True, blank=True)
    birth_place = models.CharField(max_length=255, verbose_name="Место рождения", blank=True)

    # Необязательные поля
    job = models.CharField(max_length=255, verbose_name="Место работы", blank=True)
    position = models.CharField(max_length=255, verbose_name="Должность", blank=True)
    education = models.TextField(verbose_name="Образование", blank=True)
    hobbies = models.TextField(verbose_name="Хобби", blank=True)

    # Системные поля
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_profiles')
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    # ПОКОЛЕНИЕ (новое поле)
    generation = models.IntegerField(default=0, verbose_name="Поколение")

    def __str__(self):
        parts = [self.last_name, self.first_name, self.patronymic]
        return ' '.join([p for p in parts if p]) or f"Person {self.id}"

    def get_full_name(self):
        return self.__str__()

    class Meta:
        ordering = ['last_name', 'first_name']
        verbose_name = "Анкета"
        verbose_name_plural = "Анкеты"


class Relationship(models.Model):
    """Модель для связи между двумя людьми - ТОЛЬКО 4 ТИПА"""
    RELATIONSHIP_TYPES = [
        ('mother', 'Мать'),
        ('father', 'Отец'),
        ('son', 'Сын'),
        ('daughter', 'Дочь'),
        ('husband', 'Муж'),
        ('wife', 'Жена'),
    ]

    person_from = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='outgoing_relationships',
                                    verbose_name="Человек")
    person_to = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='incoming_relationships',
                                  verbose_name="Родственник")
    relationship_type = models.CharField(max_length=20, choices=RELATIONSHIP_TYPES, verbose_name="Тип родства")

    date_created = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True)

    class Meta:
        unique_together = ['person_from', 'person_to', 'relationship_type']
        verbose_name = "Связь"
        verbose_name_plural = "Связи"

    def __str__(self):
        return f"{self.person_from} -> {self.get_relationship_type_display()} -> {self.person_to}"