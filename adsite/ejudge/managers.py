from django.db import models
from django.db.models import Q
from django.utils import timezone


class ContestManager(models.Manager):

    def for_user(self, user):
        """ Filter only to those contest in which user is participant and the
        contest has started. """
        if not user.is_authenticated():
            return self.none()
        if user.is_staff:
            return self.get_queryset()
        t = timezone.now()
        return (self.get_queryset().filter(participants=user, start__lt=t)
                                   .order_by('start'))


class ActiveContestManager(ContestManager):
    def get_queryset(self):
        t = timezone.now()
        return (super(ActiveContestManager, self).get_queryset()
                                                 .filter(start__lt=t,
                                                         finish__gt=t))


class InactiveContestManager(ContestManager):
    def get_queryset(self):
        t = timezone.now()
        return (super(InactiveContestManager, self).get_queryset()
                                                   .filter(Q(start__gt=t) |
                                                           Q(finish__lt=t)))


class ChallengeManager(models.Manager):

    def for_user(self, user):
        """ Filter to only those challenges which are part of the started
        contests and the user is participant. """
        if not user.is_authenticated():
            return self.none()
        if user.is_staff:
            return self.get_queryset()
        t = timezone.now()
        return self.get_queryset().filter(contest__participants=user,
                                          contest__start__lt=t)
