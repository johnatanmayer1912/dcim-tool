"""
tests/routing_analyzer/test_normalizer.py
------------------------------------------
Automated tests for RoutingNormalizer — aligned with v7.0.65 API.

Key API changes from legacy:
  - normalize_route() returns None for invalid/multicast/empty-destination routes
  - No UNIFIED_ROUTE_MODEL or PROTOCOL_MAPPING class attributes
  - No interface abbreviation expansion (Gi → GigabitEthernet removed)
  - Admin distance for unknown protocol defaults to 0 (not 255)
  - VRF argument added to normalize_route() and normalize_routing_table()
"""

import pytest
from modules.routing_analyzer.normalizer import RoutingNormalizer


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def norm():
    return RoutingNormalizer()


# ---------------------------------------------------------------------------
# TestRoutingNormalizerBasic
# ---------------------------------------------------------------------------

class TestRoutingNormalizerBasic:

    def test_normalizer_instantiates(self, norm):
        assert norm is not None

    def test_normalize_route_returns_dict(self, norm):
        r = norm.normalize_route({'destination': '192.168.1.0/24', 'protocol': 'C'}, 'r1')
        assert isinstance(r, dict)

    def test_normalize_route_destination_cidr(self, norm):
        r = norm.normalize_route({'destination': '192.168.1.0/24'}, 'r1')
        assert r is not None
        assert r['destination'] == '192.168.1.0/24'

    def test_normalize_route_destination_network_key(self, norm):
        """Parser uses 'network' key — normalizer should accept it."""
        r = norm.normalize_route({'network': '10.0.0.0/8', 'protocol': 'S'}, 'r1')
        assert r is not None
        assert '10.0.0.0' in r['destination']

    def test_normalize_route_device_id_preserved(self, norm):
        r = norm.normalize_route({'destination': '10.0.0.0/8'}, 'my-router')
        assert r is not None
        assert r['device_id'] == 'my-router'

    def test_normalize_route_has_timestamp(self, norm):
        r = norm.normalize_route({'destination': '10.0.0.0/8'}, 'r1')
        assert r is not None
        assert 'timestamp' in r
        assert r['timestamp']  # not empty


# ---------------------------------------------------------------------------
# TestProtocolNormalization
# ---------------------------------------------------------------------------

class TestProtocolNormalization:

    def test_proto_C_maps_to_Connected(self, norm):
        r = norm.normalize_route({'destination': '10.0.0.0/8', 'protocol': 'C'}, 'r1')
        assert r['protocol'] == 'Connected'

    def test_proto_L_maps_to_Local(self, norm):
        r = norm.normalize_route({'destination': '10.0.0.0/8', 'protocol': 'L'}, 'r1')
        assert r['protocol'] == 'Local'

    def test_proto_S_maps_to_Static(self, norm):
        r = norm.normalize_route({'destination': '10.0.0.0/8', 'protocol': 'S'}, 'r1')
        assert r['protocol'] == 'Static'

    def test_proto_O_maps_to_OSPF(self, norm):
        r = norm.normalize_route({'destination': '10.0.0.0/8', 'protocol': 'O'}, 'r1')
        assert r['protocol'] == 'OSPF'

    def test_proto_B_maps_to_BGP(self, norm):
        r = norm.normalize_route({'destination': '10.0.0.0/8', 'protocol': 'B'}, 'r1')
        assert r['protocol'] == 'BGP'

    def test_proto_D_maps_to_EIGRP(self, norm):
        r = norm.normalize_route({'destination': '10.0.0.0/8', 'protocol': 'D'}, 'r1')
        assert r['protocol'] == 'EIGRP'

    def test_proto_R_maps_to_RIP(self, norm):
        r = norm.normalize_route({'destination': '10.0.0.0/8', 'protocol': 'R'}, 'r1')
        assert r['protocol'] == 'RIP'

    def test_proto_i_maps_to_ISIS(self, norm):
        r = norm.normalize_route({'destination': '10.0.0.0/8', 'protocol': 'i'}, 'r1')
        assert r['protocol'] == 'ISIS'

    def test_proto_star_suffix_stripped(self, norm):
        r = norm.normalize_route({'destination': '0.0.0.0/0', 'protocol': 'S*',
                                   'next_hop': '10.0.0.1'}, 'r1')
        assert r is not None
        assert r['protocol'] == 'Static'

    def test_proto_Direct_maps_to_Connected(self, norm):
        r = norm.normalize_route({'destination': '10.0.0.0/8', 'protocol': 'Direct'}, 'r1')
        assert r is not None
        assert r['protocol'] == 'Connected'

    def test_proto_OSPF_fullname_preserved(self, norm):
        r = norm.normalize_route({'destination': '10.0.0.0/8', 'protocol': 'OSPF'}, 'r1')
        assert r['protocol'] == 'OSPF'

    def test_proto_BGP_fullname_preserved(self, norm):
        r = norm.normalize_route({'destination': '10.0.0.0/8', 'protocol': 'BGP'}, 'r1')
        assert r['protocol'] == 'BGP'

    def test_proto_IS_IS_maps_to_ISIS(self, norm):
        r = norm.normalize_route({'destination': '10.0.0.0/8', 'protocol': 'IS-IS'}, 'r1')
        assert r is not None
        assert r['protocol'] == 'ISIS'

    def test_proto_none_maps_to_Unknown(self, norm):
        r = norm.normalize_route({'destination': '10.0.0.0/8', 'protocol': None}, 'r1')
        assert r is not None
        assert r['protocol'] == 'Unknown'


# ---------------------------------------------------------------------------
# TestAdminDistanceAndMetric
# ---------------------------------------------------------------------------

class TestAdminDistanceAndMetric:

    def test_bracket_notation_ad_and_metric(self, norm):
        r = norm.normalize_route({'destination': '10.0.0.0/8',
                                   'protocol': 'O', 'metric': '[110/2]'}, 'r1')
        assert r is not None
        assert r['admin_distance'] == 110
        assert r['metric'] == 2

    def test_ad_field_explicit(self, norm):
        r = norm.normalize_route({'destination': '10.0.0.0/8', 'protocol': 'O',
                                   'admin_distance': '110', 'metric': '2'}, 'r1')
        assert r is not None
        assert r['admin_distance'] == 110

    def test_default_ad_connected(self, norm):
        r = norm.normalize_route({'destination': '10.0.0.0/8', 'protocol': 'C'}, 'r1')
        assert r['admin_distance'] == 0

    def test_default_ad_static(self, norm):
        r = norm.normalize_route({'destination': '10.0.0.0/8', 'protocol': 'S'}, 'r1')
        assert r['admin_distance'] == 1

    def test_default_ad_ospf(self, norm):
        r = norm.normalize_route({'destination': '10.0.0.0/8', 'protocol': 'O'}, 'r1')
        assert r['admin_distance'] == 110

    def test_default_ad_bgp(self, norm):
        r = norm.normalize_route({'destination': '10.0.0.0/8', 'protocol': 'B'}, 'r1')
        assert r['admin_distance'] == 200

    def test_default_ad_rip(self, norm):
        r = norm.normalize_route({'destination': '10.0.0.0/8', 'protocol': 'R'}, 'r1')
        assert r['admin_distance'] == 120

    def test_default_ad_eigrp(self, norm):
        r = norm.normalize_route({'destination': '10.0.0.0/8', 'protocol': 'D'}, 'r1')
        assert r['admin_distance'] == 90


# ---------------------------------------------------------------------------
# TestRouteType
# ---------------------------------------------------------------------------

class TestRouteType:

    def test_route_type_connected(self, norm):
        r = norm.normalize_route({'destination': '10.0.0.0/8', 'protocol': 'C'}, 'r1')
        assert r['route_type'] == 'Connected'

    def test_route_type_local(self, norm):
        r = norm.normalize_route({'destination': '10.0.0.1/32', 'protocol': 'L'}, 'r1')
        assert r['route_type'] == 'Connected'

    def test_route_type_static(self, norm):
        r = norm.normalize_route({'destination': '10.0.0.0/8', 'protocol': 'S'}, 'r1')
        assert r['route_type'] == 'Static'

    def test_route_type_dynamic_ospf(self, norm):
        r = norm.normalize_route({'destination': '10.0.0.0/8', 'protocol': 'O'}, 'r1')
        assert r['route_type'] == 'Dynamic'

    def test_route_type_dynamic_bgp(self, norm):
        r = norm.normalize_route({'destination': '10.0.0.0/8', 'protocol': 'B'}, 'r1')
        assert r['route_type'] == 'Dynamic'


# ---------------------------------------------------------------------------
# TestVRF
# ---------------------------------------------------------------------------

class TestVRF:

    def test_vrf_default_when_not_specified(self, norm):
        r = norm.normalize_route({'destination': '10.0.0.0/8'}, 'r1')
        assert r['vrf'] == 'default'

    def test_vrf_passed_to_normalize_route(self, norm):
        r = norm.normalize_route({'destination': '10.0.0.0/8'}, 'r1', vrf='PROD')
        assert r['vrf'] == 'PROD'

    def test_vrf_passed_to_normalize_table(self, norm):
        results = norm.normalize_routing_table(
            [{'destination': '10.0.0.0/8', 'protocol': 'C'}], 'r1', vrf='MGMT'
        )
        assert results[0]['vrf'] == 'MGMT'


# ---------------------------------------------------------------------------
# TestNormalizeRoutingTable
# ---------------------------------------------------------------------------

class TestNormalizeRoutingTable:

    def test_normalize_table_multiple_routes(self, norm):
        raw = [
            {'network': '192.168.1.0/24', 'protocol': 'C', 'metric': '0'},
            {'network': '10.0.0.0/8', 'protocol': 'S', 'metric': '[1/0]',
             'next_hop': '10.0.0.1'},
            {'network': '172.16.0.0/16', 'protocol': 'O', 'metric': '[110/2]',
             'next_hop': '10.0.0.2'},
        ]
        result = norm.normalize_routing_table(raw, 'r1')
        assert len(result) == 3
        assert all('destination' in r for r in result)
        assert all('device_id' in r for r in result)

    def test_normalize_table_empty(self, norm):
        assert norm.normalize_routing_table([], 'r1') == []

    def test_normalize_table_deduplication(self, norm):
        route = {'destination': '10.0.0.0/8', 'protocol': 'S', 'next_hop': '10.0.0.1'}
        result = norm.normalize_routing_table([route, route, route], 'r1')
        assert len(result) == 1

    def test_normalize_table_dedup_different_next_hops(self, norm):
        """ECMP routes (same dest, different next-hop) must ALL be kept."""
        raw = [
            {'destination': '10.0.0.0/8', 'protocol': 'O', 'next_hop': '10.0.0.1'},
            {'destination': '10.0.0.0/8', 'protocol': 'O', 'next_hop': '10.0.0.2'},
            {'destination': '10.0.0.0/8', 'protocol': 'O', 'next_hop': '10.0.0.3'},
        ]
        result = norm.normalize_routing_table(raw, 'r1')
        assert len(result) == 3

    def test_normalize_table_skips_multicast(self, norm):
        raw = [
            {'destination': '224.0.0.0/4', 'protocol': 'S'},
            {'destination': '10.0.0.0/8', 'protocol': 'C'},
        ]
        result = norm.normalize_routing_table(raw, 'r1')
        destinations = [r['destination'] for r in result]
        assert '224.0.0.0/4' not in destinations
        assert '10.0.0.0/8' in destinations

    def test_normalize_table_skips_empty_destination(self, norm):
        raw = [
            {'protocol': 'C'},  # no destination or network
            {'destination': '10.0.0.0/8', 'protocol': 'C'},
        ]
        result = norm.normalize_routing_table(raw, 'r1')
        assert len(result) == 1
        assert result[0]['destination'] == '10.0.0.0/8'

    def test_normalize_table_large_performance(self, norm):
        import time
        raw = [
            {'destination': f'10.{i // 256}.{i % 256}.0/24',
             'protocol': 'O', 'next_hop': '10.0.0.1'}
            for i in range(5000)
        ]
        t0 = time.time()
        result = norm.normalize_routing_table(raw, 'bigdev')
        assert len(result) == 5000
        assert time.time() - t0 < 30


# ---------------------------------------------------------------------------
# TestEdgeCases
# ---------------------------------------------------------------------------

class TestEdgeCases:

    def test_normalize_route_none_returns_none(self, norm):
        """normalize_route with no destination/network → None."""
        r = norm.normalize_route({}, 'r1')
        assert r is None

    def test_normalize_route_none_protocol(self, norm):
        r = norm.normalize_route({'destination': '10.0.0.0/8', 'protocol': None}, 'r1')
        assert r is not None
        assert r['protocol'] == 'Unknown'

    def test_normalize_route_invalid_ip_next_hop(self, norm):
        """Invalid next-hop IP should not crash — preserved as-is."""
        r = norm.normalize_route({'destination': '10.0.0.0/8', 'next_hop': 'not-an-ip'}, 'r1')
        assert r is not None
        assert r['next_hop'] == 'not-an-ip'

    def test_normalize_route_empty_next_hop(self, norm):
        r = norm.normalize_route({'destination': '10.0.0.0/8', 'next_hop': ''}, 'r1')
        assert r is not None
        assert r['next_hop'] == ''

    def test_normalize_route_multicast_returns_none(self, norm):
        r = norm.normalize_route({'destination': '224.0.0.0/4'}, 'r1')
        assert r is None

    def test_normalize_route_cidr_strict(self, norm):
        """Unusual CIDR input must not crash."""
        try:
            r = norm.normalize_route({'destination': '10.1.1.0/255.255.255.0'}, 'r1')
            # either None (failed parse) or a dict
        except Exception as exc:
            pytest.fail(f"normalize_route raised unexpectedly: {exc}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
