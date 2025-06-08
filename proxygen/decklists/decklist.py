import os
import re
from dataclasses import dataclass, field
from typing import Any
from pathlib import Path
import more_itertools
import itertools
import csv
import scryfall

@dataclass
class CardLike:
    count: int

@dataclass
class Card(CardLike):
    card: dict[str | Any]

    def __getitem__(self, key: str) -> Any:
        return self.card[key]

    def __contains__(self, key: str) -> bool:
        return key in self.card

    @property
    def name(self) -> str:
        return self['name']

    @property
    def image_uris(self):
        return [face["image_uris"] for face in scryfall.get_faces(self.card)]

    def __format__(self, format_spec: str) -> str:
        if format_spec == "text":
            return f"{self.count} {self['name']}"
        if format_spec == "arena":
            return f"{self.count} {self['name']} ({self['set'].upper()}) {self['collector_number']}"
        raise ValueError(f"Unknown format {format_spec}")

@dataclass
class CustomCard(CardLike):
    name: str
    front_face: Path
    back_face: Path | None = None

    def __format__(self, format_spec: str) -> str:
        back_face = f'[{self.back_face}]' if self.back_face else ""

        return f'cstm: {self.count} {self.name} [{self.front_face}] {back_face}'.strip()

@dataclass
class Comment:
    text: str

    def __format__(self, format_spec: str) -> str:
        return self.text


@dataclass
class Decklist:
    entries: list[CardLike | Comment] = field(default_factory=list)
    name: str = None

    def append_card(self, count: int, card) -> None:
        self.entries.append(Card(count, card))

    def append_custom_card(self, count: int, name: str, front_face: Path, back_face: Path | None) -> None:
        self.entries.append(CustomCard(count, name, front_face, back_face))

    def append_comment(self, text) -> None:
        self.entries.append(Comment(text))

    def extend(self, other) -> None:
        self.entries.extend(other.entries)

    def save(self, file: str | Path, fmt: str = "arena", mode: str = "w") -> None:
        with open(file, mode, encoding="utf-8", newline="") as f:
            f.write(format(self, fmt) + os.linesep)

    def __format__(self, format_spec: str) -> str:
        return os.linesep.join([format(e, format_spec) for e in self.entries])

    @property
    def cards(self) -> list[CardLike]:
        return [e for e in self.entries if isinstance(e, CardLike)]

    @property
    def total_count(self) -> int:
        return sum(c.count for c in self.cards)

    @property
    def total_count_unique(self) -> int:
        return len(self.cards)

# TODO: implement actual look ups
def parse_decklist_stream(stream) -> Decklist:
    decklist = Decklist()

    for line in stream:
        if line.startswith("cstm:"):
            a = line[5:].strip()
            count, rest = more_itertools.before_and_after(str.isnumeric, iter(a))
            count = int(''.join(count))
            next(rest)
            name, rest = more_itertools.before_and_after(lambda x: x != '[', rest)
            name = ''.join(name).strip()
            next(rest)
            front_face, rest = more_itertools.before_and_after(lambda x: x != ']', rest)
            front_face = ''.join(front_face)
            next(rest)
            b = ''.join(rest).strip()
            back_face = None
            if b.startswith('['):
                back_face = itertools.takewhile(lambda x: x != ']', iter(b[1:]))
                back_face = ''.join(back_face)
            decklist.append_custom_card(count, name, Path(front_face), Path(back_face) if back_face else None)
        else:
            m = re.search(r"([0-9]+)\s+(.+?)(?:\s+\((\S*)\)\s+(\S+))\s*$", line)
            if m:
                count = int(m.group(1))
                card_name = m.group(2)
                set_id = m.group(3)
                collector_number = m.group(4)

                card = scryfall.get_card(card_name=None, set_id=set_id, collector_number=collector_number)
                decklist.append_card(count, card)
            else:
                decklist.append_comment(line.rstrip())

    return decklist


def parse_decklist(filepath: str | Path) -> Decklist:
    with open(filepath, encoding="utf-8") as f:
        decklist = parse_decklist_stream(f)

    decklist.name = Path(filepath).stem

    return decklist

def parse_csv_stream(stream) -> Decklist:
    decklist = Decklist()

    for row in csv.reader(stream):
        count = int(row[0])
        if len(row) > 4:
            front_face = row[4]
            back_face = None
            if len(row) > 5:
                back_face = row[5]

            decklist.append_custom_card(count, row[1], Path(front_face), Path(back_face) if back_face else None)
        else:
            card = scryfall.get_card(card_name=None, set_id=row[2], collector_number=row[3])
            decklist.append_card(count, card)

    return decklist

def parse_csv(filepath: str | Path) -> Decklist:
    with open(filepath, encoding="utf-8") as f:
        decklist = parse_csv_stream(f)

    decklist.name = Path(filepath).stem

    return decklist

def parse_any(filepath: str | Path) -> Decklist:

    with open(filepath, encoding="utf-8") as f:
        line = next(f)
        if line.count(',') >= 3:
            is_csv = True
        else:
            is_csv = False

    if is_csv:
        return parse_csv(filepath)
    else:
        return parse_decklist(filepath)
