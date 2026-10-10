import unittest
from dd_switch_recon_pipeline import stable_board_lots,should_buffer

class ReconResearch(unittest.TestCase):
    def test_precision_only_not_economic_roundup(self):
        self.assertEqual(stable_board_lots(119999.99999999999),120000)
        self.assertEqual(stable_board_lots(119999.999),119000)
        self.assertEqual(stable_board_lots(-10),0)
    def test_mandatory_transitions_never_buffered(self):
        for policy in ('one_lot','sleeve_5bp','sleeve_20bp'):
            self.assertFalse(should_buffer(policy,-1000,1000,0,20,1e8,False))
            self.assertFalse(should_buffer(policy,1000,0,1000,20,1e8,False))
            self.assertFalse(should_buffer(policy,-1000,5000,4000,20,1e8,True))
    def test_relative_threshold_and_lot_buffer(self):
        self.assertTrue(should_buffer('one_lot',-1000,5000,4000,20,1e8,False))
        self.assertFalse(should_buffer('one_lot',-2000,5000,3000,20,1e8,False))
        self.assertTrue(should_buffer('sleeve_5bp',1000,5000,6000,20,1e8,False))
        self.assertFalse(should_buffer('sleeve_5bp',1000,5000,6000,60,1e8,False))
