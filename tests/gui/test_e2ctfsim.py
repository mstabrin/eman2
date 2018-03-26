def test_cli(qtbot, win):
    win = win('e2ctfsim','')
    main_form = win.main_form
    qtbot.addWidget(main_form)
    
    win.cycle(qtbot, main_form)
    win.cycle(qtbot, main_form.guiim)
    win.cycle(qtbot, main_form.guiplot)
    
    for f in [main_form.sdefocus, main_form.sbfactor, main_form.sampcont]:
        win.setValSlider(qtbot, main_form, f)
        win.cycle(qtbot, main_form)
        win.cycle(qtbot, main_form.guiim)
        win.cycle(qtbot, main_form.guiplot)
