import hashlib
import random
from io import BytesIO

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from PIL import Image, ImageDraw

from books.models import Book, Genre, Cover
from reviews.models import Review
from users.models import Role, Profile
from collection.models import Collection


class Command(BaseCommand):
    help = 'Создаёт тестовые роли, пользователей, жанры, книги, рецензии и подборки'

    def add_arguments(self, parser):
        parser.add_argument(
            '--books',
            type=int,
            default=30,
            help='Количество книг'
        )
        parser.add_argument(
            '--users',
            type=int,
            default=8,
            help='Количество обычных пользователей'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Очистить тестовые данные перед генерацией'
        )

    def handle(self, *args, **options):
        books_count = options['books']
        users_count = options['users']
        clear = options['clear']

        with transaction.atomic():
            if clear:
                self.clear_data()

            roles = self.create_roles()
            users = self.create_users(roles, users_count)
            genres = self.create_genres()
            books = self.create_books(books_count, genres)
            self.create_reviews(books, users)
            self.create_collections(books, users)

        self.stdout.write(self.style.SUCCESS('Тестовые данные успешно созданы'))

        self.stdout.write('')
        self.stdout.write('Пользователи для входа:')
        self.stdout.write('admin / admin12345')
        self.stdout.write('moderator / moderator12345')
        self.stdout.write('user1 / user12345')
        self.stdout.write('user2 / user12345')

    def clear_data(self):
        Collection.objects.all().delete()
        Review.objects.all().delete()
        Cover.objects.all().delete()
        Book.objects.all().delete()
        Genre.objects.all().delete()

        User.objects.filter(is_superuser=False).delete()
        User.objects.filter(username='admin').delete()

        Role.objects.all().delete()

    def create_roles(self):
        role_data = [
            {
                'name': 'Администратор',
                'description': 'Суперпользователь, имеет полный доступ к системе'
            },
            {
                'name': 'Модератор',
                'description': 'Может редактировать книги и модерировать рецензии'
            },
            {
                'name': 'Пользователь',
                'description': 'Может оставлять рецензии и создавать подборки'
            },
        ]

        roles = {}

        for item in role_data:
            role, _ = Role.objects.get_or_create(
                name=item['name'],
                defaults={'description': item['description']}
            )
            roles[item['name']] = role

        return roles

    def create_users(self, roles, users_count):
        users = []

        admin, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'first_name': 'Иван',
                'last_name': 'Админов',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        admin.first_name = 'Иван'
        admin.last_name = 'Админов'
        admin.set_password('admin12345')
        admin.is_staff = True
        admin.is_superuser = True
        admin.save()

        Profile.objects.get_or_create(
            user=admin,
            defaults={
                'middle_name': 'Иванович',
                'role': roles['Администратор']
            }
        )

        moderator, _ = User.objects.get_or_create(
            username='moderator',
            defaults={
                'first_name': 'Мария',
                'last_name': 'Модераторова',
                'is_staff': True,
            }
        )
        moderator.first_name = 'Мария'
        moderator.last_name = 'Модераторова'
        moderator.set_password('moderator12345')
        moderator.is_staff = True
        moderator.save()

        Profile.objects.get_or_create(
            user=moderator,
            defaults={
                'middle_name': 'Петровна',
                'role': roles['Модератор']
            }
        )

        first_names = [
            'Алексей', 'Дмитрий', 'София', 'Анна',
            'Павел', 'Екатерина', 'Никита', 'Ольга',
            'Кирилл', 'Дарья', 'Максим', 'Полина'
        ]

        last_names = [
            'Иванов', 'Петров', 'Сидоров', 'Смирнов',
            'Кузнецов', 'Попов', 'Васильев', 'Морозов',
            'Новиков', 'Фёдоров'
        ]

        middle_names = [
            'Александрович', 'Иванович', 'Петрович',
            'Сергеевич', 'Андреевич', 'Дмитриевич'
        ]

        for i in range(1, users_count + 1):
            user, _ = User.objects.get_or_create(
                username=f'user{i}',
                defaults={
                    'first_name': random.choice(first_names),
                    'last_name': random.choice(last_names),
                }
            )
            user.set_password('user12345')
            user.save()

            Profile.objects.get_or_create(
                user=user,
                defaults={
                    'middle_name': random.choice(middle_names),
                    'role': roles['Пользователь']
                }
            )

            users.append(user)

        return users

    def create_genres(self):
        genre_names = [
            'Фантастика',
            'Фэнтези',
            'Детектив',
            'Роман',
            'Приключения',
            'История',
            'Научная литература',
            'Ужасы',
            'Классика',
            'Психология',
            'Манга',
            'Комедия',
        ]

        genres = []

        for name in genre_names:
            genre, _ = Genre.objects.get_or_create(name=name)
            genres.append(genre)

        return genres

    def create_books(self, books_count, genres):
        title_parts_1 = [
            'Тайна', 'Хроники', 'Путь', 'Легенда',
            'Город', 'Последний', 'Зов', 'Код',
            'Мир', 'Дом', 'Тень', 'Остров'
        ]

        title_parts_2 = [
            'звёзд', 'дракона', 'времени', 'лабиринта',
            'снов', 'пепла', 'моря', 'памяти',
            'луны', 'ветра', 'книг', 'тьмы'
        ]

        authors = [
            'А. Пушкин', 'М. Булгаков', 'Ф. Достоевский',
            'Л. Толстой', 'А. Азимов', 'Р. Брэдбери',
            'Дж. Толкин', 'А. Кристи', 'С. Кинг',
            'Н. Гейман'
        ]

        publishers = [
            'Эксмо',
            'АСТ',
            'Азбука',
            'Питер',
            'Росмэн',
            'МИФ',
            'Редакция Елены Шубиной',
        ]

        books = []

        for i in range(1, books_count + 1):
            title = f'{random.choice(title_parts_1)} {random.choice(title_parts_2)} #{i}'

            book = Book.objects.create(
                title=title,
                description=(
                    f'## {title}\n\n'
                    f'Это тестовое описание книги. '
                    f'В нём можно использовать **Markdown**. '
                    f'Книга создана автоматически для проверки интерфейса.'
                ),
                year=random.randint(1980, 2026),
                publisher=random.choice(publishers),
                author=random.choice(authors),
                pages=random.randint(90, 950),
            )

            book.genres.set(random.sample(genres, random.randint(1, 3)))

            self.create_cover(book, i)

            books.append(book)

        return books

    def create_cover(self, book, index):
        image = Image.new(
            'RGB',
            (420, 620),
            color=(
                random.randint(30, 120),
                random.randint(30, 120),
                random.randint(30, 120),
            )
        )

        draw = ImageDraw.Draw(image)

        draw.rectangle(
            [20, 20, 400, 600],
            outline=(240, 240, 240),
            width=4
        )

        draw.text(
            (45, 250),
            book.title[:26],
            fill=(255, 255, 255)
        )

        draw.text(
            (45, 290),
            str(book.year),
            fill=(245, 166, 35)
        )

        buffer = BytesIO()
        image.save(buffer, format='JPEG')
        image_bytes = buffer.getvalue()

        md5_hash = hashlib.md5(image_bytes).hexdigest()

        file_name = f'cover_{book.id}_{index}.jpg'

        cover = Cover.objects.create(
            book=book,
            file_name=file_name,
            mime_type='image/jpeg',
            md5_hash=md5_hash,
        )

        cover.image.save(
            file_name,
            ContentFile(image_bytes),
            save=True
        )

    def create_reviews(self, books, users):
        review_texts = [
            'Очень понравилась книга, читается легко и интересно.',
            'Неплохая история, но местами немного затянуто.',
            'Отличная атмосфера и запоминающиеся персонажи.',
            'Книга на любителя, но в целом достойная.',
            'Интересный сюжет и хороший стиль автора.',
            'После прочтения осталось приятное впечатление.',
        ]

        for book in books:
            reviewers = random.sample(users, random.randint(0, min(5, len(users))))

            for user in reviewers:
                Review.objects.get_or_create(
                    book=book,
                    user=user,
                    defaults={
                        'score': random.randint(0, 5),
                        'text': random.choice(review_texts),
                    }
                )

    def create_collections(self, books, users):
        collection_names = [
            'Хочу прочитать',
            'Любимые книги',
            'На выходные',
            'Лучшее за год',
            'Для вдохновения',
        ]

        for user in users:
            for name in random.sample(collection_names, random.randint(1, 3)):
                collection, _ = Collection.objects.get_or_create(
                    user=user,
                    title=name
                )

                selected_books = random.sample(books, random.randint(2, min(8, len(books))))
                collection.books.set(selected_books)