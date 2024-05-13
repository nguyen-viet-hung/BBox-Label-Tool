# -------------------------------------------------------------------------------
# Name:        Object bounding box label tool
# Purpose:     Label object bboxes for ImageNet Detection data
# Author:      Qiushi
# Created:     06/06/2014

#
# -------------------------------------------------------------------------------
from __future__ import division
from tkinter import *
# import tkMessageBox
from PIL import Image, ImageTk, ExifTags
from tkinter import ttk
import os
import glob
import random

# colors for the bboxes
COLORS = ['red', 'blue', 'olive', 'teal', 'cyan', 'green', 'black']
# image sizes for the examples
SIZE = 256, 256


class LabelTool:
    def __init__(self, master):
        # set up the main frame
        self.tmp = []
        self.parent = master
        self.parent.title("LabelTool")
        self.frame = Frame(self.parent)
        self.frame.pack(fill=BOTH, expand=1)
        self.parent.resizable(width=FALSE, height=FALSE)

        # initialize global state
        self.imageDir = ''
        self.imageList = []
        self.egDir = ''
        self.egList = []
        self.outDir = ''
        self.cur = 0
        self.total = 0
        self.category = 0
        self.imagename = ''
        self.labelfilename = ''
        self.tkimg = None
        self.currentLabelclass = ''
        self.cla_can_temp = []
        self.classcandidate_filename = 'class.txt'

        # initialize mouse state
        self.STATE = {}
        self.STATE['click'] = 0
        self.STATE['x'], self.STATE['y'] = 0, 0

        # reference to bbox
        self.bboxIdList = []
        self.bboxId = None
        self.bboxList = []
        self.hl = None
        self.vl = None

        # ----------------- GUI stuff ---------------------
        # dir entry & load
        self.label = Label(self.frame, text="Image Dir:")
        self.label.grid(row=0, column=0, sticky=E)
        self.entry = Entry(self.frame)
        self.entry.grid(row=0, column=1, sticky=W + E)
        self.ldBtn = Button(self.frame, text="Load", command=self.loadDir)
        self.ldBtn.grid(row=0, column=2, sticky=W + E)

        # main panel for labeling
        self.mainPanel = Canvas(self.frame, cursor='tcross')
        self.mainPanel.bind("<Button-1>", self.mouseClick)
        self.mainPanel.bind("<Motion>", self.mouseMove)
        self.parent.bind("<Escape>", self.cancelBBox)  # press <Espace> to cancel current bbox
        self.parent.bind("s", self.cancelBBox)
        self.parent.bind("a", self.prevImage)  # press 'a' to go backforward
        self.parent.bind("d", self.nextImage)  # press 'd' to go forward
        self.mainPanel.grid(row=1, column=1, rowspan=4, sticky=W + N)

        # choose class
        self.classname = StringVar()
        self.classcandidate = ttk.Combobox(self.frame, state='readonly', textvariable=self.classname)
        self.classcandidate.grid(row=1, column=2)
        if os.path.exists(self.classcandidate_filename):
            with open(self.classcandidate_filename, encoding="utf8") as cf:
                for line in cf.readlines():
                    # print line
                    self.cla_can_temp.append(line.strip('\n'))
        # print self.cla_can_temp
        self.classcandidate['values'] = self.cla_can_temp
        self.classcandidate.current(0)
        self.currentLabelclass = self.classcandidate.get()  # init
        self.btnclass = Button(self.frame, text='ComfirmClass', command=self.setClass)
        self.btnclass.grid(row=2, column=2, sticky=W + E)

        # showing bbox info & delete bbox
        self.lb1 = Label(self.frame, text='Bounding boxes:')
        self.lb1.grid(row=3, column=2, sticky=W + N)
        self.listbox = Listbox(self.frame, width=22, height=12)
        self.listbox.grid(row=4, column=2, sticky=N + S)
        self.btnDel = Button(self.frame, text='Delete', command=self.delBBox)
        self.btnDel.grid(row=5, column=2, sticky=W + E + N)
        self.btnClear = Button(self.frame, text='ClearAll', command=self.clearBBox)
        self.btnClear.grid(row=6, column=2, sticky=W + E + N)

        # control panel for image navigation
        self.ctrPanel = Frame(self.frame)
        self.ctrPanel.grid(row=7, column=1, columnspan=2, sticky=W + E)
        self.prevBtn = Button(self.ctrPanel, text='<< Prev', width=10, command=self.prevImage)
        self.prevBtn.pack(side=LEFT, padx=5, pady=3)
        self.nextBtn = Button(self.ctrPanel, text='Next >>', width=10, command=self.nextImage)
        self.nextBtn.pack(side=LEFT, padx=5, pady=3)
        self.progLabel = Label(self.ctrPanel, text="Progress:     /    ")
        self.progLabel.pack(side=LEFT, padx=5)
        self.tmpLabel = Label(self.ctrPanel, text="Go to Image No.")
        self.tmpLabel.pack(side=LEFT, padx=5)
        self.idxEntry = Entry(self.ctrPanel, width=5)
        self.idxEntry.pack(side=LEFT)
        self.goBtn = Button(self.ctrPanel, text='Go', command=self.gotoImage)
        self.goBtn.pack(side=LEFT)

        # example pannel for illustration
        self.egPanel = Frame(self.frame, border=10)
        self.egPanel.grid(row=1, column=0, rowspan=5, sticky=N)
        self.tmpLabel2 = Label(self.egPanel, text="Examples:")
        self.tmpLabel2.pack(side=TOP, pady=5)
        self.egLabels = []
        for i in range(3):
            self.egLabels.append(Label(self.egPanel))
            self.egLabels[-1].pack(side=TOP)

        # display mouse position
        self.disp = Label(self.ctrPanel, text='')
        self.disp.pack(side=RIGHT)

        self.frame.columnconfigure(1, weight=1)
        self.frame.rowconfigure(4, weight=1)

        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        self.orientation = orientation

        # for debugging

    ##        self.setImage()
    ##        self.loadDir()

    def loadDir(self, dbg=False):
        if not dbg:
            s = self.entry.get()
            self.parent.focus()
            self.category = int(s)
        else:
            s = r'D:\workspace\python\labelGUI'
        # get image list
        self.imageDir = os.path.join(r'./Images', '%03d' % self.category)
        # print self.imageDir
        # print self.category
        self.imageList = glob.glob(os.path.join(self.imageDir, '*.JPG'))
        # print self.imageList
        if len(self.imageList) == 0:
            print('No .JPG images found in the specified dir!')
            return

        # default to the 1st image in the collection
        self.cur = 1
        self.total = len(self.imageList)

        # set up output dir
        self.outDir = os.path.join(r'./Labels', '%03d' % self.category)
        if not os.path.exists(self.outDir):
            os.mkdir(self.outDir)

        # load example bboxes
        # self.egDir = os.path.join(r'./Examples', '%03d' %(self.category))
        self.egDir = os.path.join(r'./Examples/demo')
        print(os.path.exists(self.egDir))
        if not os.path.exists(self.egDir):
            return
        filelist = glob.glob(os.path.join(self.egDir, '*.JPG'))
        self.egList = []
        random.shuffle(filelist)
        for (i, f) in enumerate(filelist):
            if i == 3:
                break
            im = Image.open(f)
            r = min(SIZE[0] / im.size[0], SIZE[1] / im.size[1])
            new_size = int(r * im.size[0]), int(r * im.size[1])
            self.tmp.append(im.resize(new_size, Image.LANCZOS))
            self.egList.append(ImageTk.PhotoImage(self.tmp[-1]))
            self.egLabels[i].config(image=self.egList[-1], width=SIZE[0], height=SIZE[1])

        self.loadImage()
        print(f'{self.total} images loaded from {s}')

    def loadImage(self):
        # load image
        imagepath = self.imageList[self.cur - 1]
        self.img = Image.open(imagepath)
        # check if orientation
        exif = self.img._getexif()
        if not isinstance(exif, type(None)):
            if exif[self.orientation] == 3:
                self.img = self.img.rotate(180, expand=True)
                self.img.save(imagepath)
            elif exif[self.orientation] == 6:
                self.img = self.img.rotate(270, expand=True)
                self.img.save(imagepath)
            elif exif[self.orientation] == 8:
                self.img = self.img.rotate(90, expand=True)
                self.img.save(imagepath)

        iwidth, iheight = self.img.size
        cwidth = 800
        cheight = int(cwidth * iheight / iwidth)
        if cheight > 700:
            cheight = 700
            cwidth = int(cheight * iwidth / iheight)
        size = (cwidth, cheight)
        resized = self.img.resize(size, Image.LANCZOS)
        self.tkimg = ImageTk.PhotoImage(resized)
        self.mainPanel.config(width=cwidth, height=cheight)
        self.mainPanel.create_image(0, 0, image=self.tkimg, anchor=NW)
        self.mainPanel.update()
        self.progLabel.config(text="%04d/%04d" % (self.cur, self.total))

        # load labels
        self.clearBBox()
        self.imagename = os.path.splitext(os.path.basename(imagepath))[0]
        print(self.imagename)
        labelname = self.imagename + '.txt'
        self.labelfilename = os.path.join(self.outDir, labelname)
        bbox_cnt = 0
        if os.path.exists(self.labelfilename):
            with open(self.labelfilename) as f:
                for (i, line) in enumerate(f):
                    t = line.split()
                    tmp = []
                    for (j, elm) in enumerate(t):
                        if j == 0:
                            tmp.append(int(elm.strip()))
                        else:
                            tmp.append(float(elm.strip()))
                    # here is for close mosaic from yolov5 or above
                    if len(tmp) == 5: # bbox for old version
                        print(tmp)
                        cx = int(tmp[1] * self.mainPanel.winfo_width())
                        cy = int(tmp[2] * self.mainPanel.winfo_height())
                        bw = int(tmp[3] * self.mainPanel.winfo_width())
                        bh = int(tmp[4] * self.mainPanel.winfo_height())
                        self.bboxList.append(tuple(tmp))
                        fx1 = cx - bw/2.0
                        fy1 = cy - bh/2.0
                        fx2 = cx + bw/2.0
                        fy2 = cy + bh/2.0
                        x1 = int(fx1)
                        y1 = int(fy1)
                        x2 = int(fx2)
                        y2 = int(fy2)
                        print(fx1, fy1, fx2, fy2, cx, cy, bw, bh)
                    else:
                        print(tmp)
                        fx1 = tmp[1] * self.mainPanel.winfo_width()
                        fy1 = tmp[2] * self.mainPanel.winfo_height()
                        fx2 = tmp[5] * self.mainPanel.winfo_width()
                        fy2 = tmp[6] * self.mainPanel.winfo_height()
                        cx = (tmp[1] + tmp[5])/2.0
                        cy = (tmp[2] + tmp[6])/2.0
                        bw = tmp[5] - tmp[1]
                        bh = tmp[6] - tmp[2]
                        new_tmp = [tmp[0], cx, cy, bw, bh]
                        self.bboxList.append(tuple(new_tmp))
                        x1 = int(fx1)
                        y1 = int(fy1)
                        x2 = int(fx2)
                        y2 = int(fy2)
                        print(fx1, fy1, fx2, fy2, cx, cy, bw, bh)

                    tmpId = self.mainPanel.create_rectangle(x1, y1, x2, y2,
                                                            width=2,
                                                            outline=COLORS[(len(self.bboxList) - 1) % len(COLORS)])
                    # print tmpId
                    self.bboxIdList.append(tmpId)
                    self.listbox.insert(END, '%s : (%d, %d) -> (%d, %d)' % (self.cla_can_temp[tmp[0]], x1, y1, x2, y2))
                    self.listbox.itemconfig(len(self.bboxIdList) - 1,
                                            fg=COLORS[(len(self.bboxIdList) - 1) % len(COLORS)])

    def saveImage(self):
        print(f"Writing filename: {self.labelfilename}")
        with open(self.labelfilename, 'w') as f:
            # f.write('%d\n' % len(self.bboxList))
            for bbox in self.bboxList:
                f.write(' '.join(map(str, bbox)) + '\n')
        print(f'Image No. {self.cur} saved')

    def mouseClick(self, event):
        if self.STATE['click'] == 0:
            self.STATE['x'], self.STATE['y'] = event.x, event.y
        else:
            x1, x2 = min(self.STATE['x'], event.x), max(self.STATE['x'], event.x)
            y1, y2 = min(self.STATE['y'], event.y), max(self.STATE['y'], event.y)
            rx1 = x1 / self.mainPanel.winfo_width()
            rx2 = x2 / self.mainPanel.winfo_width()
            ry1 = y1 / self.mainPanel.winfo_height()
            ry2 = y2 / self.mainPanel.winfo_height()
            if rx1 < 0.0:
                rx1 = 0.0
            if ry1 < 0.0:
                ry1 = 0.0
            if rx2 > 1.0:
                rx2 = 1.0
            if ry2 > 1.0:
                ry2 = 1.0
            cx = (rx1 + rx2) / 2.0
            cy = (ry1 + ry2) / 2.0
            bw = rx2 - rx1
            bh = ry2 - ry1
            self.bboxList.append((self.classcandidate.current(), cx, cy, bw, bh))
            self.bboxIdList.append(self.bboxId)
            self.bboxId = None
            self.listbox.insert(END, '%s : (%d, %d) -> (%d, %d)' % (self.classcandidate.get(), x1, y1, x2, y2))
            self.listbox.itemconfig(len(self.bboxIdList) - 1, fg=COLORS[(len(self.bboxIdList) - 1) % len(COLORS)])
        self.STATE['click'] = 1 - self.STATE['click']

    def mouseMove(self, event):
        self.disp.config(text='x: %d, y: %d' % (event.x, event.y))
        if self.tkimg:
            if self.hl:
                self.mainPanel.delete(self.hl)
            self.hl = self.mainPanel.create_line(0, event.y, self.tkimg.width(), event.y, width=2)
            if self.vl:
                self.mainPanel.delete(self.vl)
            self.vl = self.mainPanel.create_line(event.x, 0, event.x, self.tkimg.height(), width=2)
        if 1 == self.STATE['click']:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)
            self.bboxId = self.mainPanel.create_rectangle(self.STATE['x'], self.STATE['y'], \
                                                          event.x, event.y, \
                                                          width=2, \
                                                          outline=COLORS[len(self.bboxList) % len(COLORS)])

    def cancelBBox(self, event):
        if 1 == self.STATE['click']:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)
                self.bboxId = None
                self.STATE['click'] = 0

    def delBBox(self):
        sel = self.listbox.curselection()
        if len(sel) != 1:
            return
        idx = int(sel[0])
        self.mainPanel.delete(self.bboxIdList[idx])
        self.bboxIdList.pop(idx)
        self.bboxList.pop(idx)
        self.listbox.delete(idx)

    def clearBBox(self):
        for idx in range(len(self.bboxIdList)):
            self.mainPanel.delete(self.bboxIdList[idx])
        self.listbox.delete(0, len(self.bboxList))
        self.bboxIdList = []
        self.bboxList = []

    def prevImage(self, event=None):
        self.saveImage()
        if self.cur > 1:
            self.cur -= 1
            self.loadImage()

    def nextImage(self, event=None):
        self.saveImage()
        if self.cur < self.total:
            self.cur += 1
            self.loadImage()

    def gotoImage(self):
        idx = int(self.idxEntry.get())
        if 1 <= idx and idx <= self.total:
            self.saveImage()
            self.cur = idx
            self.loadImage()

    def setClass(self):
        self.currentLabelclass = self.classcandidate.get()
        print('set label class to :', self.currentLabelclass)


if __name__ == '__main__':
    root = Tk()
    tool = LabelTool(root)
    root.resizable(width=True, height=True)
    root.mainloop()
