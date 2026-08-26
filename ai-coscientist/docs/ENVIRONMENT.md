# Environment Setup

Target machine: **Windows + RTX 5070 Laptop (8GB, Blackwell `sm_120`)**, per
[D-013](DECISIONS.md). This machine is the development box; training runs go to
Vast.ai. The same environment definition must work in both places — that parity
is the point of this document.

**Verify with `python scripts/verify_env.py` and paste the output back.** Do not
trust `nvidia-smi` alone (see §6).

---

## 1. Why WSL2 rather than native Windows

- The structural biology toolchain is Linux-first; several components have no
  supported Windows path.
- Rented Vast.ai instances are Linux. Developing on WSL2 means one environment
  definition instead of two, and code that runs locally runs there unchanged.
- WDDM adds GPU memory-management overhead that WSL2's driver path avoids —
  which matters on an 8GB card.

## 2. WSL2 (run in PowerShell as Administrator)

```powershell
wsl --install -d Ubuntu-24.04
wsl --update
```

Reboot if prompted, then set up the Ubuntu user. Verify from inside WSL:

```bash
uname -r          # expect a WSL2 kernel
nvidia-smi        # should show the RTX 5070 from inside Linux
```

### The one thing that breaks this

**Do not install an NVIDIA driver inside WSL2.** The Windows driver already
provides the GPU through `/usr/lib/wsl/lib`. Installing a Linux driver inside
the distro overwrites that path and breaks CUDA in a way that is confusing to
diagnose. Install the **CUDA toolkit** if you need `nvcc` — never the driver.

If `nvidia-smi` fails inside WSL but works in Windows, update the *Windows*
driver and run `wsl --shutdown`, then reopen.

## 3. Project Python environment

```bash
sudo apt update && sudo apt install -y python3.12 python3.12-venv build-essential git
cd ~/Biotech/ai-coscientist
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

Keep the venv **inside the WSL filesystem** (`~/...`), not on `/mnt/c/`.
Cross-filesystem I/O is dramatically slower and will make data preparation
painful.

## 4. PyTorch — Blackwell requires a current build

The RTX 5070 is compute capability **`sm_120`**. Kernels for it ship only in
builds compiled against **CUDA 12.8 or later**. An older wheel will install
cleanly, report `torch.cuda.is_available() == True`, and then fail the moment a
kernel launches.

**This document deliberately does not pin a version.** Blackwell support has
been moving, and a stale pin here would be worse than no pin. Instead:

1. Go to <https://pytorch.org/get-started/locally/> and select Linux / pip /
   the **newest available CUDA** (must be ≥ 12.8).
2. Install with the index URL it gives, e.g.:
   ```bash
   pip install torch --index-url https://download.pytorch.org/whl/cu128
   ```
3. **Run `python scripts/verify_env.py`.** It launches real kernels and a
   backward pass — the only test that actually proves Blackwell support.
4. **Record the versions that passed** in §7 below, and use those exact pins on
   Vast.ai.

If verification fails at "allocate + matmul", the build lacks `sm_120` kernels:
try a newer CUDA index URL, or a nightly build.

## 5. Core dependencies

```bash
pip install -r requirements.txt
```

Structure-handling and numerical packages only. Model dependencies are added at
G1, once the architecture is settled (D-008 / D-012).

## 6. Verify

```bash
python scripts/verify_env.py
```

It reports platform, torch build, device, `sm_120` kernel availability, a real
matmul, a real backward pass, bf16/fp16 support, and a throughput number.

**Why the compute test is the decisive one.** On Blackwell, `nvidia-smi` can be
healthy and `torch.cuda.is_available()` can return `True` while the installed
build contains no kernel for the device. Nothing reveals this until a kernel
launches, at which point you get *"no kernel image is available for execution on
the device."* The script forces that moment to happen now rather than an hour
into a training run.

The throughput figure is also a baseline: it makes "is this rented card actually
faster, and by how much" a measured question later.

## 7. Verified versions

Fill in once `verify_env.py` reports READY. These pins then apply to Vast.ai
instances too, so both environments run identical code.

| Component | Version | Verified |
|-----------|---------|----------|
| Ubuntu (WSL2) | _tbd_ | _tbd_ |
| Python | _tbd_ | _tbd_ |
| PyTorch | _tbd_ | _tbd_ |
| CUDA (torch build) | _tbd_ | _tbd_ |
| NVIDIA driver (Windows) | 596.08 | 2026-08-26 |

## 8. Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `no kernel image is available for execution on the device` | torch build lacks `sm_120` | Reinstall against CUDA ≥ 12.8 (§4) |
| `nvidia-smi` works in Windows, fails in WSL | A Linux driver was installed inside WSL, or the Windows driver is stale | Never install a driver in WSL (§2); update Windows driver, `wsl --shutdown` |
| `torch.cuda.is_available()` is `False` | Stale driver, or CPU-only wheel | Check `torch.version.cuda` is not `None` |
| Out of memory at modest batch size | 8GB is genuinely small | Expected — reduce batch size and use gradient accumulation; real training belongs on Vast.ai (D-013) |
| Data preparation is extremely slow | Working under `/mnt/c/` | Move the project into the WSL filesystem (§3) |
