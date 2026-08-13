"""
学习进度持久化 — 支持多题库
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List
from .fsrs import Card


def save_all_decks(filepath: str, decks: List[dict], active_deck: Optional[str] = None) -> None:
    """保存所有题库进度

    decks: list of deck dicts, each with keys:
        - deck_id: str (题库唯一标识，用文件路径)
        - deck_name: str (显示名称)
        - deck_path: str (原始文件路径)
        - study_days: int
        - current_day: int
        - new_cards_per_day: int
        - new_card_indices: list
        - new_card_ptr: int
        - cards: Dict[str, Card]
    active_deck: 当前激活的题库 deck_id
    """
    data = {
        'active_deck': active_deck,
        'saved_at': datetime.now().isoformat(),
        'decks': [],
    }
    for d in decks:
        data['decks'].append({
            'deck_id': d['deck_id'],
            'deck_name': d['deck_name'],
            'deck_path': d['deck_path'],
            'study_days': d.get('study_days', 7),
            'current_day': d.get('current_day', 0),
            'new_cards_per_day': d.get('new_cards_per_day', 0),
            'new_card_indices': d.get('new_card_indices', []),
            'new_card_ptr': d.get('new_card_ptr', 0),
            'cards': {qid: card.to_dict() for qid, card in d.get('cards', {}).items()},
        })
    p = Path(filepath)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_all_decks(filepath: str) -> Optional[dict]:
    """加载所有题库进度

    返回 dict:
        - active_deck: str or None
        - decks: list of deck dicts (cards 已还原为 Card 对象)
    """
    p = Path(filepath)
    if not p.exists():
        return None
    with open(p, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for d in data.get('decks', []):
        cards = {}
        for qid, card_dict in d.get('cards', {}).items():
            cards[qid] = Card.from_dict(card_dict)
        d['cards'] = cards
    return data


def save_progress(filepath: str, cards: Dict[str, Card], deck_path: Optional[str] = None,
                  study_days: int = 7, current_day: int = 0,
                  new_cards_per_day: int = 0, new_card_indices: Optional[list] = None) -> None:
    """保存单题库进度（向后兼容）"""
    data = {
        'deck_path': deck_path,
        'study_days': study_days,
        'current_day': current_day,
        'new_cards_per_day': new_cards_per_day,
        'new_card_indices': new_card_indices or [],
        'saved_at': datetime.now().isoformat(),
        'cards': {qid: card.to_dict() for qid, card in cards.items()},
    }
    p = Path(filepath)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_progress(filepath: str) -> Optional[dict]:
    """加载单题库进度（向后兼容）"""
    p = Path(filepath)
    if not p.exists():
        return None
    with open(p, 'r', encoding='utf-8') as f:
        data = json.load(f)
    cards = {}
    for qid, card_dict in data.get('cards', {}).items():
        cards[qid] = Card.from_dict(card_dict)
    data['cards'] = cards
    return data
