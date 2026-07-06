"""
mesh — the Mosaic pack CLI (a thin wrapper over the Node operations).

    mesh info                 show the current pack's manifest (no LLM)
    mesh publish              export the built graph to a .mempack        (-> export_pack)
    mesh install [pack]       install a .mempack into a fresh dataset      (-> import_pack)
    mesh uninstall [dataset]  forget an installed pack — the reversibility beat

This is the `mesh install tessera@0.1.0` command a Node operator runs.
`publish` and `install` drive Cognee (they use the LLM); `info` and `uninstall` do not.

Run:  .venv/bin/python src/mesh.py <command> [args]
"""

from dotenv import load_dotenv
load_dotenv()

import asyncio
import json
import sys
import tarfile

from config import PACK_FILE, PACK_LABEL, PACK_DATASET, IMPORTED_DATASET, INSTALL_NOTE

USAGE = "usage: mesh <info | publish | install [pack] | uninstall [dataset]>"


def cmd_info() -> int:
    """Print the built pack's manifest — no Cognee, no LLM."""
    if not PACK_FILE.exists():
        print(f"No pack artifact at {PACK_FILE}. Run 'mesh publish' (or src/build_memory.py"
              " then mesh publish) first.")
        return 0
    with tarfile.open(PACK_FILE, "r:gz") as tar:
        manifest = json.load(tar.extractfile("pack.json"))
        members = tar.getnames()
    print(f"Pack:      {manifest['label']}")
    print(f"Publisher: {manifest['publisher']}")
    print(f"License:   {manifest['license']}")
    print(f"Tier:      {manifest['verification_tier']}")
    print(f"Graph:     {manifest['counts']['nodes_total']} nodes / "
          f"{manifest['counts']['edges_total']} edges")
    print(f"Embeddings:{manifest['embeddings_included']}")
    print(f"sha256:    {manifest['content_hash']}")
    print(f"Contents:  {', '.join(members)}")
    return 0


async def cmd_publish() -> int:
    from export_pack import export
    return await export()


async def cmd_install(pack: str) -> int:
    if not PACK_FILE.exists():
        print(f"No pack artifact at {PACK_FILE}. Run 'mesh publish' first "
              "(after src/build_memory.py).")
        return 1
    from import_pack import import_pack
    print(f"Installing {pack} from {PACK_FILE.name} …")
    await import_pack(PACK_FILE, IMPORTED_DATASET)
    print("\n" + "-" * 72)
    print(INSTALL_NOTE)
    print("-" * 72)
    return 0


async def cmd_uninstall(dataset: str) -> int:
    import cognee
    result = await cognee.forget(dataset=dataset)
    print(f"Uninstalled '{dataset}':", result)
    return 0


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print(USAGE)
        return 1
    cmd, rest = args[0], args[1:]
    if cmd == "info":
        return cmd_info()
    if cmd == "publish":
        return asyncio.run(cmd_publish())
    if cmd == "install":
        return asyncio.run(cmd_install(rest[0] if rest else PACK_LABEL))
    if cmd == "uninstall":
        return asyncio.run(cmd_uninstall(rest[0] if rest else IMPORTED_DATASET))
    print(USAGE)
    return 1


if __name__ == "__main__":
    sys.exit(main())
