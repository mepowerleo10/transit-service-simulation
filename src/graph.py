from pathlib import Path
import networkx as nx
import matplotlib.pyplot as plt


def draw(nodes_df, output_path: Path):
    G = nx.DiGraph()
    edges = list(zip(nodes_df["NODES"], nodes_df["NEXT_NODES"]))

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
        "connectionstyle": "arc3,rad=0.2",
        "arrowstyle": "-|>",
        "arrowsize": 20,
    }

    plt.figure(figsize=[10, 5])

    nx.draw(
        G,
        pos,
        nodelist=nodes_df["NODES"].tolist(),
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
