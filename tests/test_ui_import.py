def test_import_ui():
    import ui
    assert hasattr(ui, "main")
    assert callable(ui.main)
