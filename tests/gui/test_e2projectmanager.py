from __future__ import print_function
from PyQt4.QtCore import Qt, QPoint
import pyautogui, sys, os

def test_display_initial_gui(qtbot, win, curdir):
    win = win('e2projectmanager')
#     main_form = win.main_form
# 
#     win.cycle(qtbot, main_form)
#     main_form.showMaximized()
#     qtbot.mouseClick(main_form, Qt.LeftButton)
#     spr = main_form.tree_stacked_widget.children()[3]
#     raw_data = spr.invisibleRootItem().child(0)
#     spr.expandItem(raw_data)
#     qtbot.wait(1000)
#     # raw_data.expandItem()
#     # qtbot.wait(1000)
#     item = raw_data.child(2)
#     # sc=2.
#     # qtbot.mouseClick(spr, Qt.LeftButton, pos=QPoint(285/sc,543/sc))
#     # qtbot.mouseClick(spr, Qt.LeftButton, pos=QPoint(162/sc,103/sc))
#     # qtbot.mouseClick(spr, Qt.LeftButton, pos=QPoint(360/sc,549/sc))
#     # qtbot.mouseClick(spr, Qt.LeftButton, pos=QPoint(150,150))
#     # qtbot.mouseClick(spr, Qt.LeftButton, pos=QPoint(300,300))
#     # for i in range(0, 400, 4):
#     #     for j in range(0,400, 2):
#     #         qtbot.mouseClick(spr, Qt.LeftButton, pos=QPoint(i,j))
#     #         print(i, j)
#     #         qtbot.wait(10)
#     # print(dir(main_form.children))
#     print(main_form.children)
#     print("In test: ", item, item.text(0))
#     # main_form._tree_widget_click(item,0)
#     # print(item.mapToGlobal(item.pos()))
#     # print(curdir + '/button1.png')
#     # loc = pyautogui.locateOnScreen(curdir + '/button1.png')
#     # print(loc)
#     # x1, y1 = pyautogui.center(loc)
#     # pyautogui.click(x=x1/2, y=y1/2)
#     # click_image(qtbot, os.path.join(curdir, 'button_evaluate_import_micrographs.png'))
#     # click_image(qtbot,(165, 344))
#     # click_image(qtbot, os.path.join(curdir, 'button_import_micrographs_defocus.png'))
#     click_image(qtbot,(162, 379))
#     # click_image(qtbot, os.path.join(curdir, 'text_box_import_micrographs_defocus.png'), False)
#     click_image(qtbot,(550, 291))
# 
#     dir = os.path.join(curdir, 'data', 'bgal', 'orig_micrographs')
#     # files = [os.path.abspath(f) for f in os.listdir(dir)]
#     files = [os.path.join('orig_micrographs', f) for f in os.listdir(dir)]
#     for f in files:
#         pyautogui.typewrite(f)
#         pyautogui.typewrite(' ')
#     #     # print(f)
#     qtbot.wait(1000)
#     # print(files)
# 
#     # click_image(qtbot, os.path.join(curdir, 'button_launch.png'), False)
#     click_image(qtbot,(1120, 778))
#     # main_form.showMaximized()
# 
#     qtbot.wait(2000)
#     # try:
#     #     while True:
#     #         x, y = pyautogui.position()
#     #         positionStr = 'X: ' + str(x).rjust(4) + ' Y: ' + str(y).rjust(4)
#     #         print(positionStr, end='')
#     #         print('\b' * len(positionStr), end='')
#     # except KeyboardInterrupt:
#     #     print('\n')
#     
# def click_image(qtbot, img, isClick=True):
#     if isinstance(img, basestring):
#         loc = pyautogui.locateOnScreen(img)
#         x1, y1 = pyautogui.center(loc)
#         x1 = x1 / 2
#         y1 = y1 / 2
#         print(img)
#         print(x1, y1)
#     else:
#         x1 = img[0]
#         y1 = img[1]
#     
#     if isClick:
#         pyautogui.click(x1, y1)
#         qtbot.wait(500)
#     else:
#         pyautogui.moveTo(x1, y1)
