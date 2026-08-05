"""
Stakeholder impact network: builds a graph connecting stakeholders to
policy scenarios and to each other via user-supplied relationships (e.g.
"depends on", "affects"). Real graph algorithms (NetworkX) on user-supplied
edges — no fabricated stakeholder discovery.
"""
import networkx as nx


def build_stakeholder_graph(edges: list) -> nx.Graph:
    G = nx.Graph()
    for e in edges:
        G.add_edge(e["source"], e["target"], relationship=e.get("relationship", ""))
    return G


def graph_summary(G: nx.Graph) -> dict:
    if G.number_of_nodes() == 0:
        return {"n_nodes": 0, "n_edges": 0, "top_entities": []}
    centrality = nx.degree_centrality(G)
    top = sorted(centrality.items(), key=lambda kv: kv[1], reverse=True)[:15]
    return {
        "n_nodes": G.number_of_nodes(), "n_edges": G.number_of_edges(),
        "density": round(nx.density(G), 4),
        "top_entities": [{"entity": e, "centrality": round(c, 4)} for e, c in top],
    }
