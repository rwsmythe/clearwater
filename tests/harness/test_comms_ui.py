"""I.1 + I.2 -- the optional mail UI (comms_ui.py, the [web] extra).

Runs under stdlib unittest with FastAPI's TestClient (no third-party test
runner). Skipped when the [web] extra is not installed. Covers the inbox /
compose / bus / history surface, the L1/L3/L5 locks, the OriginGuard, and the
launch + orchestrator-bring-up surface.
"""

from __future__ import annotations

import ast
import importlib.util
import inspect
import re
import tempfile
import textwrap
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

try:
    from fastapi.testclient import TestClient  # noqa: F401
    _HAS_WEB = True
except (ImportError, RuntimeError):
    # RuntimeError: Starlette's TestClient raises it (not ImportError) when its
    # HTTP client (httpx) is absent -- the [web] extra deliberately does not pin
    # httpx, so a machine with the extra but no httpx must SKIP, not error
    # (template issue #4, item 1).
    _HAS_WEB = False


def _load_comms_ui():
    import sys
    sys.path.insert(0, str(REPO_ROOT / "scripts"))  # role_mail sibling import
    spec = importlib.util.spec_from_file_location(
        "comms_ui", REPO_ROOT / "scripts" / "comms_ui.py")
    mod = importlib.util.module_from_spec(spec)
    # Register BEFORE exec so @dataclass can resolve cls.__module__ in sys.modules.
    sys.modules["comms_ui"] = mod
    spec.loader.exec_module(mod)
    return mod


@unittest.skipUnless(_HAS_WEB, "the [web] extra is not installed")
class CommsUiTest(unittest.TestCase):
    def setUp(self) -> None:
        self.ui = _load_comms_ui()
        self.root = Path(tempfile.mkdtemp())
        self.app = self.ui.create_app(self.root, allow_launch=True)
        from fastapi.testclient import TestClient
        self.client = TestClient(self.app)
        self.headers = {"Origin": "http://127.0.0.1:8775",
                        "Host": "127.0.0.1:8775"}

    def _seed_operator_inbox(self, mtype: str = "fyi", subject: str = "hi") -> str:
        finals = self.ui.role_mail.post_message(
            self.root, "charc", ["operator"], mtype, subject, "body")
        return finals[0].name

    def _mock_run(self):
        # Scoped subprocess seam: comms_ui does `import subprocess` at module
        # level, so self.ui.subprocess IS the subprocess module; patch.object
        # swaps run() only inside the `with` block (no global leak).
        return mock.patch.object(
            self.ui.subprocess, "run",
            return_value=SimpleNamespace(returncode=0, stdout="", stderr=""))

    # --- I.1 ---
    def test_index_renders_and_shows_operator_inbox(self) -> None:
        self._seed_operator_inbox(subject="hello-op")
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("hello-op", resp.text)

    def test_compose_decision_request_refused(self) -> None:
        # L1 belt: decision_request is not in the UI type allowlist.
        resp = self.client.post(
            "/compose",
            data={"to": ["charc"], "type": "decision_request",
                  "subject": "x", "body": "y"},
            headers=self.headers)
        self.assertEqual(resp.status_code, 400)
        # Nothing written.
        self.assertFalse((self.root / "charc" / "inbox").exists()
                         and list((self.root / "charc" / "inbox").glob("*.md")))

    def test_compose_to_orchestrator_singular(self) -> None:
        # ARC-8: the orchestrator is a singular recipient -- compose lands it in
        # the one comms/orchestrator/inbox (no registry, no per-generation dir).
        resp = self.client.post(
            "/compose",
            data={"to": ["orchestrator"], "type": "status",
                  "subject": "for-orch", "body": "y"},
            headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        inbox = self.root / "orchestrator" / "inbox"
        self.assertEqual(len(list(inbox.glob("*.md"))), 1)

    def test_ack_operator_only(self) -> None:
        # L3: the UI acks ONLY the operator inbox. Ack endpoint takes a filename
        # and hardcodes role=operator; a director file is never ackable here.
        name = self._seed_operator_inbox()
        resp = self.client.post("/ack", data={"filename": name},
                                headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            list((self.root / "operator" / "inbox").glob("*.md")), [])
        self.assertEqual(
            len(list((self.root / "operator" / "read").glob("*.md"))), 1)

    def test_cross_origin_post_403(self) -> None:
        resp = self.client.post(
            "/compose",
            data={"to": ["charc"], "type": "fyi", "subject": "x", "body": "y"},
            headers={"Origin": "http://evil.example", "Host": "127.0.0.1:8775"})
        self.assertEqual(resp.status_code, 403)

    def test_director_bus_roles_are_the_two_directors(self) -> None:
        # The director bus shows the singular director(s) -- one ships; the
        # orchestrator is rendered as its own section, NOT a director-bus role.
        self.assertEqual(self.ui.DIRECTOR_BUS_ROLES, ("charc",))

    def test_compose_form_offers_orchestrator_recipient(self) -> None:
        # IMPORTANT: the /compose route accepts ARBITRARY `to` values and
        # delegates to post_message, so a backend POST proves nothing about the
        # form. Assert the RENDERED index HTML exposes the orchestrator as a
        # compose option (and no retired/unknown role).
        html = self.client.get("/").text
        self.assertIn('value="orchestrator"', html)

    def test_compose_to_charc_writes_charc_inbox(self) -> None:
        resp = self.client.post(
            "/compose",
            data={"to": ["charc"], "type": "status",
                  "subject": "for-charc", "body": "y"},
            headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        inbox = self.root / "charc" / "inbox"
        self.assertEqual(len(list(inbox.glob("*.md"))), 1)

    def test_charc_read_history_appears(self) -> None:
        finals = self.ui.role_mail.post_message(
            self.root, "orchestrator", ["charc"], "status", "charc-hist", "body")
        self.ui.role_mail.ack_message(self.root, "charc", finals[0].name)
        resp = self.client.get("/panes/history")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("charc-hist", resp.text)

    def test_bus_shows_singular_orchestrator_inbox(self) -> None:
        # ARC-8: the orchestrator renders as ONE singular "orchestrator inbox"
        # bus section (no per-generation "generation <sid>" sections), and the
        # archive-move migration's comms/orchestrator/_archive/ is IGNORED by the
        # singular read.
        self.ui.role_mail.post_message(
            self.root, "charc", ["orchestrator"], "status", "bus-msg", "body")
        # A frozen historical generation under _archive/ must NOT leak into the bus.
        archived = self.root / "orchestrator" / "_archive" / "old-sid" / "inbox"
        archived.mkdir(parents=True)
        (archived / "20240601T120000Z-charc-archived.md").write_text(
            "---\nfrom: charc\nto: orchestrator\ntype: status\n"
            "subject: archived-msg\nposted: x\n---\n\nold\n", encoding="utf-8")
        resp = self.client.get("/panes/bus")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("bus-msg", resp.text)
        self.assertNotIn("generation ", resp.text)
        self.assertNotIn("archived-msg", resp.text)

    # --- I.2 ---
    def test_launch_invalid_role_400(self) -> None:
        resp = self.client.post(
            "/launch", data={"role": "evil", "mode": "fresh"},
            headers=self.headers)
        self.assertEqual(resp.status_code, 400)

    def test_launch_roles_are_the_shipped_enum(self) -> None:
        self.assertEqual(self.ui.LAUNCH_ROLES,
                         ("both", "charc", "orchestrator"))

    def test_orchestrator_bootstrap_served_verbatim(self) -> None:
        resp = self.client.get("/orchestrator-bootstrap")
        self.assertEqual(resp.status_code, 200)
        # The bring-up block lives in charc-bootstrap.md step 5.
        self.assertIn("HARNESS_ROLE=orchestrator", resp.text)

    def test_htmx_asset_route_serves_the_inlined_client(self) -> None:
        # R2-MAJOR-1: HTMX_JS must be a non-empty module global defined BEFORE
        # main() serves -- so the /static/htmx.min.js route never NameErrors.
        self.assertTrue(getattr(self.ui, "HTMX_JS", ""),
                        "HTMX_JS must be a non-empty module global")
        resp = self.client.get("/static/htmx.min.js")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("htmx", resp.text)

    # --- Task A: dark-theme toggle (B-11) ---
    def test_theme_toggle_control_renders(self) -> None:
        # The toggle button is rendered in the page header with the toggleTheme
        # onclick handler (the user-facing dark/light control).
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn('id="theme-toggle"', resp.text)
        self.assertIn('onclick="toggleTheme()"', resp.text)

    def test_persisted_theme_preference_head_script_present(self) -> None:
        # The persisted-preference machinery: the no-flash head script reads the
        # localStorage key, the toggleTheme function flips + persists it, and the
        # dark palette ships as a :root[data-theme="dark"] custom-property block.
        resp = self.client.get("/")
        self.assertIn('localStorage.getItem("comms-theme")', resp.text)
        self.assertIn("function toggleTheme()", resp.text)
        self.assertIn(':root[data-theme="dark"]', resp.text)

    # --- Task B: expand-preserve across the 5s poll (B-13) ---
    def test_expand_preserve_live_set_js_present(self) -> None:
        # The expand-preserve script tracks open <details> rows in a live set
        # and re-opens them after every htmx swap (so an open message is not
        # collapsed by the 5s innerHTML poll). Asserting the JS -- not merely the
        # data-key attribute, which already exists -- is what distinguishes.
        resp = self.client.get("/")
        self.assertIn("htmx:afterSwap", resp.text)
        self.assertIn("details.msg[data-key]", resp.text)
        self.assertIn("openKeys", resp.text)

    # --- inc2: mechanical preservation meta-test (Step P.0) ---
    def test_existing_assertions_preserved(self) -> None:
        # Three mechanical layers guard against an accidental drop of any
        # existing assertion (byte-verbatim preservation is a review concern).
        cls_map = {
            "CommsUiTest": CommsUiTest,
            "HtmxConstantOrderingTest": HtmxConstantOrderingTest,
            "UiImportIsolationTest": UiImportIsolationTest,
        }
        # The 19 existing method names, per class (hard-coded HEAD baseline).
        existing = {
            "CommsUiTest": [
                "test_index_renders_and_shows_operator_inbox",
                "test_compose_decision_request_refused",
                "test_compose_to_orchestrator_singular",
                "test_ack_operator_only",
                "test_cross_origin_post_403",
                "test_director_bus_roles_are_the_two_directors",
                "test_compose_form_offers_orchestrator_recipient",
                "test_compose_to_charc_writes_charc_inbox",
                "test_charc_read_history_appears",
                "test_bus_shows_singular_orchestrator_inbox",
                "test_launch_invalid_role_400",
                "test_launch_roles_are_the_shipped_enum",
                "test_orchestrator_bootstrap_served_verbatim",
                "test_htmx_asset_route_serves_the_inlined_client",
                "test_theme_toggle_control_renders",
                "test_persisted_theme_preference_head_script_present",
                "test_expand_preserve_live_set_js_present",
            ],
            "HtmxConstantOrderingTest": ["test_htmx_js_defined_before_main"],
            "UiImportIsolationTest": ["test_core_does_not_import_comms_ui"],
        }
        self.assertEqual(
            sum(len(v) for v in existing.values()), 19,
            "the preservation baseline must enumerate exactly 19 methods")

        # Per-method self.assert*/self.fail COUNT baseline captured at build
        # start (>= holds; a deletion drops the count and FAILS).
        assert_count_baseline = {
            "test_index_renders_and_shows_operator_inbox": 2,
            "test_compose_decision_request_refused": 2,
            "test_compose_to_orchestrator_singular": 2,
            "test_ack_operator_only": 3,
            "test_cross_origin_post_403": 1,
            "test_director_bus_roles_are_the_two_directors": 1,
            "test_compose_form_offers_orchestrator_recipient": 1,
            "test_compose_to_charc_writes_charc_inbox": 2,
            "test_charc_read_history_appears": 2,
            "test_bus_shows_singular_orchestrator_inbox": 3,
            "test_launch_invalid_role_400": 1,
            "test_launch_roles_are_the_shipped_enum": 1,
            "test_orchestrator_bootstrap_served_verbatim": 2,
            "test_htmx_asset_route_serves_the_inlined_client": 3,
            "test_theme_toggle_control_renders": 3,
            "test_persisted_theme_preference_head_script_present": 3,
            "test_expand_preserve_live_set_js_present": 3,
            "test_htmx_js_defined_before_main": 2,
            "test_core_does_not_import_comms_ui": 2,
        }
        all_names = {n for names in existing.values() for n in names}
        self.assertEqual(
            set(assert_count_baseline), all_names,
            "the assert-count baseline must cover exactly the 19 methods")
        assert_attrs = {
            "assertEqual", "assertNotEqual", "assertIn", "assertNotIn",
            "assertTrue", "assertFalse", "assertIs", "assertIsNot",
            "assertLess", "assertLessEqual", "assertGreater",
            "assertGreaterEqual", "assertRaises", "fail",
        }

        def _method_ast(cls, name):
            src = textwrap.dedent(inspect.getsource(getattr(cls, name)))
            return ast.parse(src)

        def _self_assert_calls(tree):
            calls = []
            for node in ast.walk(tree):
                if (isinstance(node, ast.Call)
                        and isinstance(node.func, ast.Attribute)
                        and node.func.attr in assert_attrs
                        and isinstance(node.func.value, ast.Name)
                        and node.func.value.id == "self"):
                    calls.append(node)
            return calls

        def _lit(node):
            # literal_eval a node; return a sentinel on failure (non-literal).
            try:
                return ast.literal_eval(node)
            except (ValueError, TypeError, SyntaxError):
                return _NOTLIT

        _NOTLIT = object()

        # Layer 1: names still-loaded (subset).
        for cls_name, names in existing.items():
            loaded = set(unittest.TestLoader().getTestCaseNames(
                cls_map[cls_name]))
            missing = set(names) - loaded
            self.assertEqual(
                missing, set(),
                f"{cls_name} lost preserved test(s): {sorted(missing)}")

        # Layer 2: per-method assert-COUNT backstop (completeness guarantee).
        name_to_cls = {}
        for cls_name, names in existing.items():
            for n in names:
                name_to_cls[n] = cls_map[cls_name]
        for name, baseline in assert_count_baseline.items():
            tree = _method_ast(name_to_cls[name], name)
            count = len(_self_assert_calls(tree))
            self.assertGreaterEqual(
                count, baseline,
                f"{name}: assert-count {count} dropped below baseline {baseline}")

        # Layer 3: per-row VALUE pins (quote-agnostic, semantic).
        def _calls_to(cls, method, attr):
            tree = _method_ast(cls, method)
            out = []
            for node in ast.walk(tree):
                if (isinstance(node, ast.Call)
                        and isinstance(node.func, ast.Attribute)
                        and node.func.attr == attr):
                    out.append(node)
            return out

        def _self_calls_to(cls, method, attr):
            return [n for n in _calls_to(cls, method, attr)
                    if isinstance(n.func.value, ast.Name)
                    and n.func.value.id == "self"]

        def _has_arg_value(calls, value, arg_index=None):
            for c in calls:
                args = c.args
                if arg_index is not None:
                    if arg_index < len(args) and _lit(args[arg_index]) == value:
                        return True
                else:
                    if any(_lit(a) == value for a in args):
                        return True
            return False

        C = "CommsUiTest"
        # Row 1: L1 refused -> assertEqual(status, 400).
        self.assertTrue(_has_arg_value(
            _self_calls_to(cls_map[C], "test_compose_decision_request_refused",
                           "assertEqual"), 400),
            "row1: assertEqual with 400 missing")
        # Row 3: OriginGuard -> assertEqual(..., 403); Origin http://evil.example.
        self.assertTrue(_has_arg_value(
            _self_calls_to(cls_map[C], "test_cross_origin_post_403",
                           "assertEqual"), 403),
            "row3: assertEqual with 403 missing")
        tree3 = _method_ast(cls_map[C], "test_cross_origin_post_403")
        self.assertTrue(
            any(_lit(n) == "http://evil.example" for n in ast.walk(tree3)),
            "row3: Origin http://evil.example missing")
        # Row 4: L5 invalid role -> assertEqual(..., 400); role "evil".
        self.assertTrue(_has_arg_value(
            _self_calls_to(cls_map[C], "test_launch_invalid_role_400",
                           "assertEqual"), 400),
            "row4: assertEqual with 400 missing")
        tree4 = _method_ast(cls_map[C], "test_launch_invalid_role_400")
        self.assertTrue(
            any(_lit(n) == "evil" for n in ast.walk(tree4)),
            "row4: role value 'evil' missing")
        # Row 5: the launch-role enum tuple.
        self.assertTrue(_has_arg_value(
            _self_calls_to(cls_map[C], "test_launch_roles_are_the_shipped_enum",
                           "assertEqual"),
            ("both", "charc", "orchestrator")),
            "row5: LAUNCH_ROLES tuple pin missing")
        # Row 6: compose offers the orchestrator -> assertIn 'value="orchestrator"'.
        self.assertTrue(_has_arg_value(
            _self_calls_to(cls_map[C], "test_compose_form_offers_orchestrator_recipient",
                           "assertIn"), 'value="orchestrator"', arg_index=0),
            "row6: assertIn value=\"orchestrator\" missing")
        # Row 7: charc inbox-count postcondition -> assertEqual(..., 1).
        self.assertTrue(_has_arg_value(
            _self_calls_to(cls_map[C], "test_compose_to_charc_writes_charc_inbox",
                           "assertEqual"), 1, arg_index=1),
            "row7: assertEqual(len(...), 1) postcondition missing")
        # Row 8: bus roles tuple.
        self.assertTrue(_has_arg_value(
            _self_calls_to(cls_map[C], "test_director_bus_roles_are_the_two_directors",
                           "assertEqual"), ("charc",)),
            "row8: DIRECTOR_BUS_ROLES tuple pin missing")
        # Row 9: htmx asset -> assertTrue(getattr(self.ui, "HTMX_JS", ...)).
        htmx_calls = _self_calls_to(
            cls_map[C], "test_htmx_asset_route_serves_the_inlined_client",
            "assertTrue")
        found_htmx = False
        for c in htmx_calls:
            for a in c.args:
                if (isinstance(a, ast.Call)
                        and isinstance(a.func, ast.Name)
                        and a.func.id == "getattr"
                        and len(a.args) >= 2
                        and _lit(a.args[1]) == "HTMX_JS"):
                    found_htmx = True
        self.assertTrue(found_htmx,
                        "row9: assertTrue(getattr(..., 'HTMX_JS', ...)) missing")
        # Row 10 SPECIAL-CASE: str.startswith("HTMX_JS = r") + two assertLess.
        H = "HtmxConstantOrderingTest"
        starts = _calls_to(cls_map[H], "test_htmx_js_defined_before_main",
                           "startswith")
        self.assertTrue(
            any(_lit(a) == "HTMX_JS = r" for c in starts for a in c.args),
            "row10: startswith('HTMX_JS = r') missing")
        self.assertGreaterEqual(
            len(_self_calls_to(cls_map[H], "test_htmx_js_defined_before_main",
                               "assertLess")), 2,
            "row10: two assertLess calls missing")
        # Row 11: import isolation -> assertNotIn "comms_ui" AND "import fastapi".
        I = "UiImportIsolationTest"
        nin = _self_calls_to(cls_map[I], "test_core_does_not_import_comms_ui",
                             "assertNotIn")
        self.assertTrue(_has_arg_value(nin, "comms_ui", arg_index=0),
                        "row11: assertNotIn 'comms_ui' missing")
        self.assertTrue(_has_arg_value(nin, "import fastapi", arg_index=0),
                        "row11: assertNotIn 'import fastapi' missing")
        # Row 12: charc read-history -> assertIn "charc-hist".
        self.assertTrue(_has_arg_value(
            _self_calls_to(cls_map[C], "test_charc_read_history_appears",
                           "assertIn"), "charc-hist", arg_index=0),
            "row12: assertIn 'charc-hist' missing")
        # Row 2: L3 operator-only ack -- value-pin the postconditions (status
        # 200, emptied inbox [], one read file) so a same-count swap cannot evade
        # the count layer (guards the L3 lock, not just the assert count).
        ack_eq = _self_calls_to(cls_map[C], "test_ack_operator_only", "assertEqual")
        self.assertTrue(_has_arg_value(ack_eq, 200),
                        "row2: assertEqual(status, 200) missing")
        self.assertTrue(_has_arg_value(ack_eq, [], arg_index=1),
                        "row2: assertEqual(inbox glob, []) postcondition missing")
        self.assertTrue(_has_arg_value(ack_eq, 1, arg_index=1),
                        "row2: assertEqual(len(read glob), 1) postcondition missing")

    # --- inc2 Phase 1: LAUNCH_VEHICLES enum + radio + validate-before-argv ---
    def test_launch_vehicles_enum(self) -> None:
        self.assertEqual(self.ui.LAUNCH_VEHICLES, ("psmux", "powershell"))

    def test_launch_strip_renders_vehicle_radio_psmux_checked(self) -> None:
        html = self.client.get("/").text
        self.assertIn('name="vehicle"', html)
        self.assertIn('value="psmux"', html)
        self.assertIn('value="powershell"', html)
        # Prove psmux is THE default: exactly one vehicle input carries `checked`
        # and it is the value="psmux" input (a radio group's later-checked input
        # would otherwise win).
        inputs = re.findall(r'<input[^>]*name="vehicle"[^>]*>', html)
        checked = [i for i in inputs if "checked" in i]
        self.assertEqual(len(checked), 1,
                         "exactly one vehicle input must be checked")
        self.assertIn('value="psmux"', checked[0])

    def test_launch_invalid_vehicle_400(self) -> None:
        with self._mock_run() as m:
            resp = self.client.post(
                "/launch",
                data={"role": "charc", "mode": "fresh", "vehicle": "evil"},
                headers=self.headers)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("invalid vehicle &#39;evil&#39;", resp.text)
        m.assert_not_called()

    def test_vehicle_validated_before_argv_construction(self) -> None:
        # The spec requires validate vehicle BEFORE argv CONSTRUCTION; assert
        # SOURCE ORDER in the /launch closure (m.assert_not_called alone does
        # not prove the ordering).
        src = inspect.getsource(self.ui.create_app)
        self.assertLess(src.index("vehicle not in LAUNCH_VEHICLES"),
                        src.index('argv = ["powershell"'),
                        "vehicle guard must precede argv construction")

    def test_launch_vehicle_form_default_is_psmux(self) -> None:
        src = Path(self.ui.__file__).read_text(encoding="utf-8")
        self.assertIsNotNone(
            re.search(
                r'vehicle\s*:\s*str\s*=\s*Form\(\s*default\s*=\s*["\']psmux["\']',
                src),
            "vehicle must default to 'psmux' via Form(default=...)")

    def test_launch_missing_vehicle_defaults_psmux(self) -> None:
        with self._mock_run() as m:
            resp = self.client.post(
                "/launch", data={"role": "charc", "mode": "fresh"},
                headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn("-NoPsmux", m.call_args.args[0])

    # --- inc2 Phase 2: the four exact argvs + execution-contract kwargs ---
    _BASE_ARGV = ["powershell", "-NoProfile", "-File",
                  "scripts/launch_role.ps1", "-Role", "charc"]

    def _assert_launch_argv(self, mode, vehicle, expected_argv) -> None:
        data = {"role": "charc", "mode": mode, "vehicle": vehicle}
        with self._mock_run() as m:
            resp = self.client.post("/launch", data=data, headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(m.call_args.args[0], expected_argv)
        kwargs = m.call_args.kwargs
        self.assertEqual(kwargs["cwd"], str(self.ui._REPO_ROOT))
        self.assertIs(kwargs["capture_output"], True)
        self.assertIs(kwargs["text"], True)
        self.assertEqual(kwargs["timeout"], 30)

    def test_launch_psmux_fresh_argv(self) -> None:
        self._assert_launch_argv("fresh", "psmux", list(self._BASE_ARGV))

    def test_launch_psmux_resume_argv(self) -> None:
        self._assert_launch_argv("resume", "psmux",
                                 list(self._BASE_ARGV) + ["-Resume"])

    def test_launch_powershell_fresh_argv(self) -> None:
        self._assert_launch_argv("fresh", "powershell",
                                 list(self._BASE_ARGV) + ["-NoPsmux"])

    def test_launch_powershell_resume_argv(self) -> None:
        self._assert_launch_argv("resume", "powershell",
                                 list(self._BASE_ARGV) + ["-Resume", "-NoPsmux"])

    def test_l5_lock_wording_revised(self) -> None:
        src = Path(self.ui.__file__).read_text(encoding="utf-8")
        self.assertIn(
            "one of a FIXED SET of enum-validated argv VARIANTS", src)
        self.assertNotIn("runs exactly one fixed argv", src)

    # --- inc2 Phase 3: serve_port plumbing (create_app <- main -> _launch_ctx) ---
    def test_serve_port_plumbed_nondefault(self) -> None:
        from fastapi.testclient import TestClient
        app9 = self.ui.create_app(self.root, serve_port=9999)
        resp = TestClient(app9).get("/")
        self.assertIn("http://127.0.0.1:9999", resp.text)

    def test_main_passes_cli_port_into_create_app(self) -> None:
        with mock.patch.object(self.ui, "create_app") as mc, \
                mock.patch("uvicorn.run") as mu:
            self.ui.main(["--port", "9999", "--comms-root", str(self.root),
                          "--no-browser"])
        self.assertEqual(mc.call_args.kwargs.get("serve_port"), 9999)
        self.assertEqual(mu.call_args.kwargs.get("port"), 9999)

    # --- inc2 Phase 4: remote hint (escaped, <code>, 127.0.0.1) + warning ---
    def test_remote_hint_line_escaped_and_127(self) -> None:
        resp = self.client.get("/")  # setUp app, default port 8775
        self.assertIn("ssh -L 8775:127.0.0.1:8775", resp.text)
        self.assertIn("&lt;user&gt;@&lt;host&gt;", resp.text)
        self.assertIn("http://127.0.0.1:8775", resp.text)
        # The attach command shows the REPO-DERIVED session name (D3 default),
        # not the pre-D3 literal 'agents'. Compare against the module's own
        # derivation so this stays worktree-agnostic (main tree -> the repo's
        # own basename; this worktree -> 'ui-hint-fix').
        session = self.ui._SESSION_NAME
        self.assertIn(f"psmux attach -t {session}", resp.text)
        # The raw unescaped placeholders must be ABSENT (proves HTML escaping).
        self.assertNotIn("<user>@<host>", resp.text)
        # The whole hint body is ONE <code> block (spec sec 2 containment).
        self.assertIn(
            "<code>Remote: ssh -L 8775:127.0.0.1:8775 &lt;user&gt;@&lt;host&gt; "
            "then browse http://127.0.0.1:8775; agents land in psmux -- attach "
            f"with: psmux attach -t {session}</code>",
            resp.text)

    def test_no_localhost_in_hint(self) -> None:
        resp = self.client.get("/")
        self.assertNotIn("localhost:8775", resp.text)

    def test_tunnel_exposure_warning_visible(self) -> None:
        resp = self.client.get("/")
        self.assertIn(
            '<p class="tunnel-warn">Keep the forward loopback-only: no -g / '
            "0.0.0.0 / LAN-share / public tunnels -- these buttons run processes "
            "on the laptop.</p>",
            resp.text)
        # The warning is VISIBLE page text -- not hidden by an attribute...
        self.assertNotIn('tunnel-warn" hidden', resp.text)
        self.assertNotIn('tunnel-warn" style="display:none', resp.text)
        self.assertNotIn("aria-hidden", resp.text)
        self.assertNotIn('title="Keep the forward', resp.text)
        # ...nor by a same-block CSS rule.
        self.assertIsNone(
            re.search(
                r"\.tunnel-warn\s*\{[^}]*"
                r"(display\s*:\s*none|visibility\s*:\s*hidden)",
                resp.text))

    def test_module_docstring_remote_note(self) -> None:
        doc = self.ui.__doc__
        self.assertIn("ssh -L", doc)
        # The docstring attach command carries the repo-derived session name too
        # (substituted into __doc__ at import); worktree-agnostic via the
        # module's own derivation.
        self.assertIn(f"psmux attach -t {self.ui._SESSION_NAME}", doc)
        self.assertIn("loopback", doc)

    # --- ui-hint-fix drift fences: keep the UI's derived name == launcher's ---
    def test_session_name_derivation_unit(self) -> None:
        # Pure-unit mirror of launch_role.ps1 Get-DefaultSessionName: invalid-char
        # runs collapse to a SINGLE dash (replace, never bare-strip); consecutive
        # dashes collapse; leading/trailing dashes trim; '.'/'_' survive; an empty
        # or all-invalid basename falls back to 'agents'.
        f = self.ui._default_session_name
        self.assertEqual(f(Path("/x/sample-app")), "sample-app")
        self.assertEqual(f(Path("/x/foo bar")), "foo-bar")          # space run
        self.assertEqual(f(Path("/x/my repo!!name")), "my-repo-name")  # runs
        self.assertEqual(f(Path("/x/--weird--")), "weird")          # trim dashes
        self.assertEqual(f(Path("/x/my.app_v2")), "my.app_v2")      # . and _ kept
        self.assertEqual(f(Path("/x/@@@")), "agents")               # degenerate
        self.assertEqual(f(Path("/x/a  b")), "a-b")                 # collapse
        # The result always re-validates against the launcher's conservative
        # alphabet (^[A-Za-z0-9._-]+$).
        for probe in ("sample-app", "foo-bar", "my.app_v2", "agents"):
            self.assertRegex(f(Path("/x/" + probe)), r"^[A-Za-z0-9._-]+$")

    def test_ui_derivation_matches_launcher_dryrun(self) -> None:
        # PARITY drift fence: the launcher's LIVE default session name (parsed
        # from a real -DryRun) must equal the UI's Python derivation. Compare
        # DERIVATIONS (not a literal) so it holds in any checkout. Requires
        # Windows + powershell; skips if the psmux vehicle is not active (the
        # session name only surfaces on the psmux vehicle line).
        import shutil
        import subprocess
        import sys
        if sys.platform != "win32":
            self.skipTest("launcher parity requires Windows powershell")
        pwsh = shutil.which("powershell")
        if not pwsh:
            self.skipTest("powershell not on PATH")
        script = REPO_ROOT / "scripts" / "launch_role.ps1"
        proc = subprocess.run(
            [pwsh, "-NoProfile", "-ExecutionPolicy", "Bypass",
             "-File", str(script), "-DryRun", "-Role", "charc"],
            capture_output=True, text=True, timeout=120)
        out = (proc.stdout or "") + "\n" + (proc.stderr or "")
        # A crashed launcher is NOT an honest skip -- fail loudly so a launcher
        # regression cannot masquerade as "psmux inactive".
        self.assertEqual(
            proc.returncode, 0,
            f"launcher DryRun exited {proc.returncode}:\n{out}")
        m = re.search(r"shared psmux session '([^']+)'", out)
        if not m:
            # Launcher RAN cleanly but chose the FALLBACK vehicle (psmux not
            # resolved / preflight-failed): the session name is not surfaced on
            # that line. A skip here is honest -- not a false pass.
            self.skipTest(
                "psmux vehicle not active in launcher DryRun; "
                "session name not surfaced")
        launcher_name = m.group(1)
        self.assertEqual(
            launcher_name,
            self.ui._default_session_name(self.ui._REPO_ROOT),
            "UI derived session name drifted from the launcher's live default")


@unittest.skipUnless(_HAS_WEB, "the [web] extra is not installed")
class HtmxConstantOrderingTest(unittest.TestCase):
    """R2-MAJOR-1 -- HTMX_JS is defined ABOVE main()/__main__ (source order)."""

    def test_htmx_js_defined_before_main(self) -> None:
        src = (REPO_ROOT / "scripts" / "comms_ui.py").read_text(encoding="utf-8")
        lines = src.split("\n")
        htmx_line = next(i for i, ln in enumerate(lines)
                         if ln.startswith("HTMX_JS = r"))
        main_def = next(i for i, ln in enumerate(lines)
                        if ln.startswith("def main("))
        main_block = next(i for i, ln in enumerate(lines)
                          if ln.startswith("if __name__"))
        self.assertLess(htmx_line, main_def,
                        "HTMX_JS must be defined before def main")
        self.assertLess(htmx_line, main_block,
                        "HTMX_JS must be defined before the __main__ block")


@unittest.skipUnless(_HAS_WEB, "the [web] extra is not installed")
class UiImportIsolationTest(unittest.TestCase):
    def test_core_does_not_import_comms_ui(self) -> None:
        # The UI is import-isolated: role_mail must not import comms_ui (so the
        # zero-hard-deps core posture holds). Assert role_mail's source carries
        # no comms_ui import.
        src = (REPO_ROOT / "scripts" / "role_mail.py").read_text(encoding="utf-8")
        self.assertNotIn("comms_ui", src)
        self.assertNotIn("import fastapi", src)


if __name__ == "__main__":
    unittest.main()
