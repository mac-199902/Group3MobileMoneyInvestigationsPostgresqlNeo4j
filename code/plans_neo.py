"""plans_neo.py - PROFILE for Q4 B depth 10 and Q7 B bound 6 (Q2 is profiled with a time limit)."""
import mm_common as m
import queries as q

account_b, dest_b, day_b = m.SETS["B"]


def profile(name, text, params, seconds=170):
    print(f"===== {name} =====", flush=True)
    with m.neo().session(database="neo4j") as s:
        tx = s.begin_transaction(timeout=seconds)
        try:
            result = tx.run("PROFILE " + text, params)
            result.consume()
            summary = result.consume()
            plan = summary.profile
        except Exception as exc:
            print(f"   stopped: {type(exc).__name__}: {str(exc)[:120]}")
            return
        finally:
            try:
                tx.close()
            except Exception:
                pass

    def walk(node, depth=0):
        a = node["args"]
        print(f"{'  ' * depth}{node['operatorType']:<28} rows={a.get('Rows', '?'):>9}  "
              f"db_hits={a.get('DbHits', '?'):>10}  {str(a.get('Details', ''))[:70]}")
        for child in node.get("children", []):
            walk(child, depth + 1)
    walk(plan)
    print()


profile("Q4 set B depth 10", q.CYPHER_Q4.replace("DEPTH", "10"), {"account": account_b})
profile("Q7 set B bound 6", q.CYPHER_Q7.replace("BOUND", "6"), {"src": account_b, "dst": dest_b})
profile("Q2 full month (limited to 170 s)", q.CYPHER_Q2, {}, seconds=170)