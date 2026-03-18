from flask import jsonify
from neo4j_service import neo4j_conn
from app.neo4j import bp


@bp.route('/knowledge-graph', methods=['GET'])
def get_knowledge_graph():
    """获取完整知识图谱（兼容前端一次性加载）"""
    try:
        nodes_query = "MATCH (n) RETURN n.node_id AS id, labels(n)[0] AS group, n"
        edges_query = "MATCH (s)-[r:RELATION]->(t) RETURN s.node_id AS from, t.node_id AS to, r"
        nodes_result = neo4j_conn.query(nodes_query)
        edges_result = neo4j_conn.query(edges_query)

        nodes = []
        for record in nodes_result:
            node_data = record['n']
            nodes.append({
                'id': record['id'],
                'group': record['group'].lower(),
                'label': node_data.get('label'),
                'title': node_data.get('title'),
                'description': node_data.get('description'),
                'year': node_data.get('year'),
                'color': node_data.get('color')
            })

        edges = []
        for record in edges_result:
            edge_data = record['r']
            edges.append({
                'from': record['from'],
                'to': record['to'],
                'label': edge_data.get('label'),
                'color': edge_data.get('color')
            })

        return jsonify({'nodes': nodes, 'edges': edges})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取知识图谱失败：{str(e)}'}), 500


@bp.route('/knowledge-graph/nodes', methods=['GET'])
def get_knowledge_graph_nodes():
    """获取知识图谱所有节点"""
    try:
        query = "MATCH (n) RETURN n.node_id AS id, labels(n)[0] AS group, n"
        result = neo4j_conn.query(query)
        
        nodes = []
        for record in result:
            node_data = record['n']
            node = {
                'id': record['id'],
                'group': record['group'].lower(),
                'label': node_data.get('label'),
                'title': node_data.get('title'),
                'description': node_data.get('description'),
                'year': node_data.get('year'),
                'color': node_data.get('color')
            }
            nodes.append(node)
        
        return jsonify(nodes)
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取知识图谱节点失败：{str(e)}'}), 500


@bp.route('/knowledge-graph/edges', methods=['GET'])
def get_knowledge_graph_edges():
    """获取知识图谱所有边"""
    try:
        query = "MATCH (s)-[r:RELATION]->(t) RETURN s.node_id AS from, t.node_id AS to, r"
        result = neo4j_conn.query(query)
        
        edges = []
        for record in result:
            edge_data = record['r']
            edge = {
                'from': record['from'],
                'to': record['to'],
                'label': edge_data.get('label'),
                'color': edge_data.get('color')
            }
            edges.append(edge)
        
        return jsonify(edges)
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取知识图谱边失败：{str(e)}'}), 500


@bp.route('/knowledge-graph/nodes/<int:node_id>', methods=['GET'])
def get_knowledge_graph_node(node_id):
    """获取指定ID的知识图谱节点"""
    try:
        query = "MATCH (n) WHERE n.node_id = $node_id RETURN n.node_id AS id, labels(n)[0] AS group, n"
        result = neo4j_conn.query(query, {'node_id': node_id})
        
        if not result:
            return jsonify({'success': False, 'message': '节点不存在'}), 404
        
        record = result[0]
        node_data = record['n']
        node = {
            'id': record['id'],
            'group': record['group'].lower(),
            'label': node_data.get('label'),
            'title': node_data.get('title'),
            'description': node_data.get('description'),
            'year': node_data.get('year'),
            'color': node_data.get('color')
        }
        
        return jsonify(node)
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取知识图谱节点失败：{str(e)}'}), 500


@bp.route('/knowledge-graph/query/<string:query_type>', methods=['GET'])
def query_knowledge_graph(query_type):
    """根据查询类型获取过滤后的知识图谱数据"""
    try:
        queries = {
            'all': {
                'nodes': "MATCH (n) RETURN n.node_id AS id, labels(n)[0] AS group, n",
                'edges': "MATCH (s)-[r:RELATION]->(t) RETURN s.node_id AS from, t.node_id AS to, r"
            },
            'programming': {
                'nodes': "MATCH (n:Language) RETURN n.node_id AS id, labels(n)[0] AS group, n",
                'edges': "MATCH (s)-[r:RELATION]->(t) WHERE 'Language' IN labels(s) OR 'Language' IN labels(t) RETURN s.node_id AS from, t.node_id AS to, r"
            },
            'databases': {
                'nodes': "MATCH (n:Database) RETURN n.node_id AS id, labels(n)[0] AS group, n",
                'edges': "MATCH (s)-[r:RELATION]->(t) WHERE 'Database' IN labels(s) OR 'Database' IN labels(t) RETURN s.node_id AS from, t.node_id AS to, r"
            },
            'ai': {
                'nodes': "MATCH (n:Concept) WHERE n.label CONTAINS '人工智能' OR n.label CONTAINS '机器学习' OR n.label CONTAINS '深度学习' RETURN n.node_id AS id, labels(n)[0] AS group, n",
                'edges': "MATCH (s)-[r:RELATION]->(t) WHERE ('Concept' IN labels(s) AND (s.label CONTAINS '人工智能' OR s.label CONTAINS '机器学习' OR s.label CONTAINS '深度学习')) OR ('Concept' IN labels(t) AND (t.label CONTAINS '人工智能' OR t.label CONTAINS '机器学习' OR t.label CONTAINS '深度学习')) RETURN s.node_id AS from, t.node_id AS to, r"
            },
            'developers': {
                'nodes': "MATCH (n:Person) RETURN n.node_id AS id, labels(n)[0] AS group, n",
                'edges': "MATCH (s)-[r:RELATION]->(t) WHERE 'Person' IN labels(s) OR 'Person' IN labels(t) RETURN s.node_id AS from, t.node_id AS to, r"
            }
        }
        
        if query_type not in queries:
            return jsonify({'success': False, 'message': '无效的查询类型'}), 400
        
        # 执行查询获取节点
        nodes_result = neo4j_conn.query(queries[query_type]['nodes'])
        
        nodes = []
        for record in nodes_result:
            node_data = record['n']
            node = {
                'id': record['id'],
                'group': record['group'].lower(),
                'label': node_data.get('label'),
                'title': node_data.get('title'),
                'description': node_data.get('description'),
                'year': node_data.get('year'),
                'color': node_data.get('color')
            }
            nodes.append(node)
        
        # 执行查询获取边
        edges_result = neo4j_conn.query(queries[query_type]['edges'])
        
        edges = []
        for record in edges_result:
            edge_data = record['r']
            edge = {
                'from': record['from'],
                'to': record['to'],
                'label': edge_data.get('label'),
                'color': edge_data.get('color')
            }
            edges.append(edge)
        
        return jsonify({'nodes': nodes, 'edges': edges})
    except Exception as e:
        return jsonify({'success': False, 'message': f'查询知识图谱失败：{str(e)}'}), 500
