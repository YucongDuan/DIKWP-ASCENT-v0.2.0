import copy
import itertools
import math
import pytest
from dikwp_ascent.dsl import validate_program,fit,predict,schedule
from dikwp_ascent.canonical import Invalid,load_json
from dikwp_ascent.evaluator import optimum,audit_pair
from dikwp_ascent.problems import rows,schedules,validate_custom,make_split

@pytest.mark.parametrize("bad",[
 {},{"kind":"shell","command":"echo test"},
 {"kind":"basis","features":["__import__"],"ridge":0.001},
 {"kind":"basis","features":["x","x"],"ridge":0.001},
 {"kind":"basis","features":["x"],"ridge":float("nan")},
 {"kind":"basis","features":["x"],"ridge":True},
 {"kind":"basis","features":[],"ridge":0.001,"authority":True},
 {"kind":"scheduler","cost_power":1,"swap_passes":4},
 {"kind":"scheduler","cost_power":float("inf"),"swap_passes":1},
 {"kind":"scheduler","cost_power":1,"swap_passes":1.5},
])
def test_bad_program(bad):
    with pytest.raises((Invalid,TypeError)):validate_program(bad)

def test_fit_quadratic():
    rs=[{"x":x/10,"y":1+2*x/10+3*(x/10)**2} for x in range(-20,21)]
    model=fit({"kind":"basis","features":["x","x2"],"ridge":1e-6},rs)
    assert abs(predict(model,{"x":3})-34)<1e-5

def test_no_restricted_data_retrieval():
    with pytest.raises(Invalid):validate_program({"kind":"basis","features":["../../controller.key"],"ridge":.001})

def test_knapsack_oracle_matches_exhaustive():
    for case in schedules(31,8):
        best=0
        for mask in itertools.product([0,1],repeat=len(case["jobs"])):
            if sum(j["cost"]*b for j,b in zip(case["jobs"],mask))<=case["capacity"]:
                best=max(best,sum(j["value"]*b for j,b in zip(case["jobs"],mask)))
        assert optimum(case)==best

def test_all_scheduler_policies_feasible():
    for power,swaps,case in itertools.product([0,.5,1,1.5,2],range(4),schedules(17,12)):
        selected=schedule({"kind":"scheduler","cost_power":power,"swap_passes":swaps},case)
        assert len(set(selected))==len(selected)
        assert sum(case["jobs"][i]["cost"] for i in selected)<=case["capacity"]

def test_proxy_overfit_rejected():
    train=rows("sensor_shift",17)
    baseline=fit({"kind":"basis","features":["x"],"ridge":.001},train)
    shortcut=fit({"kind":"basis","features":["proxy"],"ridge":.001},train)
    report=audit_pair(baseline,shortcut,make_split("sensor_shift",17,"audit"))
    assert not report["eligible"]
    assert report["worlds"]["proxy_failure"]["candidate"]>report["worlds"]["proxy_failure"]["baseline"]

def custom():
    return {"train":rows("quadratic",1,16),"development":{w:rows("quadratic",i+4,16,w) for i,w in enumerate(["in_distribution","shifted_inputs"])},"audit":{w:rows("quadratic",i+9,16,w) for i,w in enumerate(["in_distribution","shifted_inputs"])}}

def test_custom_valid():assert validate_custom(custom())

def test_custom_overlap_rejected():
    c=custom();c["audit"]["in_distribution"][0]=copy.deepcopy(c["train"][0])
    with pytest.raises(Invalid):validate_custom(c)

def test_custom_one_world_rejected():
    c=custom();del c["audit"]["shifted_inputs"]
    with pytest.raises(Invalid):validate_custom(c)

def test_nonfinite_data_rejected():
    c=custom();c["train"][0]["y"]=float("nan")
    with pytest.raises(Invalid):validate_custom(c)

def test_duplicate_json_key_rejected(tmp_path):
    p=tmp_path/"x.json";p.write_text('{"a":1,"a":2}')
    with pytest.raises(Invalid):load_json(p)
