"""Prespecified research risk overlays; no live configuration or fitted values."""
from dataclasses import dataclass
POLICIES=('CORE_ON','DD_FIXED_FUNDED','MARKET_HALF_FAST','MARKET_HALF_CONFIRM','MARKET_FULL_CONFIRM','DD_PLUS_HALF')
@dataclass
class RiskOverlay:
    policy:str
    defensive:bool=False
    triggers:int=0
    recoveries:int=0
    def observe(self,market,dd_active):
        if self.policy not in POLICIES:raise ValueError('Unknown frozen policy')
        warning=market['dd63']<=-.05 and market['ret5']<=-.03
        trigger=market['dd63']<=-.08 and market['ret20']<=-.03
        recover=market['above_ma20'] and market['ret5']>0
        self.triggers=self.triggers+1 if trigger else 0
        self.recoveries=self.recoveries+1 if recover else 0
        if self.triggers>=2:self.defensive=True
        required=1 if self.policy=='MARKET_HALF_FAST' else 3
        if self.recoveries>=required:self.defensive=False
        market_scale=(0. if self.policy=='MARKET_FULL_CONFIRM' else .5) if self.defensive else 1.
        if self.policy=='CORE_ON':scale=1.
        elif self.policy=='DD_FIXED_FUNDED':scale=float(dd_active)
        elif self.policy=='DD_PLUS_HALF':scale=min(float(dd_active),market_scale)
        else:scale=market_scale
        return dict(scale=scale,warning=warning,trigger=trigger,recover=recover,defensive=self.defensive,
                    trigger_days=self.triggers,recovery_days=self.recoveries)
