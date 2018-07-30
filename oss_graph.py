"""Get OSS social network information from GitHub."""

from io import BytesIO
import requests
import logging
import base64
import networkx as nx
#import matplotlib.pyplot as plt

# Prototype queries in https://developer.github.com/v4/explorer/.
GRAPHQL_QUERY = """
query ($pr_cursor: String, $owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    pullRequests(first: 100, after: $pr_cursor, orderBy: {field: CREATED_AT, direction: ASC}) {
      edges {
        cursor
        node {
          author {
            login
          }
          reviews(last: 100) {
            edges {
              node {
                author {
                  login
                }
              }
            }
          }
        }
      }
      totalCount
      pageInfo {
        hasNextPage
      }
    }
  }
}
"""

def get_review_list(token, owner, name):
    headers = {"Authorization": "Bearer {}".format(token),
        "Content-Type": "application/json"}
    results, pr_cursor = [], None
    while True:
        r = requests.post('https://api.github.com/graphql', json={
                "query": GRAPHQL_QUERY,
                "variables": {
                    "owner": owner,
                    "name": name,
                    "pr_cursor": pr_cursor
                }}, headers=headers)
        r.raise_for_status()
        obj = r.json()
        results.extend(obj['data']['repository']['pullRequests']['edges'])
        if obj['data']['repository']['pullRequests']['pageInfo']['hasNextPage']:
            pr_cursor = obj['data']['repository']['pullRequests']['edges'][-1]['cursor']
        else:
            break
    
    return results


def list_to_graph_node_link(prs):
    G = nx.Graph()
    for p in prs:
        try:
            author = p['node']['author']['login']
            if author not in G.nodes:
                G.add_node(author)
            for rev in p['node']['reviews']['edges']:
                reviewer = rev['node']['author']['login']
                if reviewer not in G.adj[author]:
                    G.add_edge(author, reviewer, weight=1)
                else:
                    G[author][reviewer]['weight'] += 1
        except Exception:
            logging.info("Could not interpret PR {}".format(str(p)))
            pass

    # Invert weights
    H = nx.Graph()
    for n, nbrs in G.adj.items():
        H.add_node(n)
        for nbr, eattr in nbrs.items():
            wt = eattr['weight']
            H.add_edge(n, nbr, weight=(1.0/wt))
    
    return nx.node_link_data(H)

def get_centrality(H):
    # Returns a list of (name, centrality) tuples
    return nx.eigenvector_centrality(H, weight='weight')

#def get_base64_image(H):
#    figfile = BytesIO()
#    _, ax = plt.subplots(figsize=(24,24))
#    nx.draw(H, with_labels=True, pos=nx.spring_layout(H), ax=ax)
#    plt.savefig(figfile, format='png')
#    figfile.seek(0)  # rewind to beginning of file
#    figdata_png = base64.b64encode(figfile.getvalue())
#    return figdata_png
