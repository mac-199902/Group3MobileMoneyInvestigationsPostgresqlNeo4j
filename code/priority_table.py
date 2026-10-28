"""priority_table.py - Section 8.1 priority table built from the stored Q1 to Q7 results."""
import json

RES = r"D:\MobileMoneyProject\results"
load = lambda name: json.load(open(rf"{RES}\{name}"))
q1 = {r["set"]: r for r in load("q1_results.json")}
q3 = {r["set"]: r for r in load("q3_results.json")}
q4 = load("q4_results.json")
q5 = {r["set"]: r for r in load("q5_results.json")}
q6 = {r["set"]: r for r in load("q6_results.json")}
q7 = load("q7_results.json")


def facts(s):
    return {"account": q1[s]["account"], "hour_rwf": q1[s]["pg"][0][1],
            "sharing": len({row[0] for row in q3[s]["pg"]}),
            "d6": sum(r[1] for r in q4[f"{s}-6"]["pg"]),
            "d10": sum(r[1] for r in q4[f"{s}-10"]["pg"]),
            "chains": len(q5[s]["pg"]), "cycles": len(q6[s]["pg"]),
            "route": q7[f"{s}-6"]["pg_length"]}


widths = [7, 18, 15, 15, 12, 12, 16, 20, 14]
head = ["Pair", "Q3 sharing accts", "Q4 reached d6", "Q4 reached d10", "Q5 chains", "Q6 cycles",
        "Q7 route (b6)", "Q1 hour RWF", "Review first"]
line = "".join(h.ljust(w) for h, w in zip(head, widths))
print("Each cell: first account | second account of the pair")
print(line)
print("-" * len(line))
for a, b in (("A", "D"), ("B", "E"), ("C", "F")):
    fa, fb = facts(a), facts(b)
    sa, sb = (fa["chains"] + fa["cycles"], fa["hour_rwf"]), (fb["chains"] + fb["cycles"], fb["hour_rwf"])
    verdict = "equal" if sa == sb else (f"{a} ({fa['account']})" if sa > sb else f"{b} ({fb['account']})")
    cells = [f"{a}/{b}", f"{fa['sharing']} | {fb['sharing']}", f"{fa['d6']} | {fb['d6']}",
             f"{fa['d10']} | {fb['d10']}", f"{fa['chains']} | {fb['chains']}",
             f"{fa['cycles']} | {fb['cycles']}", f"{fa['route']} | {fb['route']}",
             f"{fa['hour_rwf']:,} | {fb['hour_rwf']:,}", verdict]
    print("".join(c.ljust(w) for c, w in zip(cells, widths)))
print()
print("Accounts: " + ", ".join(f"{s} = {facts(s)['account']}" for s in "ABCDEF"))
print("Rule: more rapid-onward (Q5) plus circular (Q6) signals first; ties go to the larger Q1 value.")
print("Q3, Q4 and Q7 are shown as structural context. This is a screening order, not a finding of fraud.")