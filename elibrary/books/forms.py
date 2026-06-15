from django import forms

from .models import Book
from reviews.models import Review


class BootstrapModelForm(forms.ModelForm):
    """Добавляет Bootstrap-классы ко всем полям формы."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css_class = 'form-select' if isinstance(field.widget, (forms.Select, forms.SelectMultiple)) else 'form-control'
            field.widget.attrs['class'] = f"{field.widget.attrs.get('class', '')} {css_class}".strip()


class BookForm(BootstrapModelForm):
    class Meta:
        model = Book
        fields = ['title', 'description', 'year', 'publisher', 'author', 'pages', 'genres']
        labels = {
            'title': 'Название',
            'description': 'Краткое описание',
            'year': 'Год',
            'publisher': 'Издательство',
            'author': 'Автор',
            'pages': 'Объём в страницах',
            'genres': 'Жанры',
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 8}),
            'genres': forms.SelectMultiple(attrs={'size': 6}),
        }


class BookCreateForm(BookForm):
    cover = forms.ImageField(label='Обложка')


class ReviewForm(BootstrapModelForm):
    class Meta:
        model = Review
        fields = ['score', 'text']
        labels = {
            'score': 'Оценка',
            'text': 'Текст рецензии',
        }
        widgets = {
            'text': forms.Textarea(attrs={'rows': 7}),
        }
