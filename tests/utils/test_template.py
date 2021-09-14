# -*- coding: utf-8 -*-

from pytest import main, raises

from objetto.utils.template import TemplateRenderError, render_template


def test_render_template():
    assert render_template("{{None}}") is None
    assert render_template("{{variable + 2}}", {"variable": 3}) == 5


def test_custom_template_tags():
    custom_tags = dict(
        block_start_tag=r"<%",
        block_end_tag=r"%>",
        variable_start_tag=r"<<",
        variable_end_tag=r">>",
        comment_start_tag=r"<#",
        comment_end_tag=r"#>",
    )
    assert render_template("<<None>>", **custom_tags) is None
    assert render_template("<<variable + 2>>", {"variable": 3}, **custom_tags) == 5


def test_exception():
    with raises(TemplateRenderError):
        render_template("{{missing_variable}}")


if __name__ == "__main__":
    main()
