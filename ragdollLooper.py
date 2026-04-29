import maya.cmds as cmds


class LoopRobeInPlaceTool(object):
    WINDOW = "loopRobeInPlaceToolWin"

    def __init__(self):
        self.blend_field = None

    def show(self):
        if cmds.window(self.WINDOW, exists=True):
            cmds.deleteUI(self.WINDOW)

        self.WINDOW = cmds.window(
            self.WINDOW,
            title="Loop Ragdoll Animation",
            sizeable=True,
            widthHeight=(100, 50)
        )
        cmds.columnLayout(adjustableColumn=True, rowSpacing=8)
        cmds.separator(h=8, style="in")

        self.blend_field = cmds.intFieldGrp(
            label="Blend Frames",
            numberOfFields=1,
            value1=10
        )

        cmds.separator(h=8, style="in")

        cmds.button(
            label="Create Seamless Loop",
            h=35,
            command=lambda *_: self.create_loop()
        )

        cmds.showWindow(self.WINDOW)

    def find_robe_controls(self):
        """
        Find transform nodes with 'robe' in the name that have keyed animation.
        """
        results = []
        all_transforms = cmds.ls(type="transform", long=True) or []

        for node in all_transforms:
            short_name = node.split("|")[-1].lower()
            if "robe" not in short_name:
                continue

            animatable = cmds.listAnimatable(node) or []
            has_keys = False

            for attr in animatable:
                try:
                    curves = cmds.keyframe(attr, q=True, name=True)
                    if curves:
                        has_keys = True
                        break
                except Exception:
                    pass

            if has_keys:
                results.append(node)

        return sorted(list(set(results)))

    def get_keyed_attrs(self, nodes):
        """
        Return keyed animatable attrs in node.attr form.
        """
        attrs = []

        for node in nodes:
            animatable = cmds.listAnimatable(node) or []
            for attr in animatable:
                try:
                    curves = cmds.keyframe(attr, q=True, name=True)
                    if curves:
                        attrs.append(attr)
                except Exception:
                    pass

        return sorted(list(set(attrs)))

    def get_value(self, attr, frame):
        try:
            return cmds.getAttr(attr, time=frame)
        except Exception:
            return None

    def set_value_key(self, attr, frame, value):
        try:
            cmds.setKeyframe(attr, t=frame, v=value)
        except Exception:
            pass

    def blend_last_frames_to_start(self, attrs, loop_start=1, loop_end=34, blend_frames=10):

        blend_start = loop_end - blend_frames + 1

        for attr in attrs:
            for i in range(blend_frames):
                target_frame = blend_start + i
                source_frame = loop_start + (blend_frames - 1 - i)

                current_val = self.get_value(attr, target_frame)
                source_val = self.get_value(attr, source_frame)

                if current_val is None or source_val is None:
                    continue

                # Progressively blend more strongly toward the source as we approach frame 34
                alpha = float(i + 1) / float(blend_frames)
                new_val = ((1.0 - alpha) * current_val) + (alpha * source_val)

                # Force the very last frame to equal frame 1 exactly
                if target_frame == loop_end:
                    frame1_val = self.get_value(attr, loop_start)
                    if frame1_val is not None:
                        new_val = frame1_val

                self.set_value_key(attr, target_frame, new_val)

            try:
                cmds.keyTangent(attr, time=(blend_start, loop_end), itt="auto", ott="auto")
            except Exception:
                pass

    def create_loop(self):
        loop_start = int(cmds.playbackOptions(q=True, min=True))
        loop_end = int(cmds.playbackOptions(q=True, max=True))
        blend_frames = cmds.intFieldGrp(self.blend_field, q=True, value1=True)

        if blend_frames < 2:
            cmds.warning("Blend Frames must be at least 2.")
            return

        total_frames = loop_end - loop_start + 1
        if blend_frames > total_frames:
            "Blend Frames cannot be longer than the loop range {}-{}.".format(loop_start, loop_end)
            return

        robe_controls = self.find_robe_controls()
        if not robe_controls:
            cmds.warning("No animated transforms with 'robe' in the name were found.")
            return

        attrs = self.get_keyed_attrs(robe_controls)
        if not attrs:
            cmds.warning("No keyed attributes found on robe controls.")
            return

        print("Found robe controls:")
        for ctrl in robe_controls:
            print("  {}".format(ctrl))

        cmds.undoInfo(openChunk=True)
        try:
            self.blend_last_frames_to_start(
                attrs=attrs,
                loop_start=loop_start,
                loop_end=loop_end,
                blend_frames=blend_frames
            )

            # Keep playback range fixed at 1-34
            cmds.playbackOptions(
                min=loop_start,
                animationStartTime=loop_start,
                max=loop_end,
                animationEndTime=loop_end
            )

            try:
                cmds.filterCurve(attrs)
            except Exception:
                pass

            cmds.inViewMessage(
                amg='Robe loop updated. Range stays <hl>{}-{}</hl>. Frame <hl>{}</hl> now matches frame <hl>{}</hl>.'.format(
                    loop_start, loop_end, loop_end, loop_start
                ),
                pos='midCenterTop',
                fade=True
            )

            print("Loop created successfully.")
            print("Last {} frames were blended back into the start.".format(blend_frames))

        finally:
            cmds.undoInfo(closeChunk=True)

def ragdollLoop():
    tool = LoopRobeInPlaceTool()
    tool.show()

ragdollLoop()