"""Gephi Graph Streaming client - sends node/edge updates via HTTP."""

import requests


class GephiClient:
    def __init__(self, host="localhost", port=8080, workspace="workspace1"):
        self.base_url = f"http://{host}:{port}/{workspace}"

    def update_node(self, node_id, **attrs):
        payload = {"an": {node_id: attrs}}
        try:
            requests.post(f"{self.base_url}?operation=updateGraph", json=payload, timeout=0.5)
        except requests.RequestException:
            pass

    def update_edge(self, edge_id, source, target, **attrs):
        payload = {"ae": {edge_id: {"source": source, "target": target, **attrs}}}
        try:
            requests.post(f"{self.base_url}?operation=updateGraph", json=payload, timeout=0.5)
        except requests.RequestException:
            pass

    def delete_node(self, node_id):
        payload = {"dn": {node_id: {}}}
        try:
            requests.post(f"{self.base_url}?operation=updateGraph", json=payload, timeout=0.5)
        except requests.RequestException:
            pass
