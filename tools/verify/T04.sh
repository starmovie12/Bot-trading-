#!/usr/bin/env bash
# tools/verify/T04.sh (MISSION V11 §12, T04 G0_ECONOMICS). Exits non-zero on any failure.
# Runs on a clean checkout of HEAD (git worktree in ${TMPDIR:-/tmp}/mission-v11-verify-T04).
# Negative controls: (a) a tampered input changes the hash; (b) an unstressed ESTIMATE ceiling never
# gives FAIL_CREDIBILITY; (c) a FAIL_ARITH resting on an unapproved limit becomes CONDITIONAL;
# (d) tax is applied once: doubling the tax rate changes only the tax lines; (e) ESTIMATE / ASSUMPTION
# small costs count 2x in the FEASIBLE test and 0 in the FAIL test.
set -u
repo=$(git rev-parse --show-toplevel) || exit 2
tmp=${TMPDIR:-/tmp}
wt="$tmp/mission-v11-verify-T04"
failures=0
pass() { echo "PASS $*"; }
fail() { echo "FAIL $*"; failures=$((failures + 1)); }
cleanup() {
  git -C "$repo" worktree remove --force "$wt" >/dev/null 2>&1
  git -C "$repo" worktree prune >/dev/null 2>&1
}
cleanup
git -C "$repo" worktree add --detach "$wt" HEAD >/dev/null 2>&1 || { echo "FAIL cannot create worktree"; exit 1; }
cd "$wt" || exit 1

# two runs are byte-identical, and they reproduce the committed G0 output
python3 tools/economics.py >/dev/null && cp EVIDENCE/T04/g0.json "$wt/.g0_run1.json"
python3 tools/economics.py >/dev/null
cmp -s EVIDENCE/T04/g0.json "$wt/.g0_run1.json" && pass "two runs byte-identical" || fail "runs differ"
git diff --quiet -- EVIDENCE/T04/g0.json EVIDENCE/T04/g0_report.md EVIDENCE/numbers.json &&
  pass "committed G0 output equals a fresh run" || fail "committed G0 output is stale"
rm -f "$wt/.g0_run1.json"

python3 - <<'PY' && pass "schema, outcomes, sensitivity table and negative controls (a)-(e)" || fail "economics checks failed"
import copy, json, re, sys
sys.path.insert(0, ".")
from tools import economics as eco
fail = []
r = json.load(open("EVIDENCE/T04/g0.json"))
# schema
allowed = {"FEASIBLE", "CONDITIONAL", "FAIL_CREDIBILITY", "FAIL_ARITH"}
if r.get("g0") not in allowed or r.get("track") not in ("SHORT", "FULL"):
    fail.append("schema: g0 / track")
if not re.fullmatch(r"[0-9a-f]{64}", r.get("inputs_sha256", "")):
    fail.append("schema: inputs_sha256")
for u in ("U1", "U2", "U3", "U4", "U5", "U6"):
    m = r["members"].get(u, {})
    if m.get("outcome") not in allowed or not isinstance(m.get("reasons"), list) or not m["reasons"]:
        fail.append(f"schema: member {u}")
if set(r["sensitivity"]) != {"U1", "U2", "U3", "U4", "U5", "U6"}:
    fail.append("sensitivity table incomplete")
if set(r["stages"]["S1_API"]["cost_hurdle_per_trade_rs"]) != {"4", "8", "12", "20"}:
    fail.append("TRADES_PM sensitivity rows 4/8/12/20 missing")
if not r["limit_feasibility"]:
    fail.append("limit-feasibility table missing")
if r["track"] != ("SHORT" if all(m["outcome"].startswith("FAIL") for m in r["members"].values()) else "FULL"):
    fail.append("TRACK does not follow the member outcomes")
base = eco.build_inputs()
def run(inp):
    return eco.compute(inp)
def all_source(inp):
    for f in inp["facts"].values():
        f["tag"] = "SOURCE"
        if f["value"] == "unknown":
            f["value"] = "6"
    for k in ("strike_step_nifty", "strike_step_sensex", "band_pct", "premium_grid"):
        inp["params"][k]["tag"] = "SOURCE"
    return inp
# (a) tampered input changes the hash
t = copy.deepcopy(base); t["facts"]["gst"]["value"] = "19"
if run(t)["inputs_sha256"] == run(base)["inputs_sha256"]:
    fail.append("(a) tampered input kept the hash")
# (b) an unstressed ESTIMATE ceiling never gives FAIL_CREDIBILITY (and a SOURCE ceiling can)
b = all_source(copy.deepcopy(base))
for name in ("MAX_TOTAL_LOSS_RS", "CAPITAL_RS"):
    b["limits"][name]["approved"] = True
b["params"]["credible_ceiling_pct_pm"] = {"value": "0.01", "tag": "ESTIMATE", "why": "verify"}
if any(m["outcome"] == "FAIL_CREDIBILITY" for m in run(b)["members"].values()):
    fail.append("(b) ESTIMATE ceiling produced FAIL_CREDIBILITY")
b["params"]["credible_ceiling_pct_pm"]["tag"] = "SOURCE"
if not any(m["outcome"] == "FAIL_CREDIBILITY" for m in run(b)["members"].values()):
    fail.append("(b) positive control: a SOURCE ceiling never fired")
# (c) FAIL_ARITH on an unapproved limit → CONDITIONAL; approved → FAIL_ARITH
c = all_source(copy.deepcopy(base))
c["limits"]["MAX_TRADE_LOSS_RS"]["value"] = "20"
c["limits"]["MAX_TOTAL_LOSS_RS"]["approved"] = False
if run(c)["members"]["U1"]["outcome"] != "CONDITIONAL":
    fail.append("(c) unapproved-limit impossibility was not CONDITIONAL")
c["limits"]["MAX_TOTAL_LOSS_RS"]["approved"] = True
c["limits"]["CAPITAL_RS"]["approved"] = True
if run(c)["members"]["U1"]["outcome"] != "FAIL_ARITH":
    fail.append("(c) positive control: approved-limit impossibility was not FAIL_ARITH")
# (d) tax applied once
d = copy.deepcopy(base); d["params"]["tax_slab_pct"]["value"] = str(2 * int(base["params"]["tax_slab_pct"]["value"]))
r0, r1 = run(base), run(d)
for k in ("stages", "members", "validation", "limit_feasibility", "g0", "track"):
    if r0[k] != r1[k]:
        fail.append(f"(d) tax change moved {k}")
if r0["tax"] == r1["tax"]:
    fail.append("(d) tax change did not move the post-tax line")
# (e) small ESTIMATE / ASSUMPTION costs: 2x for FEASIBLE, 0 for FAIL
small = sum(float(base["params"][k]["value"]) for k in ("internet_share_rs_pm", "electricity_rs_pm", "ca_fee_rs_pm", "ai_share_rs_pm"))
s0, s1 = r0["stages"]["S0_MANUAL"], r0["stages"]["S1_API"]
server = float(s1["server_rs_pm"]["value"])
checks = [
    (float(s0["fixed_fail_test_rs_pm"]["value"]), 0.0),
    (float(s0["fixed_feasible_test_rs_pm"]["value"]), 2 * small),
    (float(s1["fixed_fail_test_rs_pm"]["value"]), server),
    (float(s1["fixed_feasible_test_rs_pm"]["value"]), server + 2 * small),
]
if any(abs(a - b) > 0.005 for a, b in checks):
    fail.append("(e) small costs not 2x (FEASIBLE) / 0 (FAIL)")
for f in fail:
    print("   ", f)
sys.exit(1 if fail else 0)
PY

# I12 money tests
python3 -m pytest -q tests/invariants/test_i12_money.py >/dev/null 2>&1 && pass "tests/invariants/test_i12_money.py" ||
  fail "test_i12_money.py failed"
# TRACK recorded in STATE.md equals the G0 output
track=$(python3 -c "import json;print(json.load(open('EVIDENCE/T04/g0.json'))['track'])")
grep -q "^TRACK: $track" STATE.md && pass "STATE.md TRACK = $track" || fail "STATE.md TRACK differs from G0 ($track)"
# CP1 memo exists with a SAWAL block for every open question
[ -s docs/MEMO_CP1.md ] && grep -q '^MEMO CP1' docs/MEMO_CP1.md && pass "CP1 memo present" || fail "CP1 memo missing"
for q in F-H2PCT F-DATARIGHTS F-RECFULL; do
  grep -q "^## $q | code " OWNER_QUESTIONS.md || fail "question $q not created"
done

cd "$repo" || exit 1
cleanup
left=$(find "$tmp" -maxdepth 1 -name 'mission-v11-*' 2>/dev/null)
[ -z "$left" ] && pass "no mission-v11 temp dir left" || fail "temp dir(s) left: $left"
echo "T04 verify: $failures failure(s)"
[ "$failures" -eq 0 ]
