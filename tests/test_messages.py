import ast
import re
from pathlib import Path

import acc_race_stats
from acc_race_stats.messages import PORTUGUESE, set_language, tr

SOURCES = sorted(Path(acc_race_stats.__file__).parent.glob("*.py"))


def calls(name):
    for path in SOURCES:
        for node in ast.walk(ast.parse(path.read_text("utf-8"))):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == name:
                yield path.name, node


def test_every_text_is_translated_and_none_is_left_over():
    assert {node.args[0].value for _, node in calls("tr")} == set(PORTUGUESE)


def test_translations_have_the_same_fields():
    for english, portuguese in PORTUGUESE.items():
        assert sorted(re.findall(r"{\w+}", english)) == sorted(re.findall(r"{\w+}", portuguese)), english


def test_every_field_is_given():
    for where, node in calls("tr"):
        given = {keyword.arg for keyword in node.keywords}
        assert set(re.findall(r"{(\w+)}", node.args[0].value)) == given, (where, node.lineno)


def test_nothing_is_printed_without_translation():
    allowed = {"ACC Race Stats\n", "Idioma / Language"}
    for name in ("print", "ask", "choose", "ask_until", "ServerError", "UserError", "ResultError", "ConfigError"):
        for where, node in calls(name):
            for argument in node.args:
                parts = argument.values if isinstance(argument, ast.JoinedStr) else [argument]
                for part in parts:
                    if isinstance(part, ast.Constant) and isinstance(part.value, str):
                        assert part.value in allowed or not re.search(r"[A-Za-z]{2}", part.value), (where, part.value)


def test_language_switch():
    set_language("pt-br")
    assert tr("Connected.") == "Conectado."
    set_language("en")
    assert tr("Connected.") == "Connected."
