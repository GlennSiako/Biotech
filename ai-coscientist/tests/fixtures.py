"""Synthetic structures containing the messes real PDB entries contain.

Built rather than downloaded so the test suite runs offline and deterministically.
"""

from __future__ import annotations


def _atom(serial: int, name: str, resname: str, chain: str, resseq: int,
          xyz: tuple[float, float, float], *, altloc: str = " ",
          occupancy: float = 1.00, record: str = "ATOM", element: str = "C") -> str:
    x, y, z = xyz
    return (f"{record:<6}{serial:>5} {name:^4}{altloc}{resname:>3} {chain}"
            f"{resseq:>4}    {x:>8.3f}{y:>8.3f}{z:>8.3f}"
            f"{occupancy:>6.2f}{0.0:>6.2f}          {element:>2}")


def build_pdb() -> str:
    """A structure with: two models, a chain break, altlocs, waters, hetero,
    and a second chain that must not leak into the prepared output."""
    lines: list[str] = []
    serial = 1

    def residue(resname, chain, resseq, *, altloc=" ", occupancy=1.00,
                record="ATOM", element="C"):
        nonlocal serial
        for i, name in enumerate(("N", "CA", "C", "O")):
            lines.append(_atom(serial, name, resname, chain, resseq,
                               (float(resseq), float(i), 0.0), altloc=altloc,
                               occupancy=occupancy, record=record,
                               element="N" if name == "N" else element))
            serial += 1

    for model in (1, 2):
        lines.append(f"MODEL     {model:>4}")
        # Chain A: residues 10-12, then a break, then 16-17.
        for resseq in (10, 11, 12):
            residue("ALA", "A", resseq)
        # Residue 16 modelled in two alternate conformations.
        residue("SER", "A", 16, altloc="A", occupancy=0.65)
        residue("SER", "A", 16, altloc="B", occupancy=0.35)
        residue("GLY", "A", 17)
        # A second protein chain -- a binding partner, not our target.
        for resseq in (5, 6):
            residue("LEU", "B", resseq)
        # Heteroatoms: a ligand and two waters.
        lines.append(_atom(serial, "C1", "GOL", "A", 201, (1.0, 1.0, 1.0),
                           record="HETATM", element="C")); serial += 1
        for i, resseq in enumerate((301, 302)):
            lines.append(_atom(serial, "O", "HOH", "A", resseq,
                               (2.0 + i, 2.0, 2.0), record="HETATM", element="O"))
            serial += 1
        lines.append("ENDMDL")

    lines.append("END")
    return "\n".join(lines) + "\n"


UNIPROT_PAYLOAD = {
    "results": [
        {
            "primaryAccession": "Q9NZQ7",
            "uniProtkbId": "PD1L1_HUMAN",
            "proteinDescription": {
                "recommendedName": {"fullName": {"value": "Programmed cell death 1 ligand 1"}}
            },
            "genes": [{"geneName": {"value": "CD274"}}],
            "organism": {"scientificName": "Homo sapiens", "taxonId": 9606},
            "sequence": {"value": "MRIFAVFIFMTYWHLLNA", "length": 290},
            "uniProtKBCrossReferences": [
                {"database": "PDB", "id": "4zqk", "properties": [
                    {"key": "Method", "value": "X-ray"},
                    {"key": "Resolution", "value": "2.45 A"},
                    {"key": "Chains", "value": "B=18-134"}]},
                {"database": "PDB", "id": "3BIK", "properties": [
                    {"key": "Method", "value": "X-ray"},
                    {"key": "Resolution", "value": "2.65 A"},
                    {"key": "Chains", "value": "A=18-239"}]},
                {"database": "PDB", "id": "2K9Z", "properties": [
                    {"key": "Method", "value": "NMR"},
                    {"key": "Resolution", "value": "-"},
                    {"key": "Chains", "value": "A=18-134"}]},
                {"database": "AlphaFoldDB", "id": "Q9NZQ7", "properties": []},
            ],
        }
    ]
}
