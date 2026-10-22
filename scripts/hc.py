#!/usr/bin/env python3
"""SCNet hashcat application driver; local planning needs no credentials."""
from __future__ import annotations
import argparse
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import sys
import tempfile
import time
import uuid
from scnet_lite import Client, ClientError, default_region
from scnet_version import VERSION

ROOT = Path(__file__).resolve().parent.parent


def emit(value):
    print(json.dumps(value, ensure_ascii=False, indent=2), flush=True)


def profile(name):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", name):
        raise ClientError("invalid cluster profile name")
    path = ROOT / "clusters" / (name + ".conf")
    if not path.is_file():
        raise ClientError("unknown cluster profile: " + name)
    values = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        tokens = shlex.split(line, comments=True)
        if tokens:
            key, sep, value = tokens[0].partition("=")
            if not sep or len(tokens) != 1:
                raise ClientError("profile must contain simple KEY=value assignments")
            values[key] = value
    stack_name = values.get("STACK_PROFILE")
    if stack_name:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", stack_name):
            raise ClientError("invalid stack profile name")
        stack_path = ROOT / "stacks" / (stack_name + ".json")
        try:
            stack = json.loads(stack_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise ClientError("invalid stack profile: " + stack_name) from exc
        if not isinstance(stack, dict) or not isinstance(stack.get("module"), str) or not isinstance(stack.get("signature"), dict):
            raise ClientError("stack profile requires module and signature")
        values["HASHCAT_MODULE"] = stack["module"]
        values["STACK_ID"] = str(stack.get("id", stack_name))
        values["STACK_SIGNATURE"] = stack["signature"]
    return values


def positive(value):
    n = int(value)
    if n < 1:
        raise argparse.ArgumentTypeError("must be >= 1")
    return n


def local_path(value):
    # Only local-path options are translated. Remote /public/... stays untouched.
    if os.name == "nt" and re.match(r"^/[A-Za-z]/", value):
        value = value[1] + ":" + value[2:]
    return Path(value).expanduser()


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--version", action="version", version="hc " + VERSION)
    sub = p.add_subparsers(dest="op", required=True)
    sub.add_parser("version")
    for op in ("doctor", "crack", "status", "collect", "cancel"):
        c = sub.add_parser(op)
        c.add_argument("--region")
        c.add_argument("--cluster", default=os.getenv("SCNET_HASHCAT_CLUSTER", "kseshell"))
        if op in ("status", "collect", "cancel"):
            c.add_argument("job_id")
        if op == "collect":
            c.add_argument("--out", type=local_path)
            c.add_argument("--cover", action="store_true")
        if op == "crack":
            c.add_argument("--hashes", required=True, type=local_path)
            c.add_argument("--dict", type=local_path)
            c.add_argument("--rules", type=local_path)
            c.add_argument("--mask")
            c.add_argument("--mode", type=int, default=0)
            c.add_argument("--attack", choices=("0", "1", "3"), help="0 dictionary, 1 legacy rules alias, 3 mask; combinator attack is unsupported")
            c.add_argument("--nodes", type=positive, default=1)
            c.add_argument("--dcus-per-node", type=positive, default=1)
            c.add_argument("--cpus-per-node", type=positive, default=8)
            for key in ("queue", "walltime", "module", "modulefiles"):
                c.add_argument("--" + key, default=os.getenv("SCNET_HASHCAT_" + key.upper()))
            c.add_argument("--work-dir")
            c.add_argument("--name")
            c.add_argument("--extra-args", default="")
            c.add_argument("--wait", action="store_true")
            c.add_argument("--wait-timeout", type=positive, default=900)
            c.add_argument("--dry-run", action="store_true")
            c.add_argument("--skip-precheck", action="store_true")
    c = sub.add_parser("precheck")
    c.add_argument("--hashes", required=True, type=local_path)
    c.add_argument("--mode", type=int, default=0)
    c.add_argument("--json", action="store_true")
    c = sub.add_parser("split")
    c.add_argument("--input", required=True, type=local_path)
    c.add_argument("--parts", type=positive, required=True)
    c.add_argument("--outdir", type=local_path, required=True)
    return p


def precheck(args):
    spec = importlib.util.spec_from_file_location("hc_precheck", ROOT / "scripts/remote/hc-precheck.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.main([str(args.hashes), "--mode", str(args.mode), "--json"])


def extra_arguments(text):
    tokens = shlex.split(text)
    flags = {"-O", "--optimized-kernel-enable", "--quiet", "--status", "--backend-ignore-opencl"}
    valued = {"-w", "--workload-profile", "--runtime", "--status-timer"}
    i = 0
    while i < len(tokens):
        if tokens[i] in flags:
            i += 1
        elif tokens[i] in valued and i + 1 < len(tokens) and tokens[i + 1].isdigit():
            i += 2
        else:
            raise ClientError("unsupported extra argument; use -O, -w N, --runtime N, --quiet, --status, --status-timer N or --backend-ignore-opencl")
    return tokens


def safe_remote(path):
    if not path.startswith("/") or any(c in path for c in "\r\n\0") or ".." in PurePosixPath(path).parts:
        raise ClientError("remote path must be absolute without traversal/control characters")
    return path.rstrip("/")


def wall_seconds(value):
    h, m, s = map(int, value.split(":"))
    return h * 3600 + m * 60 + s


def make_plan(args):
    conf = profile(args.cluster)
    attack = args.attack or ("3" if args.mask else "1" if args.rules else "0")
    if args.mode < 0:
        raise ClientError("--mode must be non-negative")
    if attack == "3":
        if not args.mask or args.dict or args.rules or args.nodes != 1:
            raise ClientError("mask attack requires --mask, --nodes 1, and no dictionary/rules")
    elif not args.dict or args.mask or (attack == "1" and not args.rules):
        raise ClientError("dictionary/rules attack requires --dict; --attack 1 also requires --rules")
    if args.dcus_per_node > int(conf["ACCEL_PER_NODE"]) or args.cpus_per_node > int(conf["CPUS_PER_NODE"]):
        raise ClientError("requested per-node resources exceed the selected profile")
    walltime = args.walltime or "00:10:00"
    if not re.fullmatch(r"\d+:([0-5]\d):([0-5]\d)", walltime) or wall_seconds(walltime) < 1:
        raise ClientError("walltime must be a positive HH:MM:SS")
    for path in (args.hashes, args.dict, args.rules):
        if path and (not path.is_file() or path.stat().st_size == 0):
            raise ClientError("input is missing or empty: " + str(path))
    if not args.skip_precheck and precheck(args):
        raise ClientError("hash file rejected by precheck")
    region = args.region or default_region() or conf.get("OPENAPI_REGION_ID")
    if not region:
        raise ClientError("select exactly one --region or configure scnet-hpc")
    name = args.name or ("hc-" + time.strftime("%Y%m%d-%H%M%S"))
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}", name):
        raise ClientError("--name must be a simple job label")
    queue = args.queue or conf["PARTITION"]
    selected_module = args.module or conf["HASHCAT_MODULE"]
    signature = conf.get("STACK_SIGNATURE")
    stack_id = conf.get("STACK_ID")
    if args.module and args.module != conf["HASHCAT_MODULE"]:
        signature, stack_id = None, None
    elif signature:
        signature = json.loads(json.dumps(signature))
        signature["platform"] = {
            **signature.get("platform", {}),
            "adapter": "scnet-openapi",
            "region": str(region),
            "cluster": args.cluster,
            "queue": queue,
        }
    return {"cluster": args.cluster, "region_id": str(region), "queue": queue,
            "name": name, "nodes": args.nodes, "cpus_per_node": args.cpus_per_node,
            "cpus": args.nodes * args.cpus_per_node, "dcus_per_node": args.dcus_per_node,
            "walltime": walltime, "attack": attack, "mode": args.mode, "mask": args.mask,
            "module": selected_module, "modulefiles": args.modulefiles,
            "extra_args": extra_arguments(args.extra_args),
            "stack_id": stack_id,
            "stack_signature": signature,
            "stack_status": "reference" if signature else "unverified",
            "precheck": {"skipped": bool(args.skip_precheck)},
            "work_base": safe_remote(args.work_dir) if args.work_dir else "<remote-home>/hashcat-runs",
            "input_roles": {k: str(v.resolve()) for k, v in {"hashes": args.hashes, "dict": args.dict, "rules": args.rules}.items() if v}}


def live_preflight(client, plan):
    region = plan["region_id"]
    ctx = client.hpc_context(region)
    queue = next((q for q in client.queues(region) if q["partition"] == plan["queue"]), None)
    if queue is None:
        raise ClientError("queue not available in the selected region")
    for field, requested in (("max_nodes", plan["nodes"]), ("max_cpus_per_node", plan["cpus_per_node"]), ("max_dcus_per_node", plan["dcus_per_node"]), ("max_walltime", wall_seconds(plan["walltime"]))):
        limit = str(queue.get(field) or "")
        if limit.isdigit() and int(limit) > 0 and requested > int(limit):
            raise ClientError("requested resources exceed live queue " + field)
    limits = client.limits(region)
    for field, requested in (("user_max_nodes", plan["nodes"]), ("user_max_cpus", plan["cpus"]), ("user_max_dcus", plan["nodes"] * plan["dcus_per_node"])):
        maximum = str(limits.get(field) or "")
        if maximum.isdigit() and requested > int(maximum):
            raise ClientError("requested resources exceed live quota " + field)
    account = client.account(region)
    emit({"preflight": {"region_id": region, "queue": queue, "limits": limits,
                        "account_status": account.get("account_status"), "balance": account.get("balance")}})
    home = (ctx["center"].get("clusterUserInfo") or {}).get("homePath")
    if not home:
        raise ClientError("remote home directory not available")
    return safe_remote(home)


def remote_command(plan, run_dir, roles):
    argv = ["bash", "-l", run_dir + "/hc-node.sh", "--hashes", roles["hashes"],
            "--attack", plan["attack"], "--mode", str(plan["mode"]), "--nodes", str(plan["nodes"]),
            "--module", plan["module"], "--outdir", run_dir + "/results", "--expected-devices", str(plan["dcus_per_node"])]
    for role in ("dict", "rules"):
        if role in roles:
            argv += ["--" + role, roles[role]]
    for key in ("mask", "modulefiles"):
        if plan.get(key):
            argv += ["--" + key, plan[key]]
    for extra in plan["extra_args"]:
        argv += ["--extra", extra]
    return shlex.join(argv)


def crack(client, args):
    plan = make_plan(args)
    emit({"plan": plan, "dry_run": args.dry_run})
    if args.dry_run:
        return 0
    home = live_preflight(client, plan)
    region = plan["region_id"]
    base = plan["work_base"].replace("<remote-home>", home)
    run_dir = safe_remote(base) + "/" + plan["name"] + "-" + uuid.uuid4().hex[:12]
    plan["run_dir"] = run_dir
    plan["modulefiles"] = plan["modulefiles"] or home + "/modulefiles"
    roles = {role: run_dir + "/inputs/" + role + "/" + Path(path).name for role, path in plan["input_roles"].items()}
    plan["remote_inputs"] = roles
    client.mkdir(run_dir + "/results", region)
    for role, local in plan["input_roles"].items():
        dest = run_dir + "/inputs/" + role
        client.mkdir(dest, region)
        client.upload(local, dest, region, chunk_size=8 * 1024 * 1024)
    for name in ("hc-node.sh", "hc-common.sh"):
        client.upload(str(ROOT / "scripts/remote" / name), run_dir, region)
    with tempfile.TemporaryDirectory(prefix="scnet-hashcat-") as tmp:
        manifest = Path(tmp) / "run.json"
        manifest.write_text(json.dumps(plan, indent=2), encoding="utf-8")
        client.upload(str(manifest), run_dir, region)
    result = client.submit({"region": region, "name": plan["name"], "queue": plan["queue"],
                            "nodes": plan["nodes"], "cpus": plan["cpus"], "dcus": plan["dcus_per_node"],
                            "walltime": plan["walltime"], "work_dir": run_dir,
                            "command": remote_command(plan, run_dir, roles)})
    job_id = result["job_id"]
    emit({"job_id": job_id, "region_id": region, "run_dir": run_dir,
          "status": f"hc status {job_id} --region {region}", "collect": f"hc collect {job_id} --region {region}",
          "cancel": f"hc cancel {job_id} --region {region}"})
    if args.wait:
        client.wait(job_id, region, interval=10, timeout=args.wait_timeout)
        return collect(client, job_id, region, Path("hc-out-" + job_id))
    return 0


def result_report(job_id, job, manifest, summary, out):
    entries = set()
    for path in out.glob("pot.*"):
        if re.fullmatch(r"pot\.\d+", path.name):
            entries.update(line for line in path.read_bytes().splitlines() if line)
    (out / "pot.merged").write_bytes(b"\n".join(sorted(entries)) + (b"\n" if entries else b""))
    expected = int(manifest["nodes"])
    ranks = summary.get("ranks", [])
    ranks_ok = (sorted(r.get("rank") for r in ranks) == list(range(expected))
                and all(r.get("hashcat_rc") in (0, 1) and not r.get("error") for r in ranks)
                and summary.get("fanout_rc", 0) == 0)
    scheduler_ok = job["state"] == "COMPLETED" and str(job.get("exit_code")) in ("None", "0", "0:0") and str(job.get("platform_exit_status")) in ("None", "", "0")
    hashes = set(line.strip() for line in (out / "hashes.txt").read_bytes().splitlines() if line.strip())
    cracked_hashes = set()
    for path in out.glob("cracked.*"):
        if re.fullmatch(r"cracked\.\d+", path.name):
            cracked_hashes.update(line for line in path.read_bytes().splitlines() if line)
    cracked = len(hashes & cracked_hashes)
    report = {"job_id": job_id, "region_id": manifest["region_id"], "scheduler_state": job["state"],
              "ok": bool(scheduler_ok and ranks_ok), "expected_ranks": expected, "reported_ranks": len(ranks),
              "cracked": cracked, "total_hashes": len(hashes), "remaining": len(hashes) - cracked,
              "count_basis": "unique input lines matched to outfile-format 1; format normalization may undercount",
              "pot_entries": len(entries)}
    (out / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def collect(client, job_id, region, out, cover=False):
    if out.exists() and any(out.iterdir()) and not cover:
        raise ClientError("output directory is not empty; select a new --out or pass --cover")
    out.mkdir(parents=True, exist_ok=True)
    artifact = r"(?:summary\.json|hc-node\.log|(?:pot|cracked)\.\d+|rank\.\d+\.(?:kv|log)|devices\.\d+\.txt)"
    if cover:
        for path in out.iterdir():
            if path.is_file() and re.fullmatch(artifact, path.name):
                path.unlink()
    job = client.job(job_id, region)
    work = safe_remote(job.get("work_dir") or "")
    client.download(work + "/run.json", str(out / "run.json"), region, cover=True)
    manifest = json.loads((out / "run.json").read_text(encoding="utf-8"))
    if str(manifest["region_id"]) != str(region) or manifest["run_dir"] != work:
        raise ClientError("run manifest target does not match the selected job")
    for item in client.ls(work + "/results", region).get("files", []):
        name = item["name"]
        if re.fullmatch(artifact, name):
            client.download(work + "/results/" + name, str(out / name), region, cover=True)
    client.download(manifest["remote_inputs"]["hashes"], str(out / "hashes.txt"), region, cover=True)
    for field, name in (("stdout", "std.out"), ("stderr", "std.err")):
        if job.get(field):
            try:
                client.download(job[field], str(out / name), region, cover=True)
            except ClientError:
                pass
    path = out / "summary.json"
    summary = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    report = result_report(job_id, job, manifest, summary, out)
    emit({"report": report, "output_dir": str(out.resolve())})
    return 0 if report["ok"] else 1


def main(argv=None):
    args = parser().parse_args(argv)
    client = Client()
    try:
        if args.op == "version":
            print("hc " + VERSION)
        elif args.op == "precheck":
            return precheck(args)
        elif args.op == "split":
            args.outdir.mkdir(parents=True, exist_ok=True)
            if any(args.outdir.iterdir()):
                raise ClientError("split output directory must be empty")
            import contextlib
            with contextlib.ExitStack() as stack:
                files = [stack.enter_context((args.outdir / f"part.{i:03}").open("wb")) for i in range(args.parts)]
                with args.input.open("rb") as source:
                    for i, line in enumerate(source):
                        files[i % args.parts].write(line if line.endswith(b"\n") else line + b"\n")
            print(f"split into {args.parts} parts under {args.outdir}")
        elif args.op == "crack":
            return crack(client, args)
        else:
            region = args.region or default_region() or profile(args.cluster).get("OPENAPI_REGION_ID")
            if args.op == "doctor":
                ctx = client.hpc_context(region)
                emit({"ok": True, "region_id": ctx["region"].get("clusterId"), "queues": client.queues(region), "limits": client.limits(region)})
            elif args.op == "status":
                emit({k: v for k, v in client.job(args.job_id, region).items() if k != "raw"})
            elif args.op == "cancel":
                emit(client.cancel(args.job_id, region))
            elif args.op == "collect":
                return collect(client, args.job_id, region, args.out or Path("hc-out-" + args.job_id), args.cover)
        return 0
    except (ClientError, OSError, ValueError, KeyError) as exc:
        print("hc: error: " + str(exc), file=sys.stderr)
        if args.op == "doctor":
            print(
                "hc: first use: see references/first-use.md; check account/resource "
                "activation, credentials, region/queue and module deployment separately",
                file=sys.stderr,
            )
        return 1


if __name__ == "__main__":
    sys.exit(main())
