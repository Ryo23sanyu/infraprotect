from django.db import models


class Article(models.Model):
    name    = models.CharField(max_length=100)

class Infra(models.Model):
    title   = models.CharField(max_length=100)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)


class Table(models.Model):
    infra   = models.ForeignKey(Infra, verbose_name="橋梁名", on_delete=models.CASCADE)
    dxf     = models.FileField(verbose_name="dxfファイル", upload_to="infra/table/dxf/")
    article = models.ForeignKey(Article, on_delete=models.CASCADE, null=True, blank=True)