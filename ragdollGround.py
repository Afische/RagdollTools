from maya import cmds
from ragdoll import interactive as ri

ri.install()

def createGround():
    # Ensure a solver already exists
    solvers = cmds.ls(type="rdSolver") or []
    if not solvers:
        cmds.confirmDialog(
            title="Ragdoll Floor Skipped",
            message="No Ragdoll solver found.\nRun ragdoll setup first.",
            button=["OK"]
        )
        return

    # Create floor
    floor = cmds.polyPlane(
        name="Ragdoll_Floor",
        width=1000,
        height=1000,
        subdivisionsX=1,
        subdivisionsY=1
    )[0]

    cmds.setAttr(floor + ".translateY", 0)

    cmds.select(floor, r=True)
    ri.assign_marker()

    # Set to Animated (collider)
    markers = cmds.listConnections(floor, type="rdMarker") or []
    for marker in markers:
        if cmds.objExists(marker + ".inputType"):
            cmds.setAttr(marker + ".inputType", 2)

    # Parent under Ragdoll group
    ragdoll_grp = cmds.ls("Ragdoll", type="transform") or []

    if ragdoll_grp:
        ragdoll = ragdoll_grp[0]

        for node in ["Ragdoll_Floor", "Ragdoll_Floor_rGroup"]:
            if cmds.objExists(node):
                try:
                    cmds.parent(node, ragdoll)
                    print("Parented:", node, "under", ragdoll)
                except Exception as e:
                    print("Could not parent", node, ":", e)