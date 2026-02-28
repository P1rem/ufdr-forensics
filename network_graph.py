"""network_graph.py — Generates communication network as base64 PNG."""
import io, base64
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

def generate_network_graph(metrics: dict) -> str:
    edges = metrics.get("network_edges", [])
    if not edges:
        return ""
    try:
        import networkx as nx
        G = nx.Graph()
        G.add_node("Subject", w=1000, subj=True)
        for e in edges:
            G.add_node(e["target"], w=e["weight"], subj=False)
            G.add_edge("Subject", e["target"], weight=e["weight"])

        pos = nx.spring_layout(G, seed=42, k=2.5)
        pos["Subject"] = (0, 0)

        max_w = max(d["w"] for _,d in G.nodes(data=True))
        sizes, colors = [], []
        for node in G.nodes():
            d = G.nodes[node]
            if d.get("subj"):
                sizes.append(3000); colors.append("#00d9ff")
            else:
                w = d.get("w", 0)
                sizes.append(800 + (w/max_w)*2500)
                if w == max(e2["weight"] for e2 in edges):
                    colors.append("#ff4757")
                elif "unknown" in node.lower():
                    colors.append("#ffa502")
                else:
                    colors.append("#2ed573")

        max_ew = max(d["weight"] for _,_,d in G.edges(data=True))
        ewidths = [1+(d["weight"]/max_ew)*8 for _,_,d in G.edges(data=True)]

        fig, ax = plt.subplots(figsize=(10,8))
        fig.patch.set_facecolor("#0a0e27"); ax.set_facecolor("#0a0e27")
        nx.draw_networkx_edges(G, pos, edge_color="#00d9ff", alpha=0.4, width=ewidths, ax=ax)
        nx.draw_networkx_nodes(G, pos, node_size=sizes, node_color=colors, alpha=0.9, ax=ax)
        nx.draw_networkx_labels(G, pos, font_color="white", font_size=9, font_weight="bold", ax=ax)
        edge_labels = {(e["source"],e["target"]):str(e["weight"]) for e in edges}
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color="#ccd6f6", font_size=7, ax=ax)

        legend = [mpatches.Patch(color="#00d9ff",label="Subject"),
                  mpatches.Patch(color="#ff4757",label="Primary Contact"),
                  mpatches.Patch(color="#ffa502",label="Unknown"),
                  mpatches.Patch(color="#2ed573",label="Others")]
        ax.legend(handles=legend, loc="lower right", facecolor="#111936",
                  labelcolor="white", edgecolor="#00d9ff", fontsize=8)
        ax.set_title("Communication Network", color="#00d9ff", fontsize=14, fontweight="bold")
        ax.axis("off"); plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=120, bbox_inches="tight", facecolor="#0a0e27")
        plt.close()
        buf.seek(0)
        return base64.b64encode(buf.read()).decode()
    except Exception as e:
        print(f"[Graph] Error: {e}")
        return ""
