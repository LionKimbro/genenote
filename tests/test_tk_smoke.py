import tkintertester
from tkintertester import harness

from genenote import app as genenote_app


def reset_harness():
    harness.tests[:] = []
    harness.g["root"] = None
    harness.g["current_test"] = None
    harness.g["current_step_index"] = 0
    harness.g["test_done"] = False
    harness.g["current_timeout_after_id"] = None
    harness.g["start_time"] = None
    harness.g["test_index"] = 0
    harness.g["app_entry"] = None
    harness.g["app_reset"] = None
    harness.g["timeout_ms"] = 5000
    harness.g["exit_after_tests_executed"] = None
    harness.g["show_results_in_tk_after_tests_executed"] = None
    harness.g["exit_requested"] = False


def test_app_builds_under_tkintertester(tmp_path):
    reset_harness()

    holder = {}

    def app_entry():
        state = genenote_app.create_state(tmp_path)
        holder["state"] = state
        genenote_app.build_window(state, tkintertester.get_root())

    def app_reset():
        if "state" in holder:
            genenote_app.destroy_window(holder["state"])

    def step_window_exists():
        state = holder["state"]
        if state["window"].winfo_exists() and state["widgets"]["canvas"].winfo_exists():
            return "success", None
        return "fail", "window did not build"

    tkintertester.set_resetfn(app_reset)
    tkintertester.set_timeout(2000)
    tkintertester.add_test("window builds", [step_window_exists])
    tkintertester.run_host(app_entry, "x")

    assert harness.tests[0]["status"] == "success"
