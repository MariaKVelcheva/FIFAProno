import json

from django.contrib import messages as flash
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import JoinForm, SignUpForm, SquadForm, WagerForm
from .models import Match, Membership, Message, Prediction, Squad, Wager
from django.contrib.auth import get_user_model
User = get_user_model()


def signup(request):
    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        user.profile.avatar = form.cleaned_data["avatar"]
        user.profile.save()
        login(request, user)
        return redirect("dashboard")
    return render(request, "registration/signup.html", {"form": form})


def dashboard(request):
    now = timezone.now()
    upcoming = Match.objects.filter(kickoff__gte=now).select_related("home_team", "away_team")[:18]
    finished = (
        Match.objects.filter(status="FINISHED")
        .select_related("home_team", "away_team")
        .order_by("-kickoff")[:12]
    )
    if request.user.is_authenticated:
        preds = {p.match_id: p for p in Prediction.objects.filter(user=request.user)}
        pred_total = Prediction.objects.filter(user=request.user).aggregate(s=Sum("points"))["s"] or 0
        wager_wins = Wager.objects.filter(winner=request.user, status=Wager.SETTLED).count()
        total = pred_total + wager_wins * 10
    else:
        preds, total = {}, 0
    return render(request, "prono/dashboard.html", {"upcoming": upcoming, "finished": finished, "preds": preds, "total": total})


@login_required
@require_POST
def predict(request, match_id):
    match = get_object_or_404(Match, pk=match_id)
    if not match.is_open:
        return JsonResponse({"error": "Predictions are locked for this match."}, status=400)
    try:
        data = json.loads(request.body)
        home, away = int(data["home"]), int(data["away"])
        assert 0 <= home <= 20 and 0 <= away <= 20
    except (ValueError, KeyError, AssertionError, json.JSONDecodeError):
        return JsonResponse({"error": "Invalid score."}, status=400)
    Prediction.objects.update_or_create(
        user=request.user, match=match, defaults={"home_score": home, "away_score": away}
    )
    return JsonResponse({"saved": True, "home": home, "away": away})


@login_required
def squads(request):
    squad_form, join_form = SquadForm(), JoinForm()
    if request.method == "POST":
        if "create" in request.POST:
            squad_form = SquadForm(request.POST)
            if squad_form.is_valid():
                squad = squad_form.save(commit=False)
                squad.created_by = request.user
                squad.save()
                Membership.objects.create(user=request.user, squad=squad)
                return redirect("squad_detail", squad.id)
        elif "join" in request.POST:
            join_form = JoinForm(request.POST)
            if join_form.is_valid():
                squad = Squad.objects.filter(code__iexact=join_form.cleaned_data["code"]).first()
                if squad:
                    Membership.objects.get_or_create(user=request.user, squad=squad)
                    return redirect("squad_detail", squad.id)
                flash.error(request, "No squad found with that code.")
    my_squads = Squad.objects.filter(membership__user=request.user).annotate(n=Count("membership"))
    return render(
        request,
        "prono/squads.html",
        {"my_squads": my_squads, "squad_form": squad_form, "join_form": join_form},
    )


def _member_required(request, squad):
    return Membership.objects.filter(user=request.user, squad=squad).exists()


@login_required
def squad_detail(request, squad_id):
    squad = get_object_or_404(Squad, pk=squad_id)
    if not _member_required(request, squad):
        return HttpResponseForbidden("Not your squad.")

    Membership.objects.filter(user=request.user, squad=squad).update(last_read_at=timezone.now())

    wager_form = WagerForm(squad, request.user)
    if request.method == "POST":
        if "message" in request.POST:
            text = request.POST.get("text", "").strip()[:300]
            if text:
                Message.objects.create(squad=squad, author=request.user, text=text)
            return redirect("squad_detail", squad.id)
        if "wager" in request.POST:
            wager_form = WagerForm(squad, request.user, request.POST)
            if wager_form.is_valid():
                wager = wager_form.save(commit=False)
                wager.squad, wager.challenger = squad, request.user
                wager.save()
                return redirect("squad_detail", squad.id)

    from django.contrib.auth import get_user_model

    User = get_user_model()

    leaderboard = list(
        User.objects.filter(membership__squad=squad)
        .select_related("profile")
        .annotate(
            total=Sum("prediction__points"),
            exacts=Count("prediction", filter=Q(prediction__points__gte=3)),
        )
    )
    wager_wins = dict(
        Wager.objects.filter(squad=squad, status=Wager.SETTLED)
        .exclude(winner__isnull=True)
        .values("winner")
        .annotate(n=Count("id"))
        .values_list("winner", "n")
    )
    for u in leaderboard:
        bonus = wager_wins.get(u.id, 0) * 10
        u.total = (u.total or 0) + bonus
    leaderboard.sort(key=lambda u: -u.total)

    return render(
        request,
        "prono/squad_detail.html",
        {
            "squad": squad,
            "leaderboard": leaderboard,
            "wagers": squad.wagers.select_related("challenger", "opponent", "winner", "match"),
            "wager_form": wager_form,
            "chat": squad.messages.select_related("author__profile").order_by("-created_at")[:50][::-1],
        },
    )


@login_required
def squad_messages(request, squad_id):
    squad = get_object_or_404(Squad, pk=squad_id)
    if not _member_required(request, squad):
        return HttpResponseForbidden()
    msgs = squad.messages.select_related("author__profile").order_by("-created_at")[:50]
    return JsonResponse(
        {
            "messages": [
                {
                    "author": m.author.username,
                    "avatar": m.author.profile.avatar,
                    "text": m.text,
                    "at": m.created_at.strftime("%H:%M"),
                }
                for m in reversed(msgs)
            ]
        }
    )


@login_required
@require_POST
def wager_action(request, wager_id, action):
    wager = get_object_or_404(Wager, pk=wager_id)
    me = request.user
    if action == "accept" and me == wager.opponent and wager.status == Wager.PROPOSED:
        wager.status = Wager.ACCEPTED
    elif action == "decline" and me == wager.opponent and wager.status == Wager.PROPOSED:
        wager.status = Wager.DECLINED
    elif action.startswith("settle-") and me in (wager.challenger, wager.opponent) and wager.status == Wager.ACCEPTED:
        winner = wager.challenger if action == "settle-challenger" else wager.opponent
        wager.status, wager.winner = Wager.SETTLED, winner
    else:
        return HttpResponseForbidden()
    wager.save()
    return redirect("squad_detail", wager.squad_id)


@login_required
def notifications(request):
    data = []
    for m in Membership.objects.filter(user=request.user).select_related("squad"):
        count = Message.objects.filter(squad=m.squad, created_at__gt=m.last_read_at).exclude(author=request.user).count()
        if count:
            data.append({"squad_id": m.squad_id, "squad_name": m.squad.name, "count": count})
    return JsonResponse({"squads": data})


def player_profile(request, username):
    from django.db.models import Sum
    viewed = get_object_or_404(
        User.objects.select_related("profile"), username=username
    )
    is_own = request.user.is_authenticated and request.user == viewed

    shared_squads = []
    if request.user.is_authenticated:
        shared_squads = Squad.objects.filter(
            membership__user=request.user
        ).filter(
            membership__user=viewed
        ).distinct()

    past_preds = Prediction.objects.filter(
        user=viewed, match__status="FINISHED"
    ).select_related("match__home_team", "match__away_team").order_by("-match__kickoff")

    upcoming_preds = []
    if is_own:
        upcoming_preds = Prediction.objects.filter(
            user=viewed, match__kickoff__gt=timezone.now()
        ).select_related("match__home_team", "match__away_team").order_by("match__kickoff")

    pred_total = Prediction.objects.filter(user=viewed).aggregate(s=Sum("points"))["s"] or 0
    wager_wins = Wager.objects.filter(winner=viewed, status=Wager.SETTLED).count()
    total = pred_total + wager_wins * 10

    settled_wagers = Wager.objects.filter(
        status=Wager.SETTLED
    ).filter(
        Q(challenger=viewed) | Q(opponent=viewed)
    ).select_related("challenger", "opponent", "winner")

    wager_rows = []
    for w in settled_wagers:
        loser = w.opponent if w.winner == w.challenger else w.challenger
        wager_rows.append({
            "wager": w,
            "won": w.winner == viewed,
            "winner": w.winner,
            "loser": loser,
        })

    return render(request, "prono/player_profile.html", {
        "viewed": viewed,
        "is_own": is_own,
        "shared_squads": shared_squads,
        "past_preds": past_preds,
        "upcoming_preds": upcoming_preds,
        "total": total,
        "wager_rows": wager_rows,
    })


def compare_cakes(request, username, other_username):
    if not request.user.is_authenticated:
        return redirect("login")
    viewed = get_object_or_404(User.objects.select_related("profile"), username=username)
    other = get_object_or_404(User.objects.select_related("profile"), username=other_username)

    shared = Squad.objects.filter(
        membership__user=request.user
    ).filter(
        membership__user=viewed
    ).filter(
        membership__user=other
    ).exists()
    if not shared:
        return HttpResponseForbidden("You need to be in a shared squad to compare.")

    finished = Match.objects.filter(status="FINISHED").order_by("-kickoff")
    preds_a = {p.match_id: p for p in Prediction.objects.filter(user=viewed, match__status="FINISHED")}
    preds_b = {p.match_id: p for p in Prediction.objects.filter(user=other, match__status="FINISHED")}
    rows = [{"match": m, "pred_a": preds_a.get(m.id), "pred_b": preds_b.get(m.id)}
            for m in finished]

    compare_wagers = Wager.objects.filter(
        status=Wager.SETTLED
    ).filter(
        Q(challenger=viewed, opponent=other) | Q(challenger=other, opponent=viewed)
    ).select_related("challenger", "opponent", "winner")

    compare_wager_rows = []
    for w in compare_wagers:
        loser = w.opponent if w.winner == w.challenger else w.challenger
        compare_wager_rows.append({
            "wager": w,
            "won": w.winner == viewed,
            "winner": w.winner,
            "loser": loser,
        })

    return render(request, "prono/compare_cakes.html", {
        "viewed": viewed,
        "other": other,
        "rows": rows,
        "compare_wager_rows": compare_wager_rows,
    })


@login_required
@require_POST
def claim_wager(request, wager_id):
    wager = get_object_or_404(Wager, pk=wager_id)
    if wager.winner != request.user or wager.status != Wager.SETTLED:
        return HttpResponseForbidden()
    wager.claimed = True
    wager.save(update_fields=["claimed"])
    return JsonResponse({"claimed": True})