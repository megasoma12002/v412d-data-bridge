import unittest
import pandas as pd
from dd_switch_capital_policy import CapitalController,POLICIES
from dd_switch_capital_research import simulate

class CapitalPolicyTest(unittest.TestCase):
    def test_defense_deep_and_gradual_recovery(self):
        c=CapitalController(POLICIES[3])
        self.assertEqual(c.observe(100,.1)['scale'],.95)
        self.assertEqual(c.observe(91,-.1)['scale'],.60)
        self.assertEqual(c.observe(87,-.1)['scale'],.40)
        self.assertEqual(c.observe(96,.1)['scale'],.40)
        self.assertAlmostEqual(c.observe(99,.1)['scale'],.45)

    def test_cash_reserve_and_no_leverage(self):
        c=CapitalController(POLICIES[4]);targets,d=c.allocate({'0050':.6,'2880':.4},100,.1)
        self.assertAlmostEqual(sum(targets.values()),.9)
        self.assertAlmostEqual(d['reserve_floor'],.1)
        with self.assertRaises(ValueError):c.allocate({'0050':1.1},100,.1)

    def test_no_averaging_down(self):
        c=CapitalController(POLICIES[4]);scales=[c.observe(n,-.1)['scale'] for n in (100,90,85,80)]
        self.assertEqual(scales,sorted(scales,reverse=True))

    def test_prefix_invariance(self):
        r=pd.Series([0,-.1,.02,.3],index=pd.date_range('2020-01-01',periods=4))
        a=simulate(r.iloc[:3],POLICIES[3]);b=simulate(r,POLICIES[3]).iloc[:3]
        pd.testing.assert_frame_equal(a,b)

    def test_current_return_not_known_at_decision(self):
        r=pd.Series([0,-.1],index=pd.date_range('2020-01-01',periods=2))
        a=simulate(r,POLICIES[3]);r.iloc[1]=.5;b=simulate(r,POLICIES[3])
        self.assertEqual(a.scale.tolist(),b.scale.tolist())

if __name__=='__main__':unittest.main()
