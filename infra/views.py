from django.shortcuts import render

# == This code was created by https://noauto-nolife.com/post/django-auto-create-views/ == #

from django.shortcuts import render,redirect
from django.views import View

from .models import Article,Infra,Table
from .forms import ArticleForm,InfraForm,TableForm

class IndexView(View):

    def get(self, request, *args, **kwargs):

        context = {}
        context["form"] = TableForm()

        return render(request, "infra/index.html", context)

    def post(self, request, *args, **kwargs):

        form = TableForm(request.POST, request.FILES)

        if form.is_valid():
            print("保存")
            form.save()
        else:
            print(form.errors)

        return redirect("infra:index")

index   = IndexView.as_view()