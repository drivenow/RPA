import re
import json
import re
from typing import Any, Callable, List


def format_text(text):
    clean_text = re.sub(r'<.*?>', '', text)
    return clean_text


def format_folder_name(folder_name):
    folder_name = folder_name.strip(). \
        replace("?", "").replace("*", "").replace("<", ""). \
        replace(",", " ").replace(".", "").replace(";", ""). \
        replace(":", "").replace(">", "").replace("|", "").replace("\"", "").replace("/", ""). \
        replace("\\", "").replace("\n", "").replace("\r", "").replace("\t", "")
    return folder_name


class JsonRepairError(Exception):
    def __init__(self, e, text):
        message = "Don't know how to fix '%s', position %s (-->%s<--)" % (e.msg, e.pos, text[e.pos - 5:e.pos + 5])
        super().__init__(message)
        self.text = text


def json_repair(text):
    while True:
        try:
            return json.loads(text)
        except json.decoder.JSONDecodeError as e:
            if e.msg == "Expecting ',' delimiter":
                if text[e.pos - 1] == '"':
                    text = text[:e.pos - 1] + '\\' + text[e.pos - 1:]
                    continue
                elif text[e.pos - 2] == '"':
                    text = text[:e.pos - 2] + '\\' + text[e.pos - 2:]
                    continue
            elif e.msg == "Invalid control character at":
                if text[e.pos] == '\n':
                    text = text[:e.pos] + '\\n' + text[e.pos + 1:]
                    continue

            raise JsonRepairError(e, text) from None


def _replace_new_line(match: re.Match[str]) -> str:
    value = match.group(2)
    value = re.sub(r"\n", r"\\n", value)
    value = re.sub(r"\r", r"\\r", value)
    value = re.sub(r"\t", r"\\t", value)
    value = re.sub(r'(?<!\\)"', r"\"", value)

    return match.group(1) + value + match.group(3)


def _custom_parser(multiline_string: str) -> str:
    """
    The LLM response for `action_input` may be a multiline
    string containing unescaped newlines, tabs or quotes. This function
    replaces those characters with their escaped counterparts.
    (newlines in JSON must be double-escaped: `\\n`)
    """
    if isinstance(multiline_string, (bytes, bytearray)):
        multiline_string = multiline_string.decode()

    multiline_string = re.sub(
        r'("action_input"\:\s*")(.*?)(")',
        _replace_new_line,
        multiline_string,
        flags=re.DOTALL,
    )

    return multiline_string


# Adapted from https://github.com/KillianLucas/open-interpreter/blob/5b6080fae1f8c68938a1e4fa8667e3744084ee21/interpreter/utils/parse_partial_json.py
# MIT License


def parse_partial_json(s: str, *, strict: bool = False) -> Any:
    """Parse a JSON string that may be missing closing braces.

    Args:
        s: The JSON string to parse.
        strict: Whether to use strict parsing. Defaults to False.

    Returns:
        The parsed JSON object as a Python dictionary.
    """
    # Attempt to parse the string as-is.
    try:
        return json.loads(s, strict=strict)
    except json.JSONDecodeError:
        pass

    # Initialize variables.
    new_chars = []
    stack = []
    is_inside_string = False
    escaped = False

    # Process each character in the string one at a time.
    for char in s:
        if is_inside_string:
            if char == '"' and not escaped:
                is_inside_string = False
            elif char == "\n" and not escaped:
                char = "\\n"  # Replace the newline character with the escape sequence.
            elif char == "\\":
                escaped = not escaped
            else:
                escaped = False
        else:
            if char == '"':
                is_inside_string = True
                escaped = False
            elif char == "{":
                stack.append("}")
            elif char == "[":
                stack.append("]")
            elif char == "}" or char == "]":
                if stack and stack[-1] == char:
                    stack.pop()
                else:
                    # Mismatched closing character; the input is malformed.
                    return None

        # Append the processed character to the new string.
        new_chars.append(char)

    # If we're still inside a string at the end of processing,
    # we need to close the string.
    if is_inside_string:
        new_chars.append('"')

    # Reverse the stack to get the closing characters.
    stack.reverse()

    # Try to parse mods of string until we succeed or run out of characters.
    while new_chars:
        # Close any remaining open structures in the reverse
        # order that they were opened.
        # Attempt to parse the modified string as JSON.
        try:
            return json.loads("".join(new_chars + stack), strict=strict)
        except json.JSONDecodeError:
            # If we still can't parse the string as JSON,
            # try removing the last character
            new_chars.pop()

    # If we got here, we ran out of characters to remove
    # and still couldn't parse the string as JSON, so return the parse


_json_markdown_re = re.compile(r"```(json)?(.*)", re.DOTALL)


def parse_json_markdown(
        json_string: str, *, parser: Callable[[str], Any] = parse_partial_json
) -> dict:
    """Parse a JSON string from a Markdown string.

    Args:
        json_string: The Markdown string.

    Returns:
        The parsed JSON object as a Python dictionary.
    """
    try:
        json_str = _parse_json(json_string, parser=parser)
        if json_str is None:
            raise ValueError("Invalid JSON string")
    except Exception as e:
        # Try to find JSON string within triple backticks
        match = _json_markdown_re.search(json_string)

        # If no match found, assume the entire string is a JSON string
        if match is None:
            json_str = json_string
        else:
            # If match found, use the content within the backticks
            json_str = match.group(2)
    return _parse_json(json_str, parser=parser)


_json_strip_chars = " \n\r\t`"


def _parse_json(
        json_str: str, *, parser: Callable[[str], Any] = parse_partial_json
) -> dict:
    # Strip whitespace,newlines,backtick from the start and end
    if type(json_str) == dict:
        return json_str
    json_str = json_str.strip(_json_strip_chars)

    # handle newlines and other special characters inside the returned value
    json_str = _custom_parser(json_str)

    # Parse the JSON string into a Python dictionary
    return parser(json_str)


def parse_and_check_json_markdown(text: str, expected_keys: List[str] = []) -> dict:
    """
    Parse a JSON string from a Markdown string and check that it
    contains the expected keys.

    Args:
        text: The Markdown string.
        expected_keys: The expected keys in the JSON string.

    Returns:
        The parsed JSON object as a Python dictionary.

    Raises:
        OutputParserException: If the JSON string is invalid or does not contain
            the expected keys.
    """
    try:
        json_obj = parse_json_markdown(text)
    except json.JSONDecodeError as e:
        raise JsonRepairError(f"Got invalid JSON object. Error: {e}") from e
    if expected_keys:
        for key in expected_keys:
            if key not in json_obj:
                raise JsonRepairError(
                    f"Got invalid return object. Expected key `{key}` "
                    f"to be present, but got {json_obj}"
                )
    return json_obj


if __name__ == '__main__':
    text = "百大UP 黑马奖 <em class=\"keyword\">渤海小吏</em> 精彩发言"
    clean_text = format_text(text)
    print(clean_text)
