"""STP topology HTML via unified topo_map_shell (v7.0.0)."""
from utils.topo_map_shell import (
    default_grid_positions,
    link_rows_from_edges,
    render_topology_page,
)


def generate_stp_html(filepath, nodes, edges, link_rows=None, *, vlan_id=0, subtitle='', demo_mode=False):
    """Write STP scan report HTML with Link Inventory + static map."""
    if link_rows is None:
        link_rows = link_rows_from_edges(edges, nodes)
    positions = default_grid_positions(nodes, edges)
    nodes_out = []
    for n in nodes:
        nd = dict(n)
        nid = nd.get('id', '')
        if nid in positions:
            nd.update(positions[nid])
        if nd.get('is_root'):
            nd.setdefault('color', {'background': '#22c55e', 'border': '#16a34a'})
        nodes_out.append(nd)
    mode = 'DEMO / synthetic data' if demo_mode else 'LIVE inventory scan'
    sub = subtitle or f'STP scan · {mode} · VLAN filter: {vlan_id or "all"} · {len(nodes)} device(s)'
    render_topology_page(
        filepath,
        'STP Topology Scan',
        nodes_out,
        edges,
        link_rows,
        subtitle=sub,
        accent='#10b981',
        links_default=True,
    )
    return filepath
