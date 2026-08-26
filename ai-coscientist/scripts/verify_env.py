#!/usr/bin/env python3
"""Verify that this machine can actually train.

Driver-level checks are not sufficient on Blackwell (sm_120): nvidia-smi can be
healthy and torch.cuda.is_available() can return True while no compiled kernel
exists for the device. That failure only surfaces when a kernel launches. This
script therefore runs real compute -- a matmul and a backward pass -- and treats
those, not the reported capability, as the decisive test.

Usage:  python scripts/verify_env.py
Exit:   0 = ready to train, 1 = problem found, 2 = torch not installed.

Prints a report block intended to be pasted back into the project discussion.
"""

from __future__ import annotations

import os
import platform
import sys

SM_BLACKWELL = (12, 0)
LINE = "-" * 68

checks: list[tuple[str, bool | None, str]] = []


def record(name: str, ok: bool | None, detail: str = "") -> None:
    checks.append((name, ok, detail))
    mark = {True: "PASS", False: "FAIL", None: "INFO"}[ok]
    print(f"  [{mark}] {name}" + (f": {detail}" if detail else ""))


def section(title: str) -> None:
    print(f"\n{title}\n{LINE}")


def detect_wsl() -> bool:
    try:
        with open("/proc/version") as fh:
            return "microsoft" in fh.read().lower()
    except OSError:
        return False


def main() -> int:
    print(f"\n{LINE}\n AI Co-Scientist -- environment verification\n{LINE}")

    section("Platform")
    record("Python", sys.version_info >= (3, 10),
           f"{platform.python_version()} ({sys.executable})")
    record("OS", None, f"{platform.system()} {platform.release()}")
    if platform.system() == "Linux":
        record("WSL2", None, "yes" if detect_wsl() else "no (native Linux)")
    elif platform.system() == "Windows":
        record("WSL2", None, "running native Windows -- WSL2 recommended (see docs/ENVIRONMENT.md)")

    section("PyTorch")
    try:
        import torch
    except ImportError:
        record("torch installed", False, "not found -- see docs/ENVIRONMENT.md")
        print("\nRESULT: torch missing. Install it, then re-run.\n")
        return 2

    record("torch installed", True, torch.__version__)
    built_cuda = getattr(torch.version, "cuda", None)
    record("built against CUDA", built_cuda is not None, str(built_cuda))

    if not torch.cuda.is_available():
        record("CUDA available", False, "torch cannot see a GPU")
        print("\nRESULT: no GPU visible to torch. CPU-only work is possible "
              "(Phases 1-2), but training is not.\n")
        return 1
    record("CUDA available", True)

    section("Device")
    idx = torch.cuda.current_device()
    props = torch.cuda.get_device_properties(idx)
    cap = torch.cuda.get_device_capability(idx)
    vram_gb = props.total_memory / (1024 ** 3)

    record("device", None, props.name)
    record("compute capability", None, f"sm_{cap[0]}{cap[1]}")
    record("VRAM", None, f"{vram_gb:.1f} GB")

    arch_list = torch.cuda.get_arch_list()
    arch_tag = f"sm_{cap[0]}{cap[1]}"
    has_arch = arch_tag in arch_list
    if cap >= SM_BLACKWELL:
        record(f"{arch_tag} kernels in this build", has_arch,
               "" if has_arch else f"build has: {', '.join(arch_list)}")

    section("Real compute (the decisive test)")
    try:
        a = torch.randn(2048, 2048, device="cuda")
        b = torch.randn(2048, 2048, device="cuda")
        torch.cuda.synchronize()
        record("allocate + matmul", True, f"{(a @ b).shape}")
    except RuntimeError as exc:
        record("allocate + matmul", False, str(exc).splitlines()[0])
        print("\nRESULT: kernels will not launch on this device. This is the "
              "Blackwell failure mode -- the torch build lacks kernels for "
              f"{arch_tag}. Reinstall against a newer CUDA (docs/ENVIRONMENT.md).\n")
        return 1

    try:
        w = torch.randn(512, 512, device="cuda", requires_grad=True)
        loss = (torch.randn(64, 512, device="cuda") @ w).sum()
        loss.backward()
        torch.cuda.synchronize()
        record("backward pass", w.grad is not None and torch.isfinite(w.grad).all().item())
    except RuntimeError as exc:
        record("backward pass", False, str(exc).splitlines()[0])
        return 1

    for dtype, label in ((torch.bfloat16, "bfloat16"), (torch.float16, "float16")):
        try:
            x = torch.randn(512, 512, device="cuda", dtype=dtype)
            torch.cuda.synchronize()
            _ = x @ x
            torch.cuda.synchronize()
            record(f"{label} matmul", True)
        except RuntimeError as exc:
            record(f"{label} matmul", False, str(exc).splitlines()[0])

    section("Throughput (baseline for comparing rented cards)")
    try:
        import time
        n, iters = 4096, 20
        x = torch.randn(n, n, device="cuda", dtype=torch.bfloat16)
        for _ in range(3):
            _ = x @ x
        torch.cuda.synchronize()
        t0 = time.perf_counter()
        for _ in range(iters):
            _ = x @ x
        torch.cuda.synchronize()
        secs = (time.perf_counter() - t0) / iters
        record("bf16 matmul", None, f"{(2 * n ** 3) / secs / 1e12:.1f} TFLOP/s")
    except RuntimeError as exc:
        record("throughput", None, f"skipped ({str(exc).splitlines()[0]})")

    free, total = torch.cuda.mem_get_info()
    record("VRAM free now", None, f"{free / 1024 ** 3:.1f} / {total / 1024 ** 3:.1f} GB")

    section("Verdict")
    failed = [name for name, ok, _ in checks if ok is False]
    if failed:
        print(f"  NOT READY -- failed: {', '.join(failed)}\n")
        return 1

    print("  READY. Kernels launch and gradients flow on this device.")
    if vram_gb < 12:
        print(f"  Note: {vram_gb:.0f} GB VRAM suits development, debugging, and")
        print("  overfit-one-batch tests. Training runs go to Vast.ai (D-013).")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
