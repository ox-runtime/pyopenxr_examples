"""
pyopenxr example program track_buttons.py

Prints the state of all controller buttons for 10 frames.
Demonstrates boolean (click/touch) and float (trigger/squeeze) inputs.
"""

import ctypes
import time
import xr
from xr.utils.gl import ContextObject
from xr.utils.gl.glfw_util import GLFWOffscreenContextProvider


# Interaction profile paths
PROFILES = {
    "khr": "/interaction_profiles/khr/simple_controller",
    "index": "/interaction_profiles/valve/index_controller",
    "oculus": "/interaction_profiles/oculus/touch_controller",
    "vive": "/interaction_profiles/htc/vive_controller",
    "wmr": "/interaction_profiles/microsoft/motion_controller",
}

# Component paths per profile (left, right)
TRIGGER_PATHS = {
    "khr": ("/user/hand/left/input/select/click", "/user/hand/right/input/select/click"),
    "index": ("/user/hand/left/input/trigger/value", "/user/hand/right/input/trigger/value"),
    "oculus": ("/user/hand/left/input/trigger/value", "/user/hand/right/input/trigger/value"),
    "vive": ("/user/hand/left/input/trigger/value", "/user/hand/right/input/trigger/value"),
    "wmr": ("/user/hand/left/input/trigger/value", "/user/hand/right/input/trigger/value"),
}

SQUEEZE_PATHS = {
    "index": ("/user/hand/left/input/squeeze/force", "/user/hand/right/input/squeeze/force"),
    "oculus": ("/user/hand/left/input/squeeze/value", "/user/hand/right/input/squeeze/value"),
    "vive": ("/user/hand/left/input/squeeze/click", "/user/hand/right/input/squeeze/click"),
    "wmr": ("/user/hand/left/input/squeeze/click", "/user/hand/right/input/squeeze/click"),
}

JOYSTICK_PATHS = {
    "index": ("/user/hand/left/input/thumbstick", "/user/hand/right/input/thumbstick"),
    "oculus": ("/user/hand/left/input/thumbstick", "/user/hand/right/input/thumbstick"),
    "vive": ("/user/hand/left/input/trackpad", "/user/hand/right/input/trackpad"),
    "wmr": ("/user/hand/left/input/thumbstick", "/user/hand/right/input/thumbstick"),
}

BUTTON_A_PATHS = {
    "index": ("/user/hand/left/input/a/click", "/user/hand/right/input/a/click"),
    "oculus": ("/user/hand/left/input/x/click", "/user/hand/right/input/a/click"),
}

BUTTON_B_PATHS = {
    "index": ("/user/hand/left/input/b/click", "/user/hand/right/input/b/click"),
    "oculus": ("/user/hand/left/input/y/click", "/user/hand/right/input/b/click"),
}

BUTTON_A_TOUCH_PATHS = {
    "index": ("/user/hand/left/input/a/touch", "/user/hand/right/input/a/touch"),
    "oculus": ("/user/hand/left/input/x/touch", "/user/hand/right/input/a/touch"),
}

BUTTON_B_TOUCH_PATHS = {
    "index": ("/user/hand/left/input/b/touch", "/user/hand/right/input/b/touch"),
    "oculus": ("/user/hand/left/input/y/touch", "/user/hand/right/input/b/touch"),
}


def create_action(action_set, action_type, name, hand_paths):
    """Create an action with both hands as subaction paths."""
    return xr.create_action(
        action_set=action_set,
        create_info=xr.ActionCreateInfo(
            action_type=action_type,
            action_name=name,
            localized_action_name=name.replace("_", " ").title(),
            count_subaction_paths=len(hand_paths),
            subaction_paths=hand_paths,
        ),
    )


def suggest_bindings(instance, profile_name, action_path_pairs):
    """Suggest action bindings for an interaction profile."""
    bindings_list = []
    for action, paths in action_path_pairs:
        if paths:
            for path in paths:
                bindings_list.append(xr.ActionSuggestedBinding(action, xr.string_to_path(instance, path)))

    if bindings_list:
        xr.suggest_interaction_profile_bindings(
            instance=instance,
            suggested_bindings=xr.InteractionProfileSuggestedBinding(
                interaction_profile=xr.string_to_path(instance, PROFILES[profile_name]),
                count_suggested_bindings=len(bindings_list),
                suggested_bindings=(xr.ActionSuggestedBinding * len(bindings_list))(*bindings_list),
            ),
        )


def get_state(session, action, action_type, hand_path):
    """Get action state with error handling."""
    try:
        if action_type == xr.ActionType.FLOAT_INPUT:
            state = xr.get_action_state_float(session, xr.ActionStateGetInfo(action, hand_path))
            return state.current_state if state.is_active else None
        elif action_type == xr.ActionType.BOOLEAN_INPUT:
            state = xr.get_action_state_boolean(session, xr.ActionStateGetInfo(action, hand_path))
            return state.current_state if state.is_active else None
        elif action_type == xr.ActionType.VECTOR2F_INPUT:
            state = xr.get_action_state_vector2f(session, xr.ActionStateGetInfo(action, hand_path))
            return (state.current_state.x, state.current_state.y) if state.is_active else None
    except:
        return None


# Main program
with ContextObject(
    context_provider=GLFWOffscreenContextProvider(),
    instance_create_info=xr.InstanceCreateInfo(
        enabled_extension_names=[xr.KHR_OPENGL_ENABLE_EXTENSION_NAME],
    ),
) as context:
    hand_paths = (xr.Path * 2)(
        xr.string_to_path(context.instance, "/user/hand/left"),
        xr.string_to_path(context.instance, "/user/hand/right"),
    )

    # Create all actions
    actions = {
        "trigger": create_action(context.default_action_set, xr.ActionType.FLOAT_INPUT, "trigger", hand_paths),
        "squeeze": create_action(context.default_action_set, xr.ActionType.FLOAT_INPUT, "squeeze", hand_paths),
        "joystick": create_action(context.default_action_set, xr.ActionType.VECTOR2F_INPUT, "joystick", hand_paths),
        "button_a": create_action(context.default_action_set, xr.ActionType.BOOLEAN_INPUT, "button_a", hand_paths),
        "button_b": create_action(context.default_action_set, xr.ActionType.BOOLEAN_INPUT, "button_b", hand_paths),
        "button_a_touch": create_action(
            context.default_action_set, xr.ActionType.BOOLEAN_INPUT, "button_a_touch", hand_paths
        ),
        "button_b_touch": create_action(
            context.default_action_set, xr.ActionType.BOOLEAN_INPUT, "button_b_touch", hand_paths
        ),
    }

    # Suggest bindings for each profile
    for profile in ["khr", "index", "oculus", "vive", "wmr"]:
        suggest_bindings(
            context.instance,
            profile,
            [
                (actions["trigger"], TRIGGER_PATHS.get(profile)),
                (actions["squeeze"], SQUEEZE_PATHS.get(profile)),
                (actions["joystick"], JOYSTICK_PATHS.get(profile)),
                (actions["button_a"], BUTTON_A_PATHS.get(profile)),
                (actions["button_b"], BUTTON_B_PATHS.get(profile)),
                (actions["button_a_touch"], BUTTON_A_TOUCH_PATHS.get(profile)),
                (actions["button_b_touch"], BUTTON_B_TOUCH_PATHS.get(profile)),
            ],
        )

    # Print header
    print("\n" + "=" * 120)
    print("Controller Button States")
    print("=" * 120)

    session_was_focused = False
    for frame_index, frame_state in enumerate(context.frame_loop()):
        if context.session_state == xr.SessionState.FOCUSED:
            session_was_focused = True

            xr.sync_actions(
                context.session,
                xr.ActionsSyncInfo(1, ctypes.pointer(xr.ActiveActionSet(context.default_action_set, xr.NULL_PATH))),
            )

            for hand_idx, hand_name in enumerate(["LEFT", "RIGHT"]):
                states = {
                    name: get_state(
                        context.session,
                        action,
                        (
                            xr.ActionType.FLOAT_INPUT
                            if name in ["trigger", "squeeze"]
                            else xr.ActionType.VECTOR2F_INPUT if name == "joystick" else xr.ActionType.BOOLEAN_INPUT
                        ),
                        hand_paths[hand_idx],
                    )
                    for name, action in actions.items()
                }

                # Build output line with inline labels
                parts = [f"{hand_name:<6}"]
                for name, value in states.items():
                    if value is not None:
                        if isinstance(value, tuple):
                            parts.append(f"{name} [({value[0]:+.2f},{value[1]:+.2f})]")
                        elif isinstance(value, bool):
                            parts.append(f"{name} [{value}]")
                        else:
                            parts.append(f"{name} [{value:.3f}]")
                    else:
                        parts.append(f"{name} [---]")

                print("   ".join(parts))

        time.sleep(0.5)
        if frame_index >= 10:
            break

        print("")

    if not session_was_focused:
        print("\nWarning: Session never reached FOCUSED state.")
    print("=" * 120)
