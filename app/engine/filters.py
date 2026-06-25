from app.db.models import Candidates, Jobs


def filter(candidates: list[Candidates], job : Jobs):
    eligible_candidates : list[Candidates] = [candidate for candidate in candidates if candidate.years_experience >= job.min_experience and job.required_certs in candidate.certifications]

    return eligible_candidates