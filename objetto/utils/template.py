from typing import TYPE_CHECKING

from jinja2 import StrictUndefined, UndefinedError, TemplateSyntaxError  # type: ignore
from jinja2.nativetypes import NativeEnvironment  # type: ignore
from pyrsistent import pmap
from six import raise_from

if TYPE_CHECKING:
    from typing import Any, Optional, Mapping

__all__ = [
    "DEFAULT_TEMPLATE_TAGS",
    "TemplateRenderError",
    "has_template_tags",
    "render_template",
]


DEFAULT_TEMPLATE_TAGS = pmap({
    "block_start_tag": r"{%",
    "block_end_tag": r"%}",
    "variable_start_tag": r"{{",
    "variable_end_tag": r"}}",
    "comment_start_tag": r"{#",
    "comment_end_tag": r"#}",
})


class TemplateRenderError(Exception):
    """Error while rendering template."""


def has_template_tags(
    template,  # type: str
    block_start_tag=DEFAULT_TEMPLATE_TAGS["block_start_tag"],  # type: str
    block_end_tag=DEFAULT_TEMPLATE_TAGS["block_end_tag"],  # type: str
    variable_start_tag=DEFAULT_TEMPLATE_TAGS["variable_start_tag"],  # type: str
    variable_end_tag=DEFAULT_TEMPLATE_TAGS["variable_end_tag"],  # type: str
    comment_start_tag=DEFAULT_TEMPLATE_TAGS["comment_start_tag"],  # type: str
    comment_end_tag=DEFAULT_TEMPLATE_TAGS["comment_end_tag"],  # type: str
):
    # type: (...) -> bool
    """Tell whether string has template tags or not."""
    tags = (
        block_start_tag,
        block_end_tag,
        variable_start_tag,
        variable_end_tag,
        comment_start_tag,
        comment_end_tag,
    )
    return not bool(all(t not in template for t in tags))


def render_template(
    template,  # type: str
    variables=None,  # type: Optional[Mapping[str, Any]]
    block_start_tag=DEFAULT_TEMPLATE_TAGS["block_start_tag"],  # type: str
    block_end_tag=DEFAULT_TEMPLATE_TAGS["block_end_tag"],  # type: str
    variable_start_tag=DEFAULT_TEMPLATE_TAGS["variable_start_tag"],  # type: str
    variable_end_tag=DEFAULT_TEMPLATE_TAGS["variable_end_tag"],  # type: str
    comment_start_tag=DEFAULT_TEMPLATE_TAGS["comment_start_tag"],  # type: str
    comment_end_tag=DEFAULT_TEMPLATE_TAGS["comment_end_tag"],  # type: str
):
    # type: (...) -> Any
    """Render template with optional variables."""
    environment = NativeEnvironment(
        undefined=StrictUndefined,
        block_start_string=block_start_tag,
        block_end_string=block_end_tag,
        variable_start_string=variable_start_tag,
        variable_end_string=variable_end_tag,
        comment_start_string=comment_start_tag,
        comment_end_string=comment_end_tag,
    )
    try:
        jinja_template = environment.from_string(template)
        rendered_template = jinja_template.render(variables or {})
        try:
            assert rendered_template
        except AssertionError:
            pass
    except (TemplateSyntaxError, UndefinedError) as e:
        error = "{}; {}".format(repr(template), e)
        exc = TemplateRenderError(error)
        raise_from(exc, None)
        raise exc
    return rendered_template
