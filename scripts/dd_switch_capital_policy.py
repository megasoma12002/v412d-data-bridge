"""Account-level risk budget. No leverage, external refill, or loss averaging.

Pure research controller: callers must execute targets after observation and
account for share fills, corporate actions, receivables and cash independently.
"""
from dataclasses import dataclass
import math

@dataclass(frozen=True)
class Policy:
    name: str
    reserve: float = 0.0
    trigger: float = 1.0
    floor: float = 1.0
    deep_trigger: float = 1.0
    deep_floor: float = 1.0
    recovery: float = 0.03
    step: float = 0.05

POLICIES = (
    Policy('BASELINE'),
    Policy('RESERVE_05',reserve=.05,floor=.95,deep_floor=.95),
    Policy('RESERVE_10',reserve=.10,floor=.90,deep_floor=.90),
    Policy('DD08_F60',reserve=.05,trigger=.08,floor=.60,deep_trigger=.12,deep_floor=.40),
    Policy('DD08_F40',reserve=.10,trigger=.08,floor=.40,deep_trigger=.12,deep_floor=.25),
)

@dataclass
class CapitalController:
    policy: Policy
    peak: float = 0.0
    scale: float = 1.0
    regime: str = 'NORMAL'

    def observe(self, nav, trailing_return):
        if not math.isfinite(nav) or nav <= 0 or not math.isfinite(trailing_return):
            raise ValueError('Finite positive NAV and finite momentum required')
        self.peak=max(self.peak,float(nav))
        dd=max(0.0,1-float(nav)/self.peak)
        p=self.policy
        ceiling=1-p.reserve
        if dd >= p.deep_trigger:
            self.regime='DEEP'
        elif dd >= p.trigger and self.regime != 'DEEP':
            self.regime='DEFENSIVE'
        elif dd <= p.recovery and trailing_return > 0:
            self.regime='NORMAL'
        target=min(ceiling,p.deep_floor if self.regime=='DEEP' else p.floor if self.regime=='DEFENSIVE' else ceiling)
        self.scale=min(target,self.scale+p.step) if target>self.scale else target
        if not 0 <= self.scale <= 1:
            raise ValueError('Invalid policy risk budget')
        return dict(scale=self.scale,regime=self.regime,account_dd=dd,
                    reserve_floor=1-self.scale,nav_peak=self.peak)

    def allocate(self, weights, nav, trailing_return):
        if any(not math.isfinite(w) or w<0 for w in weights.values()) or sum(weights.values())>1+1e-9:
            raise ValueError('Invalid full-account target weights')
        decision=self.observe(nav,trailing_return)
        targets={code:w*decision['scale'] for code,w in weights.items()}
        return targets,decision
