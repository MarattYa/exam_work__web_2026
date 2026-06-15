from django import forms
from .models import Collection


class CollectionForm(forms.ModelForm):
    class Meta:
        model = Collection
        fields = ['title']
        labels = {
            'title': 'Название подборки'
        }