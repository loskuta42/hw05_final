from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from yatube import settings

from .forms import PostForm, CommentForm
from .models import Group, Post, User, Comment


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, settings.PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'index.html',
        {'page': page, 'paginator': paginator}
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    group_list = group.posts.all()
    paginator = Paginator(group_list, settings.PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'group.html',
        {'group': group, 'page': page, 'paginator': paginator}
    )


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('index')
    return render(
        request,
        'posts/new.html',
        {
            'form': form,
            'title': 'Новая запись',
            'button': 'Создать новую запись'
        }
    )


def profile(request, username):
    author = get_object_or_404(User, username=username)
    author_posts = author.posts.all()
    count = author_posts.count()
    paginator = Paginator(author_posts, settings.PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'profile.html',
        {'page': page, 'count': count, 'author': author}
    )


@login_required
def add_comment(request, post_id, username):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect(
            'post',
            post_id=post.id,
            username=post.author.username
        )
    return render(
        request,
        'includes/comments.html',
        {
            'form': form,
            'post': post
        }
    )


def post_view(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    form = CommentForm()
    author_posts = post.author.posts.all()
    count = author_posts.count()
    comments = post.comments.all()
    return render(
        request,
        'post.html',
        {
            'author': post.author,
            'post': post,
            'count': count,
            'comments': comments,
            'form': form
        }
    )


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    if post.author != request.user:
        return redirect(
            'post',
            post_id=post.id,
            username=post.author.username
        )
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect(
            'post',
            post_id=post.id,
            username=post.author.username
        )
    return render(
        request,
        'posts/new.html',
        {
            'form': form,
            'title': 'Редактировать запись',
            'button': 'Сохранить запись',
            'post': post
        }
    )




def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)
