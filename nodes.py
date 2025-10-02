import itertools
import math
import json
from typing import Tuple

commentSymbol = "#"
newline = "\n"
MAX_SEED_NUM = 1125899906842624


def strip_comments(list: list[str]):
    return [line.split(commentSymbol, 1)[0] for line in list]


def strip_empty(list: list[str]):
    return [line for line in list if line.strip()]


def bound_idx(idx: int, list: list[str]):
    return max(0, min(idx, len(list) - 1))


def pick_by_idx(idx: int, list: list[str]):
    idx = bound_idx(idx, list)
    return list[idx : idx + 1]


def to_multiline(list: list[str]):
    return newline.join(list)


def to_enumerated(list: list[str]):
    return newline.join(
        [
            commentSymbol + str(index) + newline + value + newline
            for index, value in enumerate(list)
        ]
    )


def preprocess_multiline(input: str, cut_comments: bool, ignore_empty_lines: bool):
    lines = input.split(newline)
    if cut_comments:
        lines = strip_comments(lines)

    if ignore_empty_lines:
        lines = strip_empty(lines)

    return lines


class AlwaysEqualProxy(str):
    def __eq__(self, _):
        return True

    def __ne__(self, _):
        return False


any_type = AlwaysEqualProxy("*")


class PromptSelector:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):  # type: ignore
        return {
            "required": {
                "pick_index": (
                    "INT",
                    {"default": 0, "min": 0, "max": 9999, "tooltip": ""},
                ),
                "pick_by_index": ("BOOLEAN", {"default": False, "tooltip": ""}),
                "ignore_empty_lines": ("BOOLEAN", {"default": True, "tooltip": ""}),
                "cut_comments": ("BOOLEAN", {"default": True, "tooltip": ""}),
                "prepend_text": (
                    "STRING",
                    {"multiline": False, "default": "", "tooltip": ""},
                ),
                "append_text": (
                    "STRING",
                    {"multiline": False, "default": "", "tooltip": ""},
                ),
                "multiline_text": (
                    "STRING",
                    {"multiline": True, "default": "body_text", "tooltip": ""},
                ),
            }
        }  # type: ignore

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = (
        "prompt_list",
        "body_text_list",
        "current_idx",
        "prompt_multiline",
        "prompt_multiline_with_line_numbers",
    )
    OUTPUT_IS_LIST = (True, True, True, False, False)
    FUNCTION = "make_list"
    DESCRIPTION = (
        "Produces sequence of prompts and multiline output for processing (if required)"
    )

    # OUTPUT_NODE = False
    # OUTPUT_TOOLTIPS = ("",) # Tooltips for the output node

    CATEGORY = "Text tools"

    def make_list(
        self,
        pick_index: int = 0,
        pick_by_index: bool = False,
        ignore_empty_lines: bool = True,
        cut_comments: bool = True,
        prepend_text: str = "",
        append_text: str = "",
        multiline_text: str = "",
    ):
        lines = preprocess_multiline(multiline_text, cut_comments, ignore_empty_lines)

        # Ensure pick_index is within the bounds of the list
        pick_index = max(0, min(pick_index, len(lines) - 1))

        # Extract line by pick_index if pick_by_index set
        selected_rows = lines[pick_index : pick_index + 1] if pick_by_index else lines

        body_list_out = lines
        prompt_list_out = [prepend_text + line + append_text for line in selected_rows]

        newline = "\n"
        prompt_multiline = newline.join(prompt_list_out)

        enumerated = enumerate(prompt_list_out)
        prompt_multiline_with_line_numbers = newline.join(
            ["# " + str(index) + "\n" + value for index, value in enumerated]
        )

        current_idx = [pick_index] if pick_by_index else range(len(prompt_list_out))

        return (
            prompt_list_out,
            body_list_out,
            current_idx,
            prompt_multiline,
            prompt_multiline_with_line_numbers,
        )


class PromptCombiner:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):  # type: ignore
        return {
            "required": {
                "pick_index": (
                    "INT",
                    {"default": 0, "min": 0, "max": 9999, "tooltip": ""},
                ),
                "pick_by_index": ("BOOLEAN", {"default": False, "tooltip": ""}),
                "ignore_empty_lines": ("BOOLEAN", {"default": True, "tooltip": ""}),
                "cut_comments": ("BOOLEAN", {"default": True, "tooltip": ""}),
                "prepend_text": (
                    "STRING",
                    {"multiline": False, "default": "", "tooltip": ""},
                ),
                "append_text": (
                    "STRING",
                    {"multiline": False, "default": "", "tooltip": ""},
                ),
                "separator": ("STRING", {"default": ", "}),
                "prompts_0": (
                    "STRING",
                    {"multiline": True, "default": "", "tooltip": ""},
                ),
                "prompts_1": (
                    "STRING",
                    {"multiline": True, "default": "", "tooltip": ""},
                ),
            }
        }  # type: ignore

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = (
        "prompt_list",
        "body_text_list",
        "current_idx",
        "prompt_multiline",
        "prompt_multiline_with_line_numbers",
    )
    OUTPUT_IS_LIST = (True, True, True, False, False)
    FUNCTION = "combine"
    DESCRIPTION = "Split multiline inputs and produce sequence of their combinations"

    def combine(
        self,
        pick_index: int = 0,
        pick_by_index: bool = False,
        ignore_empty_lines: bool = True,
        cut_comments: bool = True,
        prepend_text: str = "",
        append_text: str = "",
        separator: str = "",
        prompts_0: str = "",
        prompts_1: str = "",
    ):
        lines_0 = preprocess_multiline(prompts_0, cut_comments, ignore_empty_lines)
        lines_1 = preprocess_multiline(prompts_1, cut_comments, ignore_empty_lines)

        product = [
            tuple[0] + separator + tuple[1]
            for tuple in itertools.product(lines_0, lines_1)
        ]

        body_list_out = pick_by_idx(pick_index, product) if pick_by_index else product

        prompt_list_out = [prepend_text + line + append_text for line in body_list_out]

        prompt_multiline = to_multiline(prompt_list_out)

        prompt_multiline_with_line_numbers = to_enumerated(prompt_list_out)

        current_idx = [pick_index] if pick_by_index else range(len(prompt_list_out))

        return (
            prompt_list_out,
            body_list_out,
            current_idx,
            prompt_multiline,
            prompt_multiline_with_line_numbers,
        )


class SeedIndex:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):  # type: ignore
        return {
            "required": {
                "task_index": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": 1000,
                        "control_after_generate": True,
                        "tooltip": "Set control_after_generate to 'increment'",
                    },
                ),
                "seed_start": (
                    "INT",
                    {
                        "default": 0,
                        "min": -0xFFFFFFFFFFFFFFFF,
                        "max": 0xFFFFFFFFFFFFFFFF,
                        "tooltip": "Seed to work with",
                    },
                ),
                "seeds_total": (
                    "INT",
                    {
                        "default": 1,
                        "min": 1,
                        "max": 1000,
                        "tooltip": "Total seeds for each prompt index",
                    },
                ),
                "seed_method": (
                    ["fixed", "increment", "decrement"],
                    {"default": "increment", "tooltip": ""},
                ),
                "index_start": (
                    "INT",
                    {"default": 0, "min": 0, "max": 1000, "tooltip": ""},
                ),
                "indexes_total": (
                    "INT",
                    {
                        "default": 1,
                        "min": 1,
                        "max": 1000,
                        "tooltip": "When node should stop",
                    },
                ),
                "order": (
                    ["seed_then_index", "index_then_seed"],
                    {"default": "seed_then_index", "tooltip": ""},
                ),
                "batch_size": (
                    "INT",
                    {
                        "default": 1,
                        "min": 1,
                        "max": 1000,
                        "tooltip": "How many tasks should be processed in one run.",
                    },
                ),
            },
        }  # type: ignore

    RETURN_TYPES = ("INT", "INT", "STRING")
    RETURN_NAMES = ("seed", "index", "seedIndexFormatted")
    OUTPUT_IS_LIST = (True, True, True)
    FUNCTION = "nextSeedIndex"
    DESCRIPTION = (
        "Produces sequence of prompts and multiline output for processing (if required)"
    )

    @classmethod
    def VALIDATE_INPUTS(
        cls, task_index: int, seeds_total: int, indexes_total: int, batch_size: int
    ):
        if task_index > seeds_total * indexes_total / batch_size:
            return "task_index ({}) should not be greater than seeds_total*indexes_total ({})".format(
                task_index, math.floor(seeds_total * indexes_total / batch_size)
            )
        return True

    def nextSeedIndex(
        self,
        task_index: int = 0,
        seed_start: int = 0,
        seeds_total: int = 1,
        seed_method: str = "increment",
        index_start: int = 0,
        indexes_total: int = 1,
        order: str = "seed_then_index",
        batch_size: int = 1,
    ):
        total_tasks = seeds_total * indexes_total

        real_task_index = task_index * batch_size

        task_range = range(real_task_index, real_task_index + batch_size)

        seeds: list[int] = []
        prompts: list[int] = []
        descriptions: list[str] = []

        for real_task_idx in task_range:
            if real_task_idx >= total_tasks:
                break

            if order == "seed_then_index":
                seedIdx = real_task_idx % seeds_total
                promptIdx = math.floor(real_task_idx / seeds_total) % indexes_total
            else:
                seedIdx = math.floor(real_task_idx / indexes_total) % seeds_total
                promptIdx = real_task_idx % indexes_total

            seed = seed_start
            if seed_method == "increment":
                seed += seedIdx
            if seed_method == "decrement":
                seed -= seedIdx
            seeds.append(seed)

            prompt = index_start + promptIdx
            prompts.append(prompt)

            descriptions.append("seed {} index {}".format(seed, prompt))

        return (seeds, prompts, descriptions)


class TextJoin:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):  # type: ignore
        return {
            "required": {
                "separator": (
                    "STRING",
                    {"default": ", ", "tooltip": "Use \\n for new line"},
                ),
            },
            "optional": {
                "quality": ("STRING", {"forceInput": True}),
                "medium": ("STRING", {"forceInput": True}),
                "background": ("STRING", {"forceInput": True}),
                "actor": ("STRING", {"forceInput": True}),
                "expression": ("STRING", {"forceInput": True}),
                "dressing": ("STRING", {"forceInput": True}),
                "action": ("STRING", {"forceInput": True}),
                "tuning": ("STRING", {"forceInput": True}),
                "whatever": ("STRING", {"forceInput": True}),
                "more": ("STRING", {"forceInput": True}),
            },
        }  # type: ignore

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    OUTPUT_IS_LIST = (False,)
    FUNCTION = "join"

    def join(self, **kwargs: str):
        text_list: list[str] = []

        separator: str = kwargs["separator"]

        separator = separator.replace("\\n", "\n")

        # Iterate over the received inputs in sorted order.
        for key, value in kwargs.items():
            if key == "separator":
                continue

            # Only process string input ports.
            if isinstance(value, str) and (value.strip()):  # type: ignore
                text_list.append(value)

        text = separator.join(text_list)

        return (text,)


# A dictionary that contains all nodes you want to export with their names
# NOTE: names should be globally unique
NODE_CLASS_MAPPINGS = {  # type: ignore
    "PromptSelector": PromptSelector,
    "PromptCombiner": PromptCombiner,
    "SeedIndex": SeedIndex,
    "TextJoin": TextJoin,
}

# A dictionary that contains the friendly/humanly readable titles for the nodes
NODE_DISPLAY_NAME_MAPPINGS = {
    "PromptSelector": "T2 Prompt Selector",
    "PromptCombiner": "T2 Prompt Combiner",
    "SeedIndex": "T2 Seed Index",
    "TextJoin": "T2 Text Join",
}
