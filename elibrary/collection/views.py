from django.contrib import messages
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CollectionForm
from .models import Collection


def deny_no_login(request):
    messages.warning(
        request,
        'Для выполнения данного действия необходимо пройти процедуру аутентификации'
    )
    return redirect('login')


def deny_no_rights(request):
    messages.warning(request, 'У вас недостаточно прав для выполнения данного действия')
    return redirect('home')


def is_regular_user(user):
    return (
        user.is_authenticated
        and hasattr(user, 'profile')
        and user.profile.role.name == 'Пользователь'
    )


def my_collections(request):
    if not request.user.is_authenticated:
        return deny_no_login(request)
    if not is_regular_user(request.user):
        return deny_no_rights(request)

    collections = (
        Collection.objects
        .filter(user=request.user)
        .annotate(books_count=Count('books'))
        .order_by('title')
    )

    return render(request, 'collection/my_collection.html', {
        'collections': collections,
    })


def collection_create(request):
    if not request.user.is_authenticated:
        return deny_no_login(request)
    if not is_regular_user(request.user):
        return deny_no_rights(request)

    if request.method == 'POST':
        form = CollectionForm(request.POST)

        if form.is_valid():
            collection = form.save(commit=False)
            collection.user = request.user
            collection.save()

            messages.success(request, 'Подборка успешно добавлена')
        else:
            messages.error(request, 'Не удалось добавить подборку')

    return redirect('my_collections')


def collection_detail(request, pk):
    if not request.user.is_authenticated:
        return deny_no_login(request)
    if not is_regular_user(request.user):
        return deny_no_rights(request)

    collection = get_object_or_404(
        Collection.objects.prefetch_related('books__genres', 'books__cover'),
        pk=pk,
        user=request.user
    )

    return render(request, 'collection/collection_detail.html', {
        'collection': collection,
    })
