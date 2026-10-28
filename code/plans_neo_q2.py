"""plans_neo_q2.py - EXPLAIN (plan without running) for Neo4j Q2, since PROFILE hits the time limit."""
import mm_common as m
import queries as q

with m.neo().session(database="neo4j") as s:
    summary = s.run("EXPLAIN " + q.CYPHER_Q2).consume()
    plan = summary.plan


def walk(node, depth=0):
    a = node["args"]
    print(f"{'  ' * depth}{node['operatorType']:<28} est_rows={a.get('EstimatedRows', '?'):>12}  "
          f"{str(a.get('Details', ''))[:80]}")
    for child in node.get("children", []):
        walk(child, depth + 1)


print("===== Q2 full month (EXPLAIN, not executed) =====")
walk(plan)