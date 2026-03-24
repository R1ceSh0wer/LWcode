from neo4j import GraphDatabase
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD


class Neo4jConnection:
    """Neo4j数据库连接管理器"""
    
    def __init__(self):
        """初始化Neo4j连接"""
        self.driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD)
        )
    
    def close(self):
        """关闭Neo4j连接"""
        if self.driver:
            self.driver.close()
    
    def query(self, query, parameters=None):
        """执行Cypher查询并返回结果"""
        with self.driver.session() as session:
            result = session.run(query, parameters)
            return list(result)
    
    def create_node(self, label, properties):
        """创建一个节点"""
        query = f"CREATE (n:{label} $properties) RETURN n"
        return self.query(query, {"properties": properties})
    
    def find_nodes(self, label, properties=None):
        """根据标签和属性查找节点"""
        if properties:
            props_str = " AND ".join([f"n.{k} = ${k}" for k in properties.keys()])
            query = f"MATCH (n:{label}) WHERE {props_str} RETURN n"
            return self.query(query, properties)
        else:
            query = f"MATCH (n:{label}) RETURN n"
            return self.query(query)
    
    def create_relationship(self, start_label, start_props, rel_type, end_label, end_props, rel_props=None):
        """创建两个节点之间的关系"""
        start_props_str = " AND ".join([f"s.{k} = ${k}1" for k in start_props.keys()])
        end_props_str = " AND ".join([f"e.{k} = ${k}2" for k in end_props.keys()])
        
        query = f"""
        MATCH (s:{start_label}) WHERE {start_props_str}
        MATCH (e:{end_label}) WHERE {end_props_str}
        CREATE (s)-[r:{rel_type} {{
            {', '.join([f'{k}: ${k}r' for k in (rel_props or {}).keys()])}
        }}]->(e)
        RETURN r
        """
        
        params = {}
        for k, v in start_props.items():
            params[f"{k}1"] = v
        for k, v in end_props.items():
            params[f"{k}2"] = v
        if rel_props:
            for k, v in rel_props.items():
                params[f"{k}r"] = v
        
        return self.query(query, params)
    
    def update_node(self, label, property_name, property_value, update_properties):
        """更新节点属性"""
        if not update_properties:
            return []
        
        set_clause = ", ".join([f"n.{k} = ${k}" for k in update_properties.keys()])
        query = f"MATCH (n:{label}) WHERE n.{property_name} = $property_value SET {set_clause} RETURN n"
        
        params = {"property_value": property_value}
        params.update(update_properties)
        
        return self.query(query, params)


# 创建全局Neo4j连接实例
neo4j_conn = None

try:
    neo4j_conn = Neo4jConnection()
    print(f'[Neo4j] 连接成功: {NEO4J_URI}')
except Exception as e:
    print(f'[Neo4j] 连接失败: {str(e)}')
    print(f'[Neo4j] 请确保Neo4j数据库正在运行，地址: {NEO4J_URI}')
    neo4j_conn = None
