from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from articlesboard.settings import SITE_NAME
from django.urls import reverse_lazy
from django.core.signing import BadSignature
from django.contrib import messages
from django.contrib.auth import authenticate, login 
from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView
from django.contrib.auth.views import PasswordResetDoneView, PasswordResetConfirmView
from django.contrib.auth.views import PasswordResetCompleteView, PasswordChangeView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.messages.views import SuccessMessageMixin
from django.views import View
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.utils import timezone
from django.forms import ValidationError
from django.core.paginator import Paginator

from tagging.models import TaggedItem, Tag
from tagging_autocomplete.models import TagAutocomplete

from .models import AdvUser, Category, Article
from .forms import ARegisterUserForm, ChangeUserInfoForm, ArticleForm, ArticleFormSet
from .forms import DeleteArticleForm, EditArticleForm
from .utilities import signer


# Popular articles.
rate_articles = Article.objects.order_by('-rating').filter(is_active=True)[:10]


# Main page view.
def index(request):
    last_articles = Article.objects.filter(is_active=True)
    # Refreshing popular articles.
    rate_articles = Article.objects.order_by('-rating').filter(is_active=True)[:10]
    context = {'last_articles': last_articles, 'rate_articles': rate_articles}# 'site_name': SITE_NAME}
    return render(request, 'articles/index.html', context)


# Article page view.
def detail(request, pk):
    article = Article.objects.get(pk=pk)
    # Check if current user already read the article.
    if request.user not in article.viewed_users.all():
        if request.user.is_authenticated:
            article.viewed_users.add(request.user)
        article.views += 1
        article.save()
    # Get TaggedItem objects related to article.
    tags_objs = TaggedItem.objects.filter(object_id=pk)
    tags = []
    for tag in tags_objs:
        tags.append(tag.tag)
    context = {'article': article, 'tags': tags, 'site_name': SITE_NAME, 'rate_articles': rate_articles}
    return render(request, 'articles/article.html', context)


# Profile page view.
def profile(request, username=None):
    # Get AdvUser object by username.
    if username is None:
        username = request.user.username
    user = get_object_or_404(AdvUser, username=username)
    context = {'user': user, 'rate_articles': rate_articles, 'site_name': SITE_NAME}
    return render(request, 'articles/user_actions/profile.html', context)


# When user press rating button.
@login_required
def change_rating(request, rating, pk):
    article = Article.objects.get(pk=pk)
    if request.user not in article.rated_users.all():
        article.change_rating(rating, request.user)
        messages.add_message(request, messages.SUCCESS, 'Спасибо! Ваш голос учтен.')
    else:
        messages.add_message(request, messages.WARNING, 'Вы уже голосовали за эту статью!')
    # Refresh current rate_articles.
    global rate_articles
    rate_articles = Article.objects.order_by('-rating').filter(is_active=True)[:10]
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


# Post-registration activation controller.
def user_activate(request, sign):
    try:
        username = signer.unsign(sign)
    except BadSignature:
        return render(request, 'articles/user_actions/bad_signature.html')
    user = get_object_or_404(AdvUser, username=username)
    if user.is_activated:
        template = 'articles/user_actions/user_already_activated.html'
    else:
        template = 'articles/user_actions/activation_done.html'
        user.is_active = True
        user.is_activated = True
        user.save()
    return render(request, template)


@login_required
def subscribe_user(request, username):
    user = AdvUser.objects.get(username=username)
    if user not in request.user.user_subscriptions.all():
        request.user.subscribe_user(user)
    else:
        messages.add_message(request, messages.WARNING, 'Вы уже подписаны на этого пользователя!')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required
def unsubscribe_user(request, username):
    user = AdvUser.objects.get(username=username)
    if user in request.user.user_subscriptions.all():
        request.user.unsubscribe_user(user)
    else:
        messages.add_message(request, messages.WARNING, 'Вы не подписаны на этого пользователя!')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required
def subscribe_tag(request, tag):
    tag = Tag.objects.get(name=tag)
    if tag not in request.user.tags_subscriptions.all():
        request.user.subscribe_tag(tag)
    else:
        messages.add_message(request, messages.WARNING, 'Вы уже подписаны на этот тег')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required
def unsubscribe_tag(request, tag):
    tag = Tag.objects.get(name=tag)
    if tag in request.user.tags_subscriptions.all():
        request.user.unsubscribe_tag(tag)
    else:
        messages.add_message(request, messages.WARNING, 'Вы не подписаны на этот тег')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def search_by_tag(request, tag):
    articles = Article.objects.filter(tags__contains=tag)
    paginator = Paginator(articles, 9)
    if 'page' in request.GET:
        page_num = request.GET['page']
    else:
        page_num = 1
    page = paginator.get_page(page_num)
    tag = Tag.objects.get(name=tag)
    context = {'rate_articles': rate_articles, 'site_name': SITE_NAME, 'articles': page.object_list, 'page': page, 'tag': tag}
    return render(request, 'articles/search.html', context)


# Add article page view.
class ArticleAddView(TemplateView, LoginRequiredMixin):

    template_name = 'articles/user_actions/add_article.html'

    def get(self, request, *args, **kwargs):
        form = ArticleForm(initial={'author': self.request.user.pk})
        context = {'form': form, 'site_name': SITE_NAME, 'rate_articles': rate_articles}
        return render(self.request, self.template_name, context=context, *args)
    
    def post(self, request):
        form = ArticleForm(self.request.POST, self.request.FILES, initial={'author': self.request.user.pk})
        if form.is_valid():
            form.save()
            messages.add_message(self.request, messages.SUCCESS, 'Статья отправлена на модерацию.')
        else:
            messages.add_message(self.request, messages.WARNING, 'Ошибка')
        return redirect('articles:index')

    class Meta:
        model = Article
        fields = ('__all__', )


class ArticleEditView(UpdateView, SuccessMessageMixin, LoginRequiredMixin):
    
    template_name = 'articles/user_actions/edit_article.html'
    model = Article
    form_class = EditArticleForm
    
    def dispatch(self, request, pk, *args, **kwargs):
        self.article = get_object_or_404(Article, pk=pk)
        self.user_id = self.article.pk
        self.success_url = reverse_lazy('articles:article', kwargs={'pk': self.article.pk})
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        if not queryset:
            queryset = self.get_queryset()
        return get_object_or_404(queryset, pk=self.article.pk)
    
    def get(self, request):
        form = EditArticleForm(instance=self.article)
        context = {'article': self.article, 'form': form, 'site_name': SITE_NAME, 'rate_articles': rate_articles}
        return render(self.request, self.template_name, context=context)
    
    def post(self, request):
        form = EditArticleForm(self.request.POST, self.request.FILES, instance=self.article)
        if form.is_valid():
            self.article.is_active = False
            self.article.save()
            messages.add_message(self.request, messages.SUCCESS, 'Статья успешно отредактирована и отправлена на модерацию.')
        else:
            messages.add_message(self.request, messages.WARNING, 'Ошибка.')
            return redirect('articles:edit_article', pk=self.article.pk)
        return redirect('articles:index')
    
    class Meta:
        model = Article
        fields = ('__all__', )
        

# Confirm deletion of article page.
class ArticleDeleteView(TemplateView, LoginRequiredMixin):
    
    template_name = 'articles/user_actions/delete_article.html'
    
    def get(self, *args, pk):
        article = get_object_or_404(Article, pk=pk)
        form = DeleteArticleForm()
        context = {'form': form, 'article': article, 'site_name': SITE_NAME, 'rate_articles': rate_articles}
        return render(self.request, self.template_name, context)
    
    def post(self, *args, pk):
        form = DeleteArticleForm(self.request.POST)
        article = get_object_or_404(Article, pk=pk)
        if form.is_valid():
            # Restricting deletion from other users.
            if self.request.user.username.__ne__(article.author.username) and self.request.user.username.__ne__('admin'):
                messages.add_message(self.request, messages.ERROR, f'У пользователя {self.request.user.username} недостаточно прав для удаления данной статьи.')
                return redirect('articles:index')
            
            article.is_active = False
            article.save()
            messages.add_message(self.request, messages.SUCCESS, 'Статья успешно удалена')
        else:
            messages.add_message(self.request, messages.WARNING, 'Возникла ошибка во время удаления статьи!')
        return redirect('articles:index')
            

# Login page view.
class ALoginView(LoginView):

    extra_context = {'site_name': SITE_NAME, 'rate_articles': rate_articles}
    template_name = 'articles/user_actions/login.html'
    
    redirect_field_name = reverse_lazy('articles:index')
    redirect_authenticated_user = True
    
    def get(self, *args):
        return render(self.request, self.template_name, self.extra_context)

    def post(self, *args):
        user = authenticate(self.request, username=self.request.POST['username'], password=self.request.POST['password'])
        if user is not None:
            login(self.request, user)
            return redirect(self.redirect_field_name)
        else:
            messages.add_message(self.request, messages.ERROR, 'Неправильный логин или пароль')
    

# Logout page view.
class ALogoutView(LoginRequiredMixin, LogoutView):
    extra_context = {'site_name': SITE_NAME}
    template_name = 'articles/user_actions/logout.html'
    
    def get(self, *args):
        messages.add_message(self.request, messages.SUCCESS, 'Вы успешно вышли с сайта!')
        return redirect(reverse_lazy('articles:index'))
    
    
# Register page view.
class ARegisterUserView(CreateView):
    model = AdvUser
    template_name = 'articles/user_actions/register_user.html'
    form_class = ARegisterUserForm
    success_url = reverse_lazy('articles:register_done')
    
    def get(self, request):
        return render(request, self.template_name, {'site_name': SITE_NAME})
    
    
# When user activated.
class ARegisterDoneView(TemplateView):
    template_name = 'articles/user_actions/register_done.html'
    
    def get(self, request):
        return render(request, self.template_name, {'site_name': SITE_NAME})
 

# Change info view.
class ChangeUserInfoView(SuccessMessageMixin, LoginRequiredMixin, UpdateView):
    
    model = AdvUser
    template_name = 'articles/user_actions/change_user_info.html'
    form_class = ChangeUserInfoForm
    
    def dispatch(self, request, username, *args, **kwargs):
        self.user = get_object_or_404(AdvUser, username=username)
        self.user_id = self.user.pk
        self.success_url = reverse_lazy('articles:profile', kwargs={'username': self.user.username})
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        if not queryset:
            queryset = self.get_queryset()
        return get_object_or_404(queryset, username=self.user.username)
    
    def get(self, request):
        form = ChangeUserInfoForm(instance=self.user)
        context = {'form': form}
        return render(request, self.template_name, context)
    
    def post(self, request):
        form = ChangeUserInfoForm(request.POST, request.FILES, instance=self.user)
        if form.is_valid():
            form.save()
            messages.add_message(request, messages.SUCCESS, 'Профиль успешно отредактирован.')
        else:
            messages.add_message(request, messages.WARNING, 'Произошла ошибка при изменении данных профиля.')
        return redirect('articles:profile', username=self.user.username)


# Change password.
class APasswordChangeView(LoginRequiredMixin, SuccessMessageMixin, PasswordChangeView):
    template_name = 'articles/user_actions/change_password.html'
    success_url = reverse_lazy('articles:profile')
    success_message = 'Пароль успешно изменен.'


# Forget password.
class APasswordResetView(PasswordResetView):
    template_name = 'articles/user_actions/reset_password.html'
    subject_template_name = 'email/reset_password_letter_subject.txt'
    email_template_name = 'email/reset_password_letter_body.txt'
    success_url = reverse_lazy('articles:reset_password_done')

    # # def dispatch(self, request, *args, **kwargs):
    # #     self.user = get_object_or_404(AdvUser, email=request.POST['email'])
    # #     return super().dispatch(request, *args, **kwargs)

    # # def get_object(self, queryset=None):
    # #     if not queryset:
    # #         queryset = self.get_queryset()
    # #     return get_object_or_404(queryset, email=self.user.email)

    # def get(self, request):
    #     return render(request, self.template_name)

    # def post(self, request):
    #     try:
    #         user = AdvUser.objects.get(email=request.POST['email'])
    #         if user:
    #             return reverse_lazy('articles:reset_password_done')
    #     except:
    #         messages.add_message(request, messages.ERROR, 'Указанный Email не существует.')
    #         return render(request, self.template_name)


class APasswordResetDoneView(SuccessMessageMixin, PasswordResetDoneView):
    template_name = 'articles/user_actions/reset_password_done.html'
    success_message = 'Письмо успешно отправлено!'          


class APasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'articles/user_actions/reset_password_confirm.html'
    success_url = reverse_lazy('articles:reset_password_complete')


class APasswordResetCompleteView(SuccessMessageMixin, PasswordResetCompleteView):
    template_name = 'articles/user_actions/reset_password_complete.html'
    success_message = 'Пароль успешно изменен.'
