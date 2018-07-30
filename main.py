"""Request handler for Cloud Functions."""

import logging
from flask import jsonify
from oss_graph import get_review_list, list_to_graph_node_link

def get_graph(request):
    c = request.json
    logging.info("Querying GitHub GraphQL endpoint")
    prs = get_review_list(c['token'], c['owner'], c['name'])
    logging.info("Got {} PRs".format(len(prs)))
    H = list_to_graph_node_link(prs)
    return jsonify(H)
