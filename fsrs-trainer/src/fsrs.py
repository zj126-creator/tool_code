"""
FSRS-5.0 间隔重复算法核心实现

参考: https://github.com/open-spaced-repetition/fsrs4anki/wiki/The-Algorithm
"""

import math
from enum import IntEnum
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional


class Rating(IntEnum):
    """FSRS 评级"""
    AGAIN = 1
    HARD = 2
    GOOD = 3
    EASY = 4


class State(IntEnum):
    """卡片学习状态"""
    NEW = 0
    LEARNING = 1
    REVIEW = 2
    RELEARNING = 3


# FSRS 权重 (基于 FSRS-4.5 优化参数, 确保复习稳定性更新有效)
# 参考: https://github.com/open-spaced-repetition/fsrs4anki
DEFAULT_W = [
    0.4072, 1.1829, 3.1262, 15.4722, 7.2102,
    0.5316, 1.0661, 0.0111, 1.5325, 0.1547,
    1.0347, 1.9395, 0.1097, 0.1080, 0.4350,
    2.3239, 2.7232, 0.4350, 0.4350
]

# 目标可检索性 (默认 90%)
DEFAULT_TARGET_R = 0.9

# 最大间隔 (天)
MAX_INTERVAL = 36500


@dataclass
class Card:
    """FSRS 卡片记忆状态"""
    # 记忆状态
    stability: float = 0.0
    difficulty: float = 0.0
    # 卡片状态
    state: State = State.NEW
    # 复习次数
    reps: int = 0
    lapses: int = 0
    # 时间记录
    last_review: Optional[datetime] = None
    next_review: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            'stability': self.stability,
            'difficulty': self.difficulty,
            'state': int(self.state),
            'reps': self.reps,
            'lapses': self.lapses,
            'last_review': self.last_review.isoformat() if self.last_review else None,
            'next_review': self.next_review.isoformat() if self.next_review else None,
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'Card':
        card = cls()
        card.stability = d.get('stability', 0.0)
        card.difficulty = d.get('difficulty', 0.0)
        card.state = State(d.get('state', 0))
        card.reps = d.get('reps', 0)
        card.lapses = d.get('lapses', 0)
        lr = d.get('last_review')
        nr = d.get('next_review')
        card.last_review = datetime.fromisoformat(lr) if lr else None
        card.next_review = datetime.fromisoformat(nr) if nr else None
        return card


class Scheduler:
    """FSRS-5.0 调度器"""

    def __init__(self, w=None, target_r=DEFAULT_TARGET_R):
        self.w = w if w is not None else list(DEFAULT_W)
        self.target_r = target_r

    def get_retrievability(self, card: Card, now: Optional[datetime] = None) -> float:
        """计算可检索性 R = (1 + t/(9*s))^(-1)"""
        if card.state == State.NEW or card.last_review is None:
            return 0.0
        now = now or datetime.now(timezone.utc)
        elapsed_days = max(0.0, (now - card.last_review).total_seconds() / 86400.0)
        if card.stability <= 0:
            return 0.0
        return (1.0 + elapsed_days / (9.0 * card.stability)) ** (-1.0)

    def _init_stability(self, rating: Rating) -> float:
        """新牌初始稳定性: s0 = w[rating-1]"""
        return max(0.1, self.w[rating - 1])

    def _init_difficulty(self, rating: Rating) -> float:
        """新牌初始难度: d0 = w[4] - (rating-3) * w[5]"""
        d = self.w[4] - (rating - 3) * self.w[5]
        return self._clamp_difficulty(d)

    def _clamp_difficulty(self, d: float) -> float:
        """难度钳制到 [1, 10]"""
        return max(1.0, min(10.0, d))

    def _next_difficulty(self, d: float, rating: Rating) -> float:
        """复习后更新难度: d' = d - w[6] * (rating - 3)"""
        new_d = d - self.w[6] * (rating - 3)
        return self._clamp_difficulty(new_d)

    def _next_recall_stability(self, d: float, s: float, r: float, rating: Rating) -> float:
        """复习后稳定性更新"""
        if rating == Rating.AGAIN:
            # 遗忘: s' = w[11] * s^(-w[12]) * (d^(-w[13]) - 1) 或简化模型
            forgetting_factor = self.w[11] * (s ** (-self.w[12])) * ((d ** (-self.w[13])) - 1.0)
            new_s = s * forgetting_factor
        elif rating == Rating.HARD:
            new_s = s * (1.0 + self.w[7] * (d ** (-self.w[8])) * ((1.0 / r) - 1.0) ** self.w[9] * self.w[10])
        elif rating == Rating.GOOD:
            new_s = s * (1.0 + self.w[14] * (d ** (-self.w[15])) * ((1.0 / r) - 1.0) ** self.w[16] * self.w[17])
        else:  # EASY
            new_s = s * (1.0 + self.w[14] * (d ** (-self.w[15])) * ((1.0 / r) - 1.0) ** self.w[16] * self.w[17] * self.w[18])
        return max(0.1, new_s)

    def _next_interval(self, s: float) -> int:
        """计算下次复习间隔(天): interval = s * 9 * (1/R_target - 1)"""
        interval = s * 9.0 * (1.0 / self.target_r - 1.0)
        return max(1, min(MAX_INTERVAL, int(round(interval))))

    def schedule(self, card: Card, rating: Rating, now: Optional[datetime] = None) -> Card:
        """
        根据评级更新卡片状态并安排下次复习

        返回更新后的 card（原地修改并返回）
        """
        now = now or datetime.now(timezone.utc)

        if card.state == State.NEW:
            # 新牌: 初始化稳定性和难度
            card.stability = self._init_stability(rating)
            card.difficulty = self._init_difficulty(rating)
            if rating == Rating.AGAIN:
                card.state = State.LEARNING
            else:
                card.state = State.REVIEW
        elif card.state in (State.LEARNING, State.RELEARNING):
            # 学习/重学状态
            if rating == Rating.AGAIN:
                card.difficulty = self._next_difficulty(card.difficulty, rating)
                # 保持在学习状态
            else:
                card.difficulty = self._next_difficulty(card.difficulty, rating)
                r = self.get_retrievability(card, now) if card.stability > 0 else 0.5
                card.stability = self._next_recall_stability(card.difficulty, card.stability, r, rating)
                card.state = State.REVIEW
        elif card.state == State.REVIEW:
            # 复习状态
            r = self.get_retrievability(card, now)
            card.difficulty = self._next_difficulty(card.difficulty, rating)

            if rating == Rating.AGAIN:
                # 遗忘: 进入重学
                card.lapses += 1
                card.stability = self._next_recall_stability(card.difficulty, card.stability, r, rating)
                card.state = State.RELEARNING
            else:
                card.stability = self._next_recall_stability(card.difficulty, card.stability, r, rating)

        card.reps += 1
        card.last_review = now

        # 计算下次复习时间
        interval_days = self._next_interval(card.stability)
        card.next_review = now + timedelta(days=interval_days)

        return card

    def is_due(self, card: Card, now: Optional[datetime] = None) -> bool:
        """检查卡片是否到期需要复习"""
        now = now or datetime.now(timezone.utc)
        if card.state == State.NEW:
            return True
        if card.next_review is None:
            return True
        return now >= card.next_review
