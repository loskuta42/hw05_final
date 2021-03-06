from django.views.generic.base import TemplateView


class AboutAuthorView(TemplateView):
    template_name = 'author.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['author'] = 'Автор проекта - Алексей Лобарев.'
        context['github'] = (
            '<a href="https://github.com/loskuta42/">'
            'Ссылка на github</a>'
        )
        return context


class AboutTechView(TemplateView):
    template_name = 'tech.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pycharm'] = 'Сайт написан при использовании python и Django.'
        context['tech'] = 'А так же модели, формы, декораторы и многое другое'
        return context
