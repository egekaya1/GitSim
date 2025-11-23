"""Tests for plugin loader utilities."""

from pathlib import Path

from git_sim.plugins.loader import create_plugin_template, discover_plugins


def test_create_plugin_template_simulator(tmp_path: Path):
    path = create_plugin_template("example-sim", plugin_type="simulator", output_dir=tmp_path)
    created = Path(path)
    assert created.exists()
    content = created.read_text()
    assert "SafetyInfo" in content
    assert "data_loss_risk" not in content  # Ensure removed field
    assert "reversible=True" in content


def test_create_plugin_template_formatter(tmp_path: Path):
    path = create_plugin_template("fmt", plugin_type="formatter", output_dir=tmp_path)
    created = Path(path)
    assert created.exists()
    content = created.read_text()
    assert "FormatterPlugin" in content


def test_create_plugin_template_hook(tmp_path: Path):
    path = create_plugin_template("hookz", plugin_type="hook", output_dir=tmp_path)
    created = Path(path)
    assert created.exists()
    content = created.read_text()
    assert "HookPlugin" in content


def test_discover_plugins_empty():
    # With no installed entry points should return empty list gracefully
    plugins = discover_plugins()
    assert isinstance(plugins, list)
    assert plugins == []
