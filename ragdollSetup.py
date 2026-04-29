from maya import cmds
from ragdoll import interactive as ri
from ragdoll import api as rd

ri.install()

def ragdollCreation():

    # Stop if there is not exactly one Char_Rig
    char_rigs = cmds.ls("Char_Rig", type="transform") or []

    if len(char_rigs) != 1:
        cmds.confirmDialog(
            title="Ragdoll Setup Skipped",
            message="Expected exactly one Char_Rig.\nFound: {}".format(len(char_rigs)),
            button=["OK"]
        )
        return

    # Stop if Ragdoll already exists under Char_Rig
    char_rig = cmds.ls("Char_Rig", type="transform", long=True)[0]
    ragdoll_path = char_rig + "|Ragdoll"

    if cmds.objExists(ragdoll_path):
        cmds.confirmDialog(
            title="Ragdoll Setup Skipped",
            message="Ragdoll already exists under Char_Rig.",
            button=["OK"]
        )
        return

    chains = [
        ["body_C0_ctrl", "robeFront_L0_ctrl", "robeFront_L1_ctrl", "robeFront_L2_ctrl", "robeFront_L3_ctrl"],
        ["body_C0_ctrl", "robeFront_R0_ctrl", "robeFront_R1_ctrl", "robeFront_R2_ctrl", "robeFront_R3_ctrl"],
        ["body_C0_ctrl", "robeBack_L0_ctrl",  "robeBack_L1_ctrl",  "robeBack_L2_ctrl",  "robeBack_L3_ctrl"],
        ["body_C0_ctrl", "robeBack_R0_ctrl",  "robeBack_R1_ctrl",  "robeBack_R2_ctrl",  "robeBack_R3_ctrl"],
    ]

    top_leg_colliders = [
        "leg_R0_thigh_jnt_bind",
        "leg_L0_thigh_jnt_bind",
    ]

    bottom_leg_colliders = [
        "leg_R0_calf_jnt_bind",
        "leg_L0_calf_jnt_bind",
    ]

    collider_joints = top_leg_colliders + bottom_leg_colliders

    hair_joints = ["hair1_C0_ctrl", "hair2_C0_ctrl", "hair3_C0_ctrl"]

    def get_first_marker(ctrl):
        markers = cmds.listConnections(ctrl, type="rdMarker") or []
        if not markers:
            print("No marker found for:", ctrl)
            return None
        return markers[0]

    def create_distance_constraint(marker_a, marker_b):
        cmds.select(clear=True)
        cmds.select([marker_a, marker_b], replace=True, noExpand=True)

        if hasattr(ri, "distance_constraint"):
            return ri.distance_constraint()

        if hasattr(ri, "create_distance_constraint"):
            return ri.create_distance_constraint()

        if hasattr(ri, "create_distance"):
            return ri.create_distance()

        raise RuntimeError("Could not find a Ragdoll distance constraint command.")

    # Assign and connect chains for robe
    for chain in chains:
        if all(cmds.objExists(x) for x in chain):
            cmds.select(chain, r=True)
            ri.assign_and_connect()
        else:
            print("Can't find controls for chain:", chain)

    cmds.select(clear=True)

    # Make robe chain markers use box shape and adjust extents
    for chain in chains:
        for ctrl in chain:
            markers = cmds.listConnections(ctrl, type="rdMarker") or []
            for m in markers:
                if cmds.objExists(m + ".shapeType"):
                    cmds.setAttr(m + ".shapeType", 0)
                if cmds.objExists(m + ".shapeExtentsZ"):
                    cmds.setAttr(m + ".shapeExtentsZ", 8)
                if cmds.objExists(m + ".shapeExtentsY"):
                    cmds.setAttr(m + ".shapeExtentsY", 0.5)

    # Prevent twisted marker orientation
    for chain in chains:
        top_markers = cmds.listConnections(chain[0], type="rdMarker") or []

        if not top_markers:
            continue

        top_marker = top_markers[0]

        if not cmds.objExists(top_marker + ".shapeRotationX"):
            continue

        top_rx = cmds.getAttr(top_marker + ".shapeRotationX")

        for ctrl in chain[1:]:
            markers = cmds.listConnections(ctrl, type="rdMarker") or []
            for m in markers:
                if cmds.objExists(m + ".shapeRotationX"):
                    cmds.setAttr(m + ".shapeRotationX", top_rx)

    # Fix back robe marker shape orientation
    back_chains = [chains[2], chains[3]]

    for chain in back_chains:
        for ctrl in chain[1:]:  # skip body_C0_ctrl
            markers = cmds.listConnections(ctrl, type="rdMarker") or []
            for m in markers:
                if cmds.objExists(m + ".shapeRotationX"):
                    cmds.setAttr(m + ".shapeRotationX", 90)

    # Robe marker friction
    side_robe_ctrls = [
        "robeFront_L0_ctrl", "robeFront_L1_ctrl", "robeFront_L2_ctrl", "robeFront_L3_ctrl",
        "robeFront_R0_ctrl", "robeFront_R1_ctrl", "robeFront_R2_ctrl", "robeFront_R3_ctrl",
    ]

    back_robe_ctrls = [
        "robeBack_L0_ctrl", "robeBack_L1_ctrl", "robeBack_L2_ctrl", "robeBack_L3_ctrl",
        "robeBack_R0_ctrl", "robeBack_R1_ctrl", "robeBack_R2_ctrl", "robeBack_R3_ctrl",
    ]

    for ctrl in side_robe_ctrls:
        markers = cmds.listConnections(ctrl, type="rdMarker") or []
        for marker in markers:
            if cmds.objExists(marker + ".friction"):
                cmds.setAttr(marker + ".friction", 0.6)

    for ctrl in back_robe_ctrls:
        markers = cmds.listConnections(ctrl, type="rdMarker") or []
        for marker in markers:
            if cmds.objExists(marker + ".friction"):
                cmds.setAttr(marker + ".friction", 1.0)

    # Find solver
    solvers = cmds.ls(type="rdSolver")
    if not solvers:
        raise RuntimeError("No rdSolver found in the scene.")

    solver = solvers[0]

    # Change solver settings to stable and custom start time
    for attr, value in [
        ("solverType", 0),   # Stable
        ("startTime", 2),    # Custom (enum)
    ]:
        if cmds.objExists(solver + "." + attr):
            print(attr, "enum:", cmds.attributeQuery(attr, node=solver, listEnum=True))
            cmds.setAttr(solver + "." + attr, value)
            print("Set", solver + "." + attr, "to", value)

    # Set the custom start frame
    if cmds.objExists(solver + ".customStartTime"):
        cmds.setAttr(solver + ".customStartTime", -30)
        print("Set customStartTime to -30")

    # Set scene playback preroll to -30
    cmds.playbackOptions(min=-30)
    cmds.playbackOptions(animationStartTime=-30)

    # Create one shared group for all leg colliders
    collider_group = rd.createGroup(solver)

    # Set collider group to Animated
    if cmds.objExists(collider_group + ".inputType"):
        cmds.setAttr(collider_group + ".inputType", 2)

    # Assign leg collider markers into the group
    existing_colliders = [j for j in collider_joints if cmds.objExists(j)]

    if existing_colliders:
        cmds.select(existing_colliders, r=True)
        ri.assign_marker()
    else:
        print("No collider joints found.")

    # Set collider groups to Animated
    for joint in collider_joints:
        markers = cmds.listConnections(joint, type="rdMarker") or []

        for marker in markers:
            groups = cmds.listConnections(marker, type="rdGroup") or []

            for grp in groups:
                if cmds.objExists(grp + ".inputType"):
                    cmds.setAttr(grp + ".inputType", 2)

    # Top leg colliders: capsule, radius 3.5
    for joint in top_leg_colliders:
        markers = cmds.listConnections(joint, type="rdMarker") or []

        for marker in markers:
            if cmds.objExists(marker + ".shapeType"):
                cmds.setAttr(marker + ".shapeType", 2)  # capsule

            if cmds.objExists(marker + ".shapeRadius"):
                cmds.setAttr(marker + ".shapeRadius", 3.5)

    # Bottom leg colliders: box shape, extents, offsets, friction
    for joint in bottom_leg_colliders:
        markers = cmds.listConnections(joint, type="rdMarker") or []

        for marker in markers:
            if cmds.objExists(marker + ".shapeType"):
                cmds.setAttr(marker + ".shapeType", 0)  # box

            if cmds.objExists(marker + ".shapeExtentsX"):
                cmds.setAttr(marker + ".shapeExtentsX", 25.076)

            if cmds.objExists(marker + ".shapeExtentsY"):
                cmds.setAttr(marker + ".shapeExtentsY", 7)

            if cmds.objExists(marker + ".shapeExtentsZ"):
                cmds.setAttr(marker + ".shapeExtentsZ", 8)

            if cmds.objExists(marker + ".friction"):
                cmds.setAttr(marker + ".friction", 0.6)

            if joint.startswith("leg_R") and cmds.objExists(marker + ".shapeOffsetX"):
                cmds.setAttr(marker + ".shapeOffsetX", 12.5)

            if joint.startswith("leg_L") and cmds.objExists(marker + ".shapeOffsetX"):
                cmds.setAttr(marker + ".shapeOffsetX", -12.5)

            if joint.startswith("leg_R") and cmds.objExists(marker + ".shapeOffsetZ"):
                cmds.setAttr(marker + ".shapeOffsetZ", -1)

            if joint.startswith("leg_L") and cmds.objExists(marker + ".shapeOffsetZ"):
                cmds.setAttr(marker + ".shapeOffsetZ", 1)

    # body_C0_ctrl rGroups: rotate stiffness 0.5, rotate damping 1

    groups = set()

    # From marker connections (reliable)
    for marker in cmds.listConnections("body_C0_ctrl", type="rdMarker") or []:
        groups.update(cmds.listConnections(marker, type="rdGroup") or [])

    # From name pattern (fallback)
    groups.update(cmds.ls("body_C0_ctrl_rGroup*", type="rdGroup") or [])

    # Apply values
    for grp in groups:
        for attr, value in [
            ("rotateStiffness", 0.01),
            ("angularStiffness", 0.01),
            ("driveAngularStiffness", 0.01),
            ("rotateDamping", 1),
            ("angularDamping", 1),
            ("driveAngularDamping", 1),
        ]:
            if cmds.objExists(grp + "." + attr):
                cmds.setAttr(grp + "." + attr, value)
                break

        print("Updated:", grp)

    # Create robe distance constraints
    constraint_pairs = [
        # Back left/right width
        ("robeBack_L1_ctrl", "robeBack_R1_ctrl"),
        ("robeBack_L2_ctrl", "robeBack_R2_ctrl"),
        ("robeBack_L3_ctrl", "robeBack_R3_ctrl"),

        # Back diagonals
        ("robeBack_L1_ctrl", "robeBack_R2_ctrl"),
        ("robeBack_R1_ctrl", "robeBack_L2_ctrl"),
        ("robeBack_L2_ctrl", "robeBack_R3_ctrl"),
        ("robeBack_R2_ctrl", "robeBack_L3_ctrl"),

        # Front to back, left side
        ("robeFront_L1_ctrl", "robeBack_L1_ctrl"),
        ("robeFront_L2_ctrl", "robeBack_L2_ctrl"),
        ("robeFront_L3_ctrl", "robeBack_L3_ctrl"),

        # Front to back, right side
        ("robeFront_R1_ctrl", "robeBack_R1_ctrl"),
        ("robeFront_R2_ctrl", "robeBack_R2_ctrl"),
        ("robeFront_R3_ctrl", "robeBack_R3_ctrl"),
    ]

    for ctrl_a, ctrl_b in constraint_pairs:
        marker_a = get_first_marker(ctrl_a)
        marker_b = get_first_marker(ctrl_b)

        if not marker_a or not marker_b:
            continue

        try:
            create_distance_constraint(marker_a, marker_b)
            print("Created distance constraint:", marker_a, marker_b)
        except Exception as e:
            print("Failed to create constraint for", ctrl_a, ctrl_b, ":", e)

    # Apply settings to all distance constraints
    #for con in cmds.ls(type="rdDistanceConstraint") or []:
    #    if cmds.objExists(con + ".method"):
    #        cmds.setAttr(con + ".method", 2)  # Maximum

    #    if cmds.objExists(con + ".minimum"):
    #        cmds.setAttr(con + ".minimum", 0)

    #    if cmds.objExists(con + ".maximum"):
    #        cmds.setAttr(con + ".maximum", 1)

    #    if cmds.objExists(con + ".stiffness"):
    #        cmds.setAttr(con + ".stiffness", 0.5)

    #    if cmds.objExists(con + ".dampingRatio"):
    #        cmds.setAttr(con + ".dampingRatio", 0.01)

    #    print("Updated constraint:", con)

    # Cleanup: Remove ground if it exists, remove extra group
    ground = cmds.ls("rGround")
    if ground:
        cmds.delete(ground)

    if cmds.objExists("rGroup"):
        cmds.delete("rGroup")

    # Create Ragdoll root
    ragdoll_root = "Ragdoll"
    if not cmds.objExists(ragdoll_root):
        cmds.group(empty=True, name=ragdoll_root)

    # Parent everything directly under Ragdoll, ordered by type
    ordered_types = [
        "rdSolver",
        "rdGroup",
        "rdMarker",
        "rdDistanceConstraint",
    ]

    for node_type in ordered_types:
        for node in cmds.ls(type=node_type) or []:
            parent = cmds.listRelatives(node, parent=True)
            if not parent:
                continue

            transform = parent[0]

            if transform == ragdoll_root:
                continue

            try:
                cmds.parent(transform, ragdoll_root)
            except:
                pass

    # Reorder children visually in the Outliner
    children = cmds.listRelatives(ragdoll_root, children=True, type="transform") or []

    ordered_children = []

    for node_type in ordered_types:
        for node in cmds.ls(type=node_type) or []:
            parent = cmds.listRelatives(node, parent=True)
            if parent and parent[0] in children:
                ordered_children.append(parent[0])

    for child in reversed(ordered_children):
        try:
            cmds.reorder(child, front=True)
        except:
            pass

    # Parent Ragdoll group under Char_Rig if it exists
    if cmds.objExists("Char_Rig"):
        try:
            cmds.parent(ragdoll_root, "Char_Rig")
        except:
            pass

    cmds.select(clear=True)
    print("Robe chains, leg colliders, and robe constraints set up")