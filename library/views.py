from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth import get_user_model
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import PasswordChangeForm
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from .forms import UserForm, CustomUserCreationForm
from .models import Book, Borrow

User = get_user_model()


def home(request):
    books = Book.objects.all().order_by('id')
    query = request.GET.get('q')

    if query:
        books = books.filter(title__icontains=query)
        if books.exists():
            messages.success(request, f'找到 {books.count()} 本书籍与"{query}"相关！')
        else:
            messages.info(request, f'没有找到与"{query}"相关的书籍。')

    paginator = Paginator(books, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'library/home.html', {
        'page_obj': page_obj,
        'query': query,
    })


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                auth_login(request, user)
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'message': '用户名或密码错误！'})
        else:
            return JsonResponse({'success': False, 'message': '用户名或密码错误！'})
    else:
        form = AuthenticationForm()
    return render(request, 'library/login_form.html', {'form': form})


@login_required
def borrow_book(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    if request.method == 'POST':
        borrow, created = Borrow.objects.get_or_create(
            user=request.user,
            book=book,
            is_returned=0,
            defaults={'due_date': request.POST['due_date']}
        )
        if created:
            messages.success(request, f'成功借阅《{book.title}》！')
        else:
            borrow.due_date = request.POST['due_date']
            borrow.save()
            messages.info(request, f'已更新《{book.title}》的到期时间！')
        return redirect('borrow_records')
    return render(request, 'library/borrow_book.html', {'book': book})


def login_required_message(function):
    def wrap(request, *args, **kwargs):
        if request.user.is_authenticated:
            return function(request, *args, **kwargs)
        else:
            messages.error(request, '请先登录！')
            return redirect('home')

    return wrap


@login_required_message
def borrow_books(request):
    if request.method == 'POST':
        book_ids = request.POST.getlist('borrow_books')
        days = int(request.POST.get('days', 7))
        days = min(max(days, 1), 30)

        for book_id in book_ids:
            book = get_object_or_404(Book, id=book_id)
            borrow, created = Borrow.objects.get_or_create(
                user=request.user,
                book=book,
                is_returned=0,
                defaults={'due_date': timezone.now().date() + timedelta(days=days)}
            )
            if created:
                messages.success(request, f'成功借阅《{book.title}》！')
            else:
                borrow.due_date = timezone.now().date() + timedelta(days=days)
                borrow.save()
                messages.info(request, f'已更新《{book.title}》的到期时间！')

        return redirect('borrow_records')
    return redirect('home')


@login_required
def borrow_records(request):
    user = request.user
    query = request.GET.get('q')
    status_filter = request.GET.get('status')

    borrows = Borrow.objects.filter(user=user).order_by('id')

    if query:
        borrows = borrows.filter(book__title__icontains=query)

    if status_filter:
        borrows = borrows.filter(is_returned=status_filter)

    paginator = Paginator(borrows, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if request.method == 'POST':
        borrow_ids = request.POST.getlist('return_books')
        Borrow.objects.filter(id__in=borrow_ids).update(is_returned=1, return_date=timezone.now())
        for borrow_id in borrow_ids:
            borrow = Borrow.objects.get(id=borrow_id)
            messages.success(request, f'成功归还《{borrow.book.title}》！')
        return redirect('borrow_records')

    return render(request, 'library/borrow_records.html', {
        'page_obj': page_obj,
        'query': query,
        'status_filter': status_filter,
    })


@login_required
def user_detail(request):
    user = request.user
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, '用户信息更新成功！')
            return redirect('user_detail')
        else:
            messages.error(request, '更新用户信息时出错。')
    else:
        form = UserForm(instance=user)
    return render(request, 'library/user_detail.html', {'form': form})


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, '密码更改成功！')
            return redirect('user_detail')
        else:
            messages.error(request, '更改密码时出错。')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'library/change_password.html', {'form': form})


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return JsonResponse({'success': True, 'message': '注册成功！'})
        else:
            return JsonResponse({'success': False, 'message': '注册失败，请检查表单信息。'})
    else:
        form = CustomUserCreationForm()
    return render(request, 'library/register_form.html', {'form': form})
