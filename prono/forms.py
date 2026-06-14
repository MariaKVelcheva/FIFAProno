from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import AVATARS, Squad, Wager


class SignUpForm(UserCreationForm):
    avatar = forms.ChoiceField(
        choices=[(a, a) for a in AVATARS],
        widget=forms.RadioSelect,
        initial="⚽",
    )


class SquadForm(forms.ModelForm):
    class Meta:
        model = Squad
        fields = ["name"]


class JoinForm(forms.Form):
    code = forms.CharField(max_length=10, label="Squad code")


class WagerForm(forms.ModelForm):
    class Meta:
        model = Wager
        fields = ["opponent", "match", "stake"]

    def __init__(self, squad, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.contrib.auth import get_user_model

        User = get_user_model()
        self.fields["opponent"].queryset = User.objects.filter(
            membership__squad=squad
        ).exclude(pk=user.pk)
        from .models import Match

        self.fields["match"].required = False
        self.fields["match"].queryset = Match.objects.filter(
            status__in=["SCHEDULED", "TIMED"]
        )[:40]
