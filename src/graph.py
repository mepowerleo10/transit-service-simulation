from pathlib import Path
import traceback
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt


def draw(nodes_df: pd.DataFrame, output_path: Path):
    try:
        nodes_with_next_df =  nodes_df[nodes_df.notna().all(axis=1)]
        G = nx.DiGraph()
        edges = list(zip(nodes_with_next_df["NODES"], nodes_with_next_df["NEXT_NODES"]))

        G.add_nodes_from(nodes_df["NODES"])
        G.add_edges_from(edges)

        # Generate the spring layout
        pos = nodes_df["POSITIONS"]
        # pos = nx.spring_layout(G, k=0.1, pos=dict(zip(nodes_df["NODES"], pos)), iterations=1)

        options = {
            "edge_color": "gray",
            "font_size": 12,
            "font_color": "black",
            "with_labels": True,
            "connectionstyle": "arc3,rad=0.3",
            "arrowstyle": "-|>",
            "arrowsize": 20,
        }

        plt.figure(figsize=[20, 10])

        nx.draw(
            G,
            pos,
            nodelist=nodes_df["NODES"].to_list(),
            node_color=nodes_df["COLORS"],
            node_shape="o",
            node_size=nodes_df["SIZES"],
            **options,
        )

        ax = plt.gca()
        ax.set_axis_on()
        ax.tick_params(left=True, bottom=True, labelleft=True, labelbottom=True)
        plt.grid(True)

        # Save the plot
        image_output_path = output_path / "graph.png"
        print(f"Saving the graph in {image_output_path.as_posix()}")
        plt.savefig(
            image_output_path,
            format="png",
            bbox_inches="tight",
            pad_inches=0.1,
        )

        gml_output_path = output_path / "graph.gml"
        print(f"Saving the GML for graph in {gml_output_path}")
        nx.write_gml(G, gml_output_path)
    except Exception:
        traceback.print_exc()
