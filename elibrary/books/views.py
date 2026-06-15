import hashlib
import os
from functools import wraps

import bleach
import markdown

from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.safestring import mark_safe

from collection.models import Collection
from reviews.models import Review
from .forms import BookCreateForm, BookForm, ReviewForm
from .models import Book, Cover


ALLOWED_MARKDOWN_TAGS = list(bleach.sanitizer.ALLOWED_TAGS) + [
    'p', 'br', 'pre', 'code', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li', 'blockquote', 'strong', 'em', 'img', 'table',
    'thead', 'tbody', 'tr', 'th', 'td'
]
ALLOWED_MARKDOWN_ATTRIBUTES = {
    **bleach.sanitizer.ALLOWED_ATTRIBUTES,
    'a': ['href', 'title'],
    'img': ['src', 'alt', 'title'],
}


def clean_markdown_text(value):
    return bleach.clean(
        value or '',
        tags=ALLOWED_MARKDOWN_TAGS,
        attributes=ALLOWED_MARKDOWN_ATTRIBUTES,
        strip=True,
    )


def markdown_to_safe_html(value):
    html = markdown.markdown(value or '', extensions=['extra', 'nl2br'])
    clean_html = bleach.clean(
        html,
        tags=ALLOWED_MARKDOWN_TAGS,
        attributes=ALLOWED_MARKDOWN_ATTRIBUTES,
        strip=True,
    )
    return mark_safe(clean_html)


def get_role(user):
    if not user.is_authenticated:
        return None
    if user.is_superuser:
        return 'Администратор'
    profile = getattr(user, 'profile', None)
    return profile.role.name if profile and profile.role else None


def has_role(user, roles):
    return get_role(user) in roles


def deny_no_login(request):
    messages.warning(
        request,
        'Для выполнения данного действия необходимо пройти процедуру аутентификации'
    )
    return redirect('login')


def deny_no_rights(request):
    messages.warning(
        request,
        'У вас недостаточно прав для выполнения данного действия'
    )
    return redirect('home')


def auth_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return deny_no_login(request)
        return view_func(request, *args, **kwargs)
    return wrapper


def book_list(request):
    books = (
        Book.objects
        .prefetch_related('genres')
        .select_related('cover')
        .annotate(
            avg_score=Avg('review__score'),
            reviews_count=Count('review', distinct=True),
        )
        .order_by('-year', '-id')
    )

    paginator = Paginator(books, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'books/index.html', {
        'page_obj': page_obj,
        'role': get_role(request.user),
        'querystring': '',
    })

def save_cover(book, uploaded_file):
    file_bytes = uploaded_file.read()
    md5_hash = hashlib.md5(file_bytes).hexdigest()
    uploaded_file.seek(0)

    existing_cover = Cover.objects.filter(md5_hash=md5_hash).first()
    if existing_cover and existing_cover.image:
        return Cover.objects.create(
            book=book,
            image=existing_cover.image.name,
            file_name=existing_cover.file_name,
            mime_type=existing_cover.mime_type,
            md5_hash=md5_hash,
        )

    return Cover.objects.create(
        book=book,
        image=uploaded_file,
        file_name=uploaded_file.name,
        mime_type=getattr(uploaded_file, 'content_type', 'application/octet-stream'),
        md5_hash=md5_hash,
    )


@auth_required
def book_create(request):
    if not has_role(request.user, ['Администратор']):
        return deny_no_rights(request)

    if request.method == 'POST':
        form = BookCreateForm(request.POST, request.FILES)

        if form.is_valid():
            try:
                with transaction.atomic():
                    book = form.save(commit=False)
                    book.description = clean_markdown_text(book.description)
                    book.save()
                    form.save_m2m()
                    save_cover(book, request.FILES['cover'])

                messages.success(request, 'Книга успешно добавлена')
                return redirect('book_detail', pk=book.pk)

            except Exception:
                messages.error(
                    request,
                    'При сохранении данных возникла ошибка. Проверьте корректность введённых данных.'
                )
        else:
            messages.error(
                request,
                'При сохранении данных возникла ошибка. Проверьте корректность введённых данных.'
            )
    else:
        form = BookCreateForm()

    return render(request, 'books/book_form.html', {
        'form': form,
        'is_create': True,
    })


def book_detail(request, pk):
    book = get_object_or_404(
        Book.objects.prefetch_related('genres').select_related('cover'),
        pk=pk
    )

    reviews = list(
        Review.objects
        .filter(book=book)
        .select_related('user', 'user__profile')
        .order_by('-created_at')
    )
    for review in reviews:
        review.html_text = markdown_to_safe_html(review.text)

    user_review = None
    user_collections = None
    can_review = False

    if request.user.is_authenticated:
        user_review = Review.objects.filter(book=book, user=request.user).first()
        can_review = has_role(request.user, ['Пользователь', 'Модератор', 'Администратор'])

        if has_role(request.user, ['Пользователь']):
            user_collections = Collection.objects.filter(user=request.user).order_by('title')

    html_description = markdown_to_safe_html(book.description)

    return render(request, 'books/book_detail.html', {
        'book': book,
        'reviews': reviews,
        'user_review': user_review,
        'user_collections': user_collections,
        'html_description': html_description,
        'role': get_role(request.user),
        'can_review': can_review,
    })


@auth_required
def book_update(request, pk):
    if not has_role(request.user, ['Администратор', 'Модератор']):
        return deny_no_rights(request)

    book = get_object_or_404(Book, pk=pk)

    if request.method == 'POST':
        form = BookForm(request.POST, instance=book)

        if form.is_valid():
            try:
                with transaction.atomic():
                    book = form.save(commit=False)
                    book.description = clean_markdown_text(book.description)
                    book.save()
                    form.save_m2m()

                messages.success(request, 'Книга успешно обновлена')
                return redirect('book_detail', pk=book.pk)

            except Exception:
                messages.error(
                    request,
                    'При сохранении данных возникла ошибка. Проверьте корректность введённых данных.'
                )
        else:
            messages.error(
                request,
                'При сохранении данных возникла ошибка. Проверьте корректность введённых данных.'
            )
    else:
        form = BookForm(instance=book)

    return render(request, 'books/book_form.html', {
        'form': form,
        'is_create': False,
        'book': book,
    })


@auth_required
def book_delete(request, pk):
    if not has_role(request.user, ['Администратор']):
        return deny_no_rights(request)

    book = get_object_or_404(Book, pk=pk)

    if request.method == 'POST':
        title = book.title
        image_path = None
        image_name = None

        if hasattr(book, 'cover') and book.cover.image:
            image_path = book.cover.image.path
            image_name = book.cover.image.name

        book.delete()

        if image_path and image_name and not Cover.objects.filter(image=image_name).exists() and os.path.exists(image_path):
            os.remove(image_path)

        messages.success(request, f'Книга «{title}» успешно удалена')

    return redirect('home')


@auth_required
def review_create(request, pk):
    if not has_role(request.user, ['Пользователь', 'Модератор', 'Администратор']):
        return deny_no_rights(request)

    book = get_object_or_404(Book, pk=pk)

    if Review.objects.filter(book=book, user=request.user).exists():
        messages.warning(request, 'Вы уже писали рецензию на эту книгу')
        return redirect('book_detail', pk=book.pk)

    if request.method == 'POST':
        form = ReviewForm(request.POST)

        if form.is_valid():
            review = form.save(commit=False)
            review.book = book
            review.user = request.user
            review.text = clean_markdown_text(review.text)
            review.save()

            messages.success(request, 'Рецензия успешно добавлена')
            return redirect('book_detail', pk=book.pk)

        messages.error(request, 'При сохранении рецензии возникла ошибка')
    else:
        form = ReviewForm(initial={'score': 5})

    return render(request, 'books/review_form.html', {
        'form': form,
        'book': book,
    })


@auth_required
def review_update(request, pk):
    if not has_role(request.user, ['Пользователь', 'Модератор', 'Администратор']):
        return deny_no_rights(request)

    book = get_object_or_404(Book, pk=pk)
    review = get_object_or_404(Review, book=book, user=request.user)

    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)

        if form.is_valid():
            review = form.save(commit=False)
            review.text = clean_markdown_text(review.text)
            review.save()
            messages.success(request, 'Рецензия успешно обновлена')
            return redirect('book_detail', pk=book.pk)

        messages.error(request, 'При сохранении рецензии возникла ошибка')
    else:
        form = ReviewForm(instance=review)

    return render(request, 'books/review_form.html', {
        'form': form,
        'book': book,
        'is_update': True,
    })


@auth_required
def add_to_collection(request, pk):
    if not has_role(request.user, ['Пользователь']):
        return deny_no_rights(request)

    book = get_object_or_404(Book, pk=pk)

    if request.method == 'POST':
        collection_id = request.POST.get('collection_id')
        collection = get_object_or_404(Collection, pk=collection_id, user=request.user)

        if collection.books.filter(pk=book.pk).exists():
            messages.info(request, 'Эта книга уже есть в выбранной подборке')
        else:
            collection.books.add(book)
            messages.success(request, 'Книга успешно добавлена в подборку')

    return redirect('book_detail', pk=book.pk)
