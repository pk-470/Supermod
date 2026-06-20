import random
from typing import Optional

from supermod.features.qotd._constants import *


def qotd_get() -> Optional[list[str]]:
    questions: list[list[str]] = qotd_wks().get_all_values()
    questions = [
        question
        for question in questions
        if question[2]
        and (question[1] == "N" and not question[3] or question[1] == "Y")
    ]
    if not questions:
        return None
    question_full = random.choice(questions)
    return question_full


def mark_as_used(question: list[str]) -> None:
    wks = qotd_wks()
    cell = wks.find(question[2])
    assert cell is not None
    question_row = cell.row
    current = wks.cell(question_row, 4).numeric_value or 0
    wks.update_cell(question_row, 4, int(current) + 1)
