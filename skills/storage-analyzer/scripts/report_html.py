"""Render report values safely inside the template's JavaScript literals."""
import json
import re


def script_json(value):
    # HTML parses script end tags before JavaScript parses quoted strings.
    # Escape HTML-significant bytes and JS line separators without changing data.
    return (json.dumps(value, ensure_ascii=False)
            .replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e")
            .replace("\u2028", "\\u2028").replace("\u2029", "\\u2029"))


def render_report(template, data, delete_config=None):
    values = {"__REPORT_DATA__": script_json(data),
              "__DELETE_CONFIG__": script_json(delete_config)}
    # A single pass ensures marker-like strings in user data are never replaced.
    return re.sub(r"__REPORT_DATA__|__DELETE_CONFIG__", lambda m: values[m[0]], template)
