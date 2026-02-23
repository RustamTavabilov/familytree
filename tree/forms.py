from django import forms
from .models import Profile, Relationship


class ProfileForm(forms.ModelForm):
    """Форма для создания и редактирования анкеты человека"""
    birth_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Дата рождения"
    )

    class Meta:
        model = Profile
        fields = [
            'last_name', 'first_name', 'patronymic',
            'birth_date', 'birth_place',
            'job', 'position', 'education', 'hobbies'
        ]
        widgets = {
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Иванов'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Иван'}),
            'patronymic': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Иванович'}),
            'birth_place': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Москва'}),
            'job': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Место работы'}),
            'position': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Должность'}),
            'education': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Высшее, МГУ'}),
            'hobbies': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Рыбалка, чтение'}),
        }


class RelationshipForm(forms.ModelForm):
    """Форма для создания связи между двумя людьми"""

    class Meta:
        model = Relationship
        fields = ['person_from', 'person_to', 'relationship_type']
        widgets = {
            'person_from': forms.Select(attrs={'class': 'form-control'}),
            'person_to': forms.Select(attrs={'class': 'form-control'}),
            'relationship_type': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'person_from': 'Человек',
            'person_to': 'Родственник',
            'relationship_type': 'Тип родства',
        }