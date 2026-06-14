EXACT = 3
OUTCOME = 1
KNOCKOUT_MULTIPLIER = 2


def outcome(home, away):
    if home > away:
        return "H"
    if away > home:
        return "A"
    return "D"


def points_for(prediction, match):
    if match.home_score is None or match.away_score is None:
        return None
    if prediction.home_score == match.home_score and prediction.away_score == match.away_score:
        pts = EXACT
    elif outcome(prediction.home_score, prediction.away_score) == outcome(match.home_score, match.away_score):
        pts = OUTCOME
    else:
        pts = 0
    if match.is_knockout:
        pts *= KNOCKOUT_MULTIPLIER
    return pts


def score_match(match):
    from .models import Prediction

    for pred in Prediction.objects.filter(match=match):
        pred.points = points_for(pred, match)
        pred.save(update_fields=["points"])
