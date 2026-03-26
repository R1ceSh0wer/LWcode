from flask import jsonify, request, current_app
from datetime import datetime
from .models import ExamColumn
from ..comments.models import Comment
from ..archives.models import ModelArchive
from ..users.models import db
from app.api_response import ok, fail
from neo4j_service import neo4j_conn
from utils import allowed_file, ocr_process, batch_ocr_process, save_uploaded_file, init_ocr_engine, extract_knowledge_from_ocr_text, process_question_images_for_knowledge, get_knowledge_model
import os
import json
import re
from . import bp


def _parse_knowledge_mapping_file(archive_mapping_path: str):
    """解析 knowledge_mapping.txt，返回 {编号: 知识点名称}"""
    result = {}
    if not archive_mapping_path:
        return result

    # 归一化到 backend 根目录，兼容 archives/xxx 与绝对路径两种写法
    if os.path.isabs(archive_mapping_path):
        full_path = archive_mapping_path
    else:
        backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        full_path = os.path.join(backend_dir, archive_mapping_path)

    if not os.path.exists(full_path):
        return result

    with open(full_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # 兼容 "1：xxx" / "1:xxx" / "1 xxx"
            match = re.match(r'^\s*(\d+)\s*[：: ]\s*(.+?)\s*$', line)
            if match:
                code = int(match.group(1))
                name = match.group(2).strip()
                if name:
                    result[code] = name
    return result


def _build_initial_graph_from_column(column: ExamColumn):
    """根据专栏题目知识点构建初始图谱（小球放在背包中）"""
    if not column or not column.question_knowledge:
        return [], [], []

    try:
        qk_data = json.loads(column.question_knowledge)
    except Exception:
        qk_data = {}

    if not isinstance(qk_data, dict):
        return [], [], []

    archive = ModelArchive.query.filter_by(id=column.archive_id).first() if column.archive_id else None
    mapping = _parse_knowledge_mapping_file(archive.knowledge_mapping_path if archive else '')

    weight_by_code = {}
    for _, codes in qk_data.items():
        if not isinstance(codes, list):
            continue
        for code in codes:
            try:
                code_int = int(code)
            except Exception:
                continue
            weight_by_code[code_int] = weight_by_code.get(code_int, 0) + 1

    nodes = []
    for code in sorted(weight_by_code.keys()):
        label = mapping.get(code, f'知识点{code}')
        nodes.append({
            'id': f'k_{code}',
            'code': code,
            'label': label,
            'weight': int(weight_by_code[code]),
            'x': None,
            'y': None,
            'inBackpack': True,
            'partitionTags': []
        })

    return nodes, [], []


def _save_column_graph_to_neo4j(column_id: int, teacher_id: int, nodes: list, edges: list):
    """保存知识图谱到 Neo4j（不再按专栏隔离）"""
    # 检查Neo4j连接是否可用
    if not neo4j_conn:
        return
    
    # 不再清理数据，而是更新或创建节点
    if nodes:
        for node in nodes:
            # 检查节点是否已存在
            existing_node = neo4j_conn.query(
                "MATCH (n:ColumnKnowledgeNode {node_id: $node_id}) RETURN n",
                {'node_id': node['id']}
            )
            
            if existing_node:
                # 获取现有节点的权重
                existing_weight = existing_node[0]['n'].get('weight', 1)
                new_weight = node.get('weight', 1)
                
                # 合并权重：取最大值
                merged_weight = max(existing_weight, new_weight)
                
                # 更新现有节点
                neo4j_conn.query(
                    """
                    MATCH (n:ColumnKnowledgeNode {node_id: $node_id})
                    SET n.code = $code,
                        n.label = $label,
                        n.weight = $weight,
                        n.x = $x,
                        n.y = $y,
                        n.in_backpack = $inBackpack,
                        n.partition_tags = $partitionTags,
                        n.teacher_id = $teacher_id
                    """,
                    {
                        'node_id': node['id'],
                        'code': node.get('code'),
                        'label': node.get('label'),
                        'weight': merged_weight,
                        'x': node.get('x'),
                        'y': node.get('y'),
                        'inBackpack': node.get('inBackpack', False),
                        'partitionTags': node.get('partitionTags', []),
                        'teacher_id': teacher_id
                    }
                )
            else:
                # 创建新节点
                neo4j_conn.query(
                    """
                    CREATE (n:ColumnKnowledgeNode {
                      node_id: $node_id,
                      code: $code,
                      label: $label,
                      weight: $weight,
                      x: $x,
                      y: $y,
                      in_backpack: $inBackpack,
                      partition_tags: $partitionTags,
                      teacher_id: $teacher_id
                    })
                    """,
                    {
                        'node_id': node['id'],
                        'code': node.get('code'),
                        'label': node.get('label'),
                        'weight': node.get('weight', 1),
                        'x': node.get('x'),
                        'y': node.get('y'),
                        'inBackpack': node.get('inBackpack', False),
                        'partitionTags': node.get('partitionTags', []),
                        'teacher_id': teacher_id
                    }
                )
    
    # 保存边
    if edges:
        for edge in edges:
            # 检查边是否已存在
            existing_edge = neo4j_conn.query(
                """
                MATCH (s:ColumnKnowledgeNode {node_id: $from_id})-[r:COLUMN_RELATION]->(t:ColumnKnowledgeNode {node_id: $to_id})
                RETURN r
                """,
                {'from_id': edge['from'], 'to_id': edge['to']}
            )
            
            if not existing_edge:
                # 创建新边
                neo4j_conn.query(
                    """
                    MATCH (s:ColumnKnowledgeNode {node_id: $from_id})
                    MATCH (t:ColumnKnowledgeNode {node_id: $to_id})
                    CREATE (s)-[r:COLUMN_RELATION {
                      edge_id: $edge_id,
                      label: $label,
                      teacher_id: $teacher_id
                    }]->(t)
                    """,
                    {
                        'from_id': edge['from'],
                        'to_id': edge['to'],
                        'edge_id': edge['id'],
                        'label': edge.get('label', '相关'),
                        'teacher_id': teacher_id
                    }
                )


def _load_column_graph_from_neo4j(column_id: int = None):
    """从Neo4j加载知识图谱数据（不再按专栏隔离）"""
    # 检查Neo4j连接是否可用
    if not neo4j_conn:
        print(f'[DEBUG] Neo4j连接不可用')
        return [], [], []
    
    # 加载所有知识图谱数据
    try:
        print(f'[DEBUG] 开始加载知识图谱数据')
        nodes_res = neo4j_conn.query(
            """
            MATCH (n:ColumnKnowledgeNode)
            RETURN n
            ORDER BY n.code ASC
            """
        )
        edges_res = neo4j_conn.query(
            """
            MATCH (s:ColumnKnowledgeNode)-[r:COLUMN_RELATION]->(t:ColumnKnowledgeNode)
            RETURN s.node_id AS from_id, t.node_id AS to_id, r
            """
        )
        # 加载分区数据
        print(f'[DEBUG] 开始加载分区数据')
        partitions_res = neo4j_conn.query(
            """
            MATCH (p:Partition)
            RETURN p
            ORDER BY p.name ASC
            """
        )
        print(f'[DEBUG] 分区数据加载完成，共 {len(partitions_res)} 个分区')
    except Exception as e:
        print(f'[Neo4j] 加载知识图谱数据失败: {str(e)}')
        import traceback
        traceback.print_exc()
        return [], [], []

    nodes = []
    node_ids = set()  # 用于去重
    for rec in nodes_res:
        n = rec['n']
        node_id = n.get('node_id')
        if node_id and node_id not in node_ids:
            node_ids.add(node_id)
            nodes.append({
                'id': node_id,
                'code': n.get('code'),
                'label': n.get('label'),
                'weight': int(n.get('weight') or 1),
                'x': n.get('x'),
                'y': n.get('y'),
                'inBackpack': bool(n.get('in_backpack')),
                'partitionTags': n.get('partition_tags') or []
            })

    edges = []
    for rec in edges_res:
        r = rec['r']
        edges.append({
            'id': r.get('edge_id'),
            'from': rec['from_id'],
            'to': rec['to_id'],
            'label': r.get('label') or '相关'
        })

    # 从分区数据和节点的partitionTags中提取分区
    partition_set = set()
    # 从分区数据中提取
    for rec in partitions_res:
        p = rec['p']
        partition_name = p.get('name')
        if partition_name:
            partition_set.add(partition_name)
            print(f'[DEBUG] 从分区数据中提取: {partition_name}')
    # 从节点的partitionTags中提取
    for n in nodes:
        for tag in (n.get('partitionTags') or []):
            if tag:
                partition_set.add(tag)
                print(f'[DEBUG] 从节点中提取分区: {tag}')
    partitions = sorted(list(partition_set))
    print(f'[DEBUG] 最终分区列表: {partitions}')
    return nodes, edges, partitions


def _ensure_teacher_graph(column: ExamColumn = None):
    """确保存在教师图谱数据（Neo4j）；若不存在则自动初始化"""
    column_id = column.id if column else None
    nodes, edges, partitions = _load_column_graph_from_neo4j(column_id)
    
    # 如果有专栏，总是将其知识点合并到现有图谱中
    if column:
        # 从当前专栏构建初始图谱
        init_nodes, init_edges, _ = _build_initial_graph_from_column(column)
        
        # 合并节点权重
        if init_nodes:
            # 加载现有节点
            existing_nodes = {n['id']: n for n in nodes}
            merged_nodes = []
            
            # 处理现有节点
            for node_id, node in existing_nodes.items():
                # 查找对应的初始节点
                init_node = next((n for n in init_nodes if n['id'] == node_id), None)
                if init_node:
                    # 合并权重：取最大值
                    node['weight'] = max(node['weight'], init_node['weight'])
                merged_nodes.append(node)
            
            # 添加新节点
            for init_node in init_nodes:
                if init_node['id'] not in existing_nodes:
                    merged_nodes.append(init_node)
            
            # 保存合并后的节点
            _save_column_graph_to_neo4j(column.id, column.teacher_id, merged_nodes, edges)
            return {'nodes': merged_nodes, 'edges': edges, 'partitions': partitions}
    
    # 如果没有数据且没有专栏，返回空数据
    if not nodes:
        # 从所有专栏构建初始图谱
        all_nodes = []
        all_edges = []
        all_columns = ExamColumn.query.all()
        
        for col in all_columns:
            init_nodes, init_edges, _ = _build_initial_graph_from_column(col)
            all_nodes.extend(init_nodes)
            all_edges.extend(init_edges)
        
        # 去重节点
        unique_nodes = []
        node_ids = set()
        for node in all_nodes:
            if node['id'] and node['id'] not in node_ids:
                node_ids.add(node['id'])
                unique_nodes.append(node)
        
        # 保存合并后的节点
        if unique_nodes and all_columns:
            # 使用第一个专栏的教师ID
            teacher_id = all_columns[0].teacher_id
            _save_column_graph_to_neo4j(all_columns[0].id, teacher_id, unique_nodes, all_edges)
            # 即使没有节点，也应该加载分区数据
            _, _, partitions = _load_column_graph_from_neo4j()
            return {'nodes': unique_nodes, 'edges': all_edges, 'partitions': partitions}
        
        # 如果没有数据且没有专栏，返回空数据
        return {'nodes': [], 'edges': [], 'partitions': []}
    
    # 如果有数据，直接返回
    return {'nodes': nodes, 'edges': edges, 'partitions': partitions}


@bp.route('/columns', methods=['GET'])
def get_columns():
    try:
        columns = ExamColumn.query.all()
        
        result = []
        for column in columns:
            result.append({
                'id': str(column.id),
                'name': column.title,
                'description': column.question_text or '',
                'archiveId': column.archive_id,
                'created': column.created_at.strftime('%Y-%m-%d'),
                'teacherId': str(column.teacher_id),
                'humanKnowledgePath': column.human_knowledge or ''
            })
        
        return ok(result)
    except Exception as e:
        return fail(f'获取专栏列表失败：{str(e)}', 500)


@bp.route('/columns/<int:id>', methods=['GET'])
def get_column(id: int):
    try:
        column = ExamColumn.query.filter_by(id=id).first()
        
        if column:
            return ok({
                'id': str(column.id),
                'name': column.title,
                'description': column.question_text or '',
                'archiveId': column.archive_id,
                'created': column.created_at.strftime('%Y-%m-%d'),
                'questionImagePath1': column.question_image_path1 or '',
                'questionImagePath2': column.question_image_path2 or '',
                'questionImagePath3': column.question_image_path3 or '',
                'questionImagePath4': column.question_image_path4 or '',
                'questionImagePath5': column.question_image_path5 or '',
                'questionImagePath6': column.question_image_path6 or '',
                'teacherId': str(column.teacher_id)
            })
        return fail('专栏不存在', 404)
    except Exception as e:
        return fail(f'获取专栏信息失败：{str(e)}', 500)


@bp.route('/columns', methods=['POST'])
def create_column():
    try:
        title = request.form.get('name')
        teacher_id = request.form.get('teacherId', 1)
        archive_id = request.form.get('archiveId', type=int)
        
        new_column = ExamColumn(
            teacher_id=teacher_id,
            title=title,
            question_text="",
            archive_id=archive_id
        )
        # 处理人工标注知识点文件上传
        human_knowledge_file = request.files.get('human_knowledge_file')
        human_knowledge_path = None
        if human_knowledge_file:
            # 该字段只允许 txt；这里不要复用 allowed_file（它依赖 ALLOWED_EXTENSIONS）
            if not human_knowledge_file.filename.lower().endswith('.txt'):
                db.session.rollback()
                return fail('只允许上传 TXT 格式的知识点标注文件', 400)
            file_path, filename = save_uploaded_file(human_knowledge_file, allowed_exts={'txt'})
            if file_path:
                human_knowledge_path = f'uploads/{filename}'
                new_column.human_knowledge = human_knowledge_path
            else:
                db.session.rollback()
                return fail('保存知识点标注文件失败', 500)
        
        db.session.add(new_column)
        db.session.commit()
        
        question_image_paths = [None] * 6
        file_paths = []
        
        for i in range(1, 7):
            file_key = f'image{i}'
            if file_key in request.files:
                file = request.files[file_key]
                if file and allowed_file(file.filename):
                    file_path, filename = save_uploaded_file(file)
                    if file_path:
                        relative_path = f'uploads/{filename}'
                        setattr(new_column, f'question_image_path{i}', relative_path)
                        question_image_paths[i-1] = file_path
                        file_paths.append(file_path)
        
        question_texts_dict = {}
        question_knowledge_dict = {}
        
        if file_paths:
            print(f'[OCR] 开始并行处理 {len(file_paths)} 张图片')
            ocr_results = batch_ocr_process(file_paths, quality_mode='light', max_workers=2)
            
            for i, (image_path, ocr_result) in enumerate(zip(question_image_paths, ocr_results)):
                if image_path and ocr_result:
                    question_texts_dict[f"img_{i+1}"] = ocr_result
            
            try:
                print(f'[Knowledge] 开始从OCR文本提取题目和预测知识点')
                
                # 获取知识点模型
                print(f'[DEBUG] 获取知识点模型...')
                knowledge_model = get_knowledge_model()
                print(f'[DEBUG] 知识点模型获取结果: {knowledge_model is not None}')
                
                if knowledge_model:
                    # 初始化OCR引擎
                    ocr_engine = init_ocr_engine()
                    
                    # 使用 process_question_images_for_knowledge 处理分页题目
                    all_questions, all_knowledge = process_question_images_for_knowledge(file_paths, ocr_engine, knowledge_model)
                    
                    question_texts_dict = {str(k): v for k, v in all_questions.items()}
                    question_knowledge_dict = {str(k): v for k, v in all_knowledge.items()}
                    print(f'[Knowledge] 识别到 {len(question_texts_dict)} 道题目，{len(question_knowledge_dict)} 道题目的知识点')
                else:
                    print(f'[ERROR] 知识点模型初始化失败')
            except Exception as e:
                print(f'[WARN] 知识点预测失败: {str(e)}')
                import traceback
                traceback.print_exc()
        
        # 解析人工标注知识点文件并与模型预测知识点结合
        if human_knowledge_path:
            try:
                import json
                import re
                
                # 解析人工标注知识点文件
                def parse_human_knowledge_file(file_path):
                    if not file_path or not os.path.exists(file_path):
                        return None
                    
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                    
                    if not content:
                        return None
                    
                    # 尝试 JSON 解析
                    try:
                        normalized = (
                            content.replace('“', '"')
                            .replace('”', '"')
                            .replace("‘", "'")
                            .replace("’", "'")
                        )
                        data = json.loads(normalized)
                        if isinstance(data, dict):
                            parsed_data = {}
                            for key, value in data.items():
                                key_str = str(key).strip()
                                if isinstance(value, list):
                                    nums = []
                                    for x in value:
                                        if isinstance(x, (int, float)):
                                            nums.append(int(x))
                                        else:
                                            x_str = str(x).strip()
                                            if re.fullmatch(r'-?\d+', x_str):
                                                nums.append(int(x_str))
                                    if nums:
                                        parsed_data[key_str] = nums
                                else:
                                    # 允许 value 直接为单个数字
                                    value_str = str(value).strip()
                                    if re.fullmatch(r'-?\d+', value_str):
                                        parsed_data[key_str] = [int(value_str)]
                                    # 允许 value 为逗号/分号分隔的数字字符串
                                    else:
                                        parts = re.split(r'[,；;]', value_str)
                                        nums = []
                                        for p in parts:
                                            p_stripped = p.strip()
                                            if re.fullmatch(r'-?\d+', p_stripped):
                                                nums.append(int(p_stripped))
                                        if nums:
                                            parsed_data[key_str] = nums
                            return parsed_data
                    except Exception:
                        pass
                    
                    # 尝试键值对文本解析
                    try:
                        lines = content.split('\n')
                        parsed_data = {}
                        for line in lines:
                            line = line.strip()
                            if not line or ':' not in line:
                                continue
                            key_part, value_part = line.split(':', 1)
                            key_str = key_part.strip()
                            value_str = value_part.strip()
                            
                            # 处理值：可能是单个数字或逗号/分号分隔的数字
                            parts = re.split(r'[,；;]', value_str)
                            nums = []
                            for p in parts:
                                p_stripped = p.strip()
                                if re.fullmatch(r'-?\d+', p_stripped):
                                    nums.append(int(p_stripped))
                            if nums:
                                parsed_data[key_str] = nums
                        if parsed_data:
                            return parsed_data
                    except Exception:
                        pass
                    
                    return None
                
                # 解析人工标注知识点
                human_knowledge_full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], os.path.basename(human_knowledge_path))
                human_knowledge_data = parse_human_knowledge_file(human_knowledge_full_path)
                
                if human_knowledge_data:
                    print(f'[INFO] 成功加载并解析人工标注知识点文件')
                    print(f'[DEBUG] 人工标注知识点: {human_knowledge_data}')
                    
                    # 结合人工标注知识点与模型预测知识点
                    for q_key, base_codes in question_knowledge_dict.items():
                        # 获取人工标注的知识点
                        human_codes = human_knowledge_data.get(q_key, [])
                        
                        # 按要求：人工标注“追加”到模型预测之后，并保留序列顺序（去重但不打乱）
                        merged_codes = []
                        seen = set()
                        for c in list(base_codes) + list(human_codes):
                            try:
                                c_int = int(c)
                            except Exception:
                                continue
                            if c_int not in seen:
                                seen.add(c_int)
                                merged_codes.append(c_int)
                        
                        if merged_codes:
                            question_knowledge_dict[q_key] = merged_codes
                    
                    print(f'[INFO] 成功结合人工标注知识点与模型预测知识点')
                else:
                    print(f'[WARN] 人工标注知识点文件解析失败或为空')
            except Exception as e:
                print(f'[ERROR] 处理人工标注知识点失败: {str(e)}')
                import traceback
                traceback.print_exc()
        
        new_column.question_text = json.dumps(question_texts_dict, ensure_ascii=False) if question_texts_dict else "{}"
        new_column.question_knowledge = json.dumps(question_knowledge_dict, ensure_ascii=False) if question_knowledge_dict else "{}"
        
        db.session.commit()

        # 创建专栏后，自动按题目知识点初始化教师知识图谱（小球 + 权重）
        _ensure_teacher_graph(new_column)
        
        return ok({
            'id': str(new_column.id),
            'name': new_column.title,
            'description': new_column.question_text,
            'questionKnowledge': new_column.question_knowledge,
            'archiveId': new_column.archive_id,
            'created': new_column.created_at.strftime('%Y-%m-%d'),
            'teacherId': str(new_column.teacher_id)
        }, status_code=201)
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return fail(f'创建专栏失败：{str(e)}', 500)


@bp.route('/columns/<int:id>/knowledge-graph', methods=['GET'])
def get_column_knowledge_graph(id: int):
    """获取教师端专栏知识图谱构建数据（不存在则按题目自动初始化）"""
    try:
        column = ExamColumn.query.filter_by(id=id).first()
        if not column:
            return fail('专栏不存在', 404)

        graph = _ensure_teacher_graph(column)
        nodes = graph.get('nodes', [])
        edges = graph.get('edges', [])
        partitions = graph.get('partitions', [])

        return ok({
            'columnId': str(column.id),
            'nodes': nodes,
            'edges': edges,
            'partitions': partitions
        })
    except Exception as e:
        return fail(f'获取专栏知识图谱失败：{str(e)}', 500)


@bp.route('/columns/<int:id>/knowledge-graph', methods=['PUT'])
def save_column_knowledge_graph(id: int):
    """保存教师端专栏知识图谱构建数据"""
    data = request.get_json() or {}
    try:
        column = ExamColumn.query.filter_by(id=id).first()
        if not column:
            return fail('专栏不存在', 404)

        nodes = data.get('nodes', [])
        edges = data.get('edges', [])
        partitions = data.get('partitions', [])

        print(f'[DEBUG] 接收到的分区数据: {partitions}')

        if not isinstance(nodes, list) or not isinstance(edges, list) or not isinstance(partitions, list):
            return fail('图谱数据格式错误', 400)

        # 保存分区数据到 Neo4j
        if partitions and neo4j_conn:
            try:
                print(f'[DEBUG] 开始保存分区数据到 Neo4j')
                # 清除旧的分区数据
                neo4j_conn.query(
                    """
                    MATCH (p:Partition)
                    DETACH DELETE p
                    """
                )
                print(f'[DEBUG] 旧的分区数据已清除')
                
                # 保存新的分区数据
                for partition in partitions:
                    if isinstance(partition, str) and partition.strip():
                        print(f'[DEBUG] 保存分区: {partition.strip()}')
                        neo4j_conn.query(
                            """
                            CREATE (p:Partition {name: $name})
                            """,
                            {'name': partition.strip()}
                        )
                print(f'[DEBUG] 分区数据保存完成')
            except Exception as e:
                print(f'[Neo4j] 保存分区数据失败: {str(e)}')
                import traceback
                traceback.print_exc()

        _save_column_graph_to_neo4j(column.id, column.teacher_id, nodes, edges)
        return ok(message='知识图谱保存成功')
    except Exception as e:
        db.session.rollback()
        print(f'[ERROR] 保存知识图谱失败: {str(e)}')
        import traceback
        traceback.print_exc()
        return fail(f'保存专栏知识图谱失败：{str(e)}', 500)


@bp.route('/columns/knowledge-graph/latest', methods=['GET'])
def get_latest_teacher_knowledge_graph():
    """给学生端使用：获取最新专栏的教师构建知识图谱"""
    try:
        latest_column = ExamColumn.query.order_by(ExamColumn.created_at.desc()).first()
        if not latest_column:
            return ok(None, message='暂无专栏')

        graph = _ensure_teacher_graph(latest_column)
        nodes = graph.get('nodes', [])
        edges = graph.get('edges', [])
        partitions = graph.get('partitions', [])

        return ok({
            'columnId': str(latest_column.id),
            'nodes': nodes,
            'edges': edges,
            'partitions': partitions
        })
    except Exception as e:
        return fail(f'获取最新教师知识图谱失败：{str(e)}', 500)


@bp.route('/columns/<int:id>', methods=['PUT'])
def update_column(id: int):
    data = request.get_json()
    try:
        column = ExamColumn.query.filter_by(id=id).first()
        if not column:
            return fail('专栏不存在', 404)
        
        column.title = data.get('name', column.title)
        column.question_text = data.get('description', column.question_text)
        column.archive_id = data.get('archiveId', column.archive_id)
        db.session.commit()
        
        return ok({
            'id': str(column.id),
            'name': column.title,
            'description': column.question_text,
            'archiveId': column.archive_id,
            'created': column.created_at.strftime('%Y-%m-%d'),
            'teacherId': str(column.teacher_id)
        })
    except Exception as e:
        db.session.rollback()
        return fail(f'更新专栏失败：{str(e)}', 500)


@bp.route('/columns/<int:id>', methods=['DELETE'])
def delete_column(id: int):
    try:
        column = ExamColumn.query.filter_by(id=id).first()
        if not column:
            return fail('专栏不存在', 404)
        
        # 提取专栏的知识点，用于后续减少权重
        column_knowledge = {}
        if column.question_knowledge:
            try:
                import json
                qk_data = json.loads(column.question_knowledge)
                if isinstance(qk_data, dict):
                    for _, codes in qk_data.items():
                        if isinstance(codes, list):
                            for code in codes:
                                try:
                                    code_int = int(code)
                                    column_knowledge[code_int] = column_knowledge.get(code_int, 0) + 1
                                except Exception:
                                    continue
            except Exception:
                pass
        
        image_paths = [
            column.question_image_path1,
            column.question_image_path2,
            column.question_image_path3,
            column.question_image_path4,
            column.question_image_path5,
            column.question_image_path6
        ]
        
        for image_path in image_paths:
            if image_path:
                full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], os.path.basename(image_path))
                try:
                    if os.path.exists(full_path):
                        os.remove(full_path)
                        print(f'[DELETE] 删除图片文件: {full_path}')
                except Exception as e:
                    print(f'[DELETE] 删除图片文件失败 {full_path}: {str(e)}')
        
        comments = Comment.query.filter_by(column_id=id).all()
        for comment in comments:
            comment_image_paths = [
                comment.answer_image_path1,
                comment.answer_image_path2,
                comment.answer_image_path3,
                comment.answer_image_path4,
                comment.answer_image_path5,
                comment.answer_image_path6
            ]
            
            for image_path in comment_image_paths:
                if image_path:
                    full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], os.path.basename(image_path))
                    try:
                        if os.path.exists(full_path):
                            os.remove(full_path)
                            print(f'[DELETE] 删除评语图片文件: {full_path}')
                    except Exception as e:
                        print(f'[DELETE] 删除评语图片文件失败 {full_path}: {str(e)}')
        
        Comment.query.filter_by(column_id=id).delete()
        
        db.session.delete(column)
        db.session.commit()
        
        # 减少知识图谱中对应知识点的权重
        if column_knowledge and neo4j_conn:
            try:
                # 加载所有知识图谱数据
                nodes_res = neo4j_conn.query(
                    """
                    MATCH (n:ColumnKnowledgeNode)
                    RETURN n
                    """
                )
                
                # 处理每个节点
                for rec in nodes_res:
                    n = rec['n']
                    node_id = n.get('node_id')
                    code = n.get('code')
                    
                    # 检查该节点是否在当前专栏的知识点中
                    if code and code in column_knowledge:
                        # 获取当前权重
                        current_weight = n.get('weight', 1)
                        # 计算新权重
                        new_weight = max(0, current_weight - column_knowledge[code])
                        
                        if new_weight > 0:
                            # 更新权重
                            neo4j_conn.query(
                                """
                                MATCH (n:ColumnKnowledgeNode {node_id: $node_id})
                                SET n.weight = $weight
                                """,
                                {'node_id': node_id, 'weight': new_weight}
                            )
                        else:
                            # 权重为0，删除节点
                            neo4j_conn.query(
                                """
                                MATCH (n:ColumnKnowledgeNode {node_id: $node_id})
                                DETACH DELETE n
                                """,
                                {'node_id': node_id}
                            )
                
                print(f'[DELETE] 已更新知识图谱中知识点的权重')
            except Exception as e:
                print(f'[DELETE] 更新知识图谱失败: {str(e)}')
        
        return ok(None, message='专栏已删除')
    except Exception as e:
        db.session.rollback()
        return fail(f'删除专栏失败：{str(e)}', 500)
