import random

from .qotd_constants import *


def qotd_get() -> list[str]:
    questions: list[list[str]] = QOTD_WKS.get_all_values()
    questions = [
        question
        for question in questions
        if question[2]
        and (question[1] == "N" and not question[3] or question[1] == "Y")
    ]
    question_full = random.choice(questions)
    return question_full


def mark_as_used(question: list[str]) -> None:
    cell = QOTD_WKS.find(question[2])
    assert cell is not None
    question_row = cell.row
    question_count = QOTD_WKS.cell(question_row, 3)
    if question_count:
        QOTD_WKS.update_cell(question_row, 4, 1)
    else:
        QOTD_WKS.update_cell(question_row, 4, int(question_count) + 1)
