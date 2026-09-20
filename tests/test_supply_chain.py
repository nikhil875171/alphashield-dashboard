import unittest
import networkx as nx
from src.supply_chain_graph import build_supply_chain_network, get_supplier_ripple_effect, render_interactive_network_graph


class TestSupplyChainGraph(unittest.TestCase):
    def setUp(self):
        self.G = build_supply_chain_network()

    def test_graph_nodes_and_edges(self):
        """Verify networkx directed graph has nodes, edges, and valid tiers."""
        self.assertIsInstance(self.G, nx.DiGraph)
        self.assertGreater(len(self.G.nodes), 15)
        self.assertGreater(len(self.G.edges), 15)

        # Check key Anchor OEMs exist
        for anchor in ["TSLA", "MSFT", "AMZN"]:
            self.assertIn(anchor, self.G.nodes)
            self.assertEqual(self.G.nodes[anchor]["tier"], "ANCHOR_OEM")

        # Check key Tier-1 suppliers exist
        for t1 in ["MOTHERSON.NS", "VRT", "ETN"]:
            self.assertIn(t1, self.G.nodes)
            self.assertEqual(self.G.nodes[t1]["tier"], "TIER_1")

        # Check key Tier-2 suppliers exist
        for t2 in ["SONACOMS.NS", "COHR", "6324.T", "6268.T"]:
            self.assertIn(t2, self.G.nodes)
            self.assertEqual(self.G.nodes[t2]["tier"], "TIER_2")

        # Check key Tier-3 suppliers exist
        for t3 in ["2049.TW", "MOG.A", "WELCORP.NS", "DD"]:
            self.assertIn(t3, self.G.nodes)
            self.assertEqual(self.G.nodes[t3]["tier"], "TIER_3")

    def test_supplier_ripple_lookup(self):
        """Verify ripple effect lookup for specific anchors and suppliers."""
        # Check Vertiv (VRT) in AI Datacenter Case
        ripple_vrt = get_supplier_ripple_effect("VRT")
        self.assertEqual(ripple_vrt.role, "TIER_1")
        self.assertIn("MSFT", ripple_vrt.connected_anchors)
        self.assertIn("Liquid Cooling", ripple_vrt.case_description)

        # Check Sona BLW (SONACOMS.NS) in EV Case
        ripple_sona = get_supplier_ripple_effect("SONACOMS.NS")
        self.assertEqual(ripple_sona.role, "TIER_2")

        # Check Harmonic Drive Systems (6324.T) in Humanoid Automation Case
        ripple_harmonic = get_supplier_ripple_effect("6324.T")
        self.assertEqual(ripple_harmonic.role, "TIER_2")
        self.assertEqual(ripple_harmonic.case_name, "Humanoid & Factory Automation")

        # Check Energy Recovery (ERII) in Desalination Case
        ripple_erii = get_supplier_ripple_effect("ERII")
        self.assertEqual(ripple_erii.role, "TIER_2")
        self.assertEqual(ripple_erii.case_name, "Water Desalination & Treatment")

        # Check Telecom Case E
        ripple_tejas = get_supplier_ripple_effect("TEJASNET.NS")
        self.assertEqual(ripple_tejas.role, "TIER_2")
        self.assertIn("BHARTIARTL.NS", ripple_tejas.connected_anchors)
        self.assertEqual(ripple_tejas.case_name, "5G/6G Telecom & Networks")

        # Check Textiles Case F
        ripple_arvind = get_supplier_ripple_effect("ARVIND.NS")
        self.assertEqual(ripple_arvind.role, "TIER_2")
        self.assertIn("PAGEIND.NS", ripple_arvind.connected_anchors)
        self.assertEqual(ripple_arvind.case_name, "Textiles, Technical Fibers & High-Performance Fabrics")

    def test_interactive_plot_rendering(self):
        """Verify Plotly figure is generated without errors."""
        fig = render_interactive_network_graph(highlight_ticker="VRT")
        self.assertIsNotNone(fig)
        self.assertEqual(len(fig.data), 2)  # 1 edge trace + 1 node trace


if __name__ == "__main__":
    unittest.main()
