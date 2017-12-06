from django.db import models
from django.template.defaultfilters import slugify
from django.utils import timezone


class Contest(models.Model):
    name = models.CharField(max_length=255)
    slug_name = models.SlugField(unique=True)
    start = models.DateTimeField(default=timezone.now())
    end = models.DateTimeField(default=timezone.now())

    # todo: contestants

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.id:
            self.slug_name = slugify(self.name)
        super(Contest, self).save(*args, **kwargs)

    @property
    def is_active(self):
        t = timezone.now()
        return self.start <= t < self.end

    @property
    def has_finished(self):
        return self.end >= timezone.now()

    @property
    def has_started(self):
        return self.start >= timezone.now()
    
    @property
    def status(self):
        if self.is_active:
            return 'active'
        elif self.has_finished:
            return 'finished'
        else:
            return 'due'

    # todo: get scores for contestants


class Problem(models.Model):
    name = models.CharField(max_length=255)
    slug_name = models.SlugField(unique=True)
    statement = models.TextField(default='')
    contest = models.ForeignKey(Contest, null=False, default=Contest()) # todo : method for default contest
    points = models.IntegerField(default=500)

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.id:
            self.slug = slugify(self.name)
        super(Problem, self).save(*args, **kwargs)
