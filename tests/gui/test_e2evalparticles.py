def test_display_initial_gui(main_window, snap):
    main_window = main_window('e2evalparticles')
    snap = snap('e2evalparticles')
    snap(main_window)
