#!/usr/bin/env python3

from io import BytesIO
import tkinter as tk
import tkinter.filedialog
from paphra_tktable import table
from PIL import Image, ImageTk
from cairo import ImageSurface, Context, FORMAT_ARGB32
import shlex
import os

import gerber
from gerber.render.cairo_backend import GerberCairoContext
from gerber.render import RenderSettings, theme
from gerber.utils import listdir

class ComponentListGui(tk.ttk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        titles = [{'text': 'PN', 'width': 30, 'type': 'l'},
                  {'text': 'Description', 'width': 40, 'type': 'l'},
                  {'text': 'Count', 'width': 5, 'type': 'l'}]
        self.tb = table.Table(self, titles=titles,_keys_=["PN", "Description", "Count"], height=600)

    def add_components(self, components, layer):
        bom = []
        if self.tb.rows_list != None:
            self.tb.rows_list.clear()
        for c in components:
            if c["layer"] == layer:
                comp = {"PN": c["part_number"], "Description": c["description"], "Count": 1}
                bom_comp = next((item for item in bom if item["PN"] == comp["PN"]), None)
                if bom_comp == None:
                    bom.append(comp)
                else:
                    bom_comp["Count"] += 1
        self.tb.add_rows(bom)

class PcbGui(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack()

        self.ctx = GerberCairoContext(8)
        self.ctx.units = 'metric'

        self.layers = {}
        self.components = []
        # self.components = self.load_pickplace()
        self.layer = "TopLayer"

        # self.geometry("{}x{}".format(self._image_ref.width(), self._image_ref.height()))

        self.clist = ComponentListGui(self)
        # self.clist.add_components(self.components, self.layer)
        self.clist.pack(expand=True, side="right")

        self.label = tk.Label(self)
        self.label.pack(expand=True, side="left")
        # self.draw_component()

        self.bind('<ButtonRelease-1>', self.draw_component)

    def select_gerber_folder(self):
        dir = tk.filedialog.askdirectory(title="Select folder with Gerbers")
        self.layers = {}
        for infile in listdir(dir):
            path = os.path.join(dir, infile)
            if infile.lower().endswith('gbl'):
                self.layers['gbl'] = gerber.load_layer(path)
            if infile.lower().endswith('gtl'):
                self.layers['gtl'] = gerber.load_layer(path)
            if infile.lower().endswith('gtp'):
                self.layers['gtp'] = gerber.load_layer(path)
        self.draw_component()

    def set_layer(self, layer):
        self.layer = layer
        self.draw_component()
        self.clist.add_components(self.components, self.layer)

    def menubar(self, root):
        menubar = tk.Menu(root)
        pageMenu = tk.Menu(menubar)
        pageMenu.add_command(label="Open Gerber folder", command=self.select_gerber_folder)
        pageMenu.add_command(label="Open pick and place file", command=self.load_pickplace)
        menubar.add_cascade(label="File", menu=pageMenu)

        layerMenu = tk.Menu(menubar)
        layerMenu.add_radiobutton(label="Top Layer", command=lambda : self.set_layer("TopLayer"))
        layerMenu.add_radiobutton(label="Bottom Layer", command=lambda : self.set_layer("BottomLayer"))
        menubar.add_cascade(label="Layer", menu=layerMenu)

        helpMenu = tk.Menu(menubar, name="help")
        helpMenu.add_command(label="About")
        menubar.add_cascade(label="Help", menu=helpMenu)
        return menubar

    # def load_gerber(self):      
    #     self.layers = {}
    #     self.layers.append(gerber.load_layer('example.GTL'))
        # self.ctx.render_layers(layers, buffer, max_width=self.w, max_height=self.h, verbose=True)

    def draw_component(self, event=None):
        self.ctx.clear()
        
        if len(self.layers) > 0:
            if self.layer == "TopLayer":
                copper_settings = RenderSettings(color=theme.COLORS['black'], alpha=0.8, mirror=False)
                self.ctx.render_layer(self.layers["gtl"], settings=copper_settings, verbose=True)
                self.ctx.new_render_layer(mirror=False)
            if self.layer == "BottomLayer":
                copper_settings = RenderSettings(color=theme.COLORS['black'], alpha=0.8, mirror=True)
                self.ctx.render_layer(self.layers["gbl"], settings=copper_settings)
                self.ctx.new_render_layer(mirror=True)
            
            self.ctx._color =(1.0, 0.0, 1.0)
            layer = self.layer
            if self.clist.tb.selected_row != None:
                part_number = self.clist.tb.selected_row['PN']
            else:
                part_number = None
            for c in self.components:
                if (c['layer'] == layer) and (c['part_number'] == part_number):
                    print("{} {}".format(c['x_mm'],c['y_mm']))
                    self.ctx.render(gerber.primitives.Circle((c['x_mm'],c['y_mm']),1))
            self.ctx.flatten()
            buffer = BytesIO()
            self.ctx.dump(buffer)
            img = ImageTk.PhotoImage(Image.open(buffer))
            self.label.configure(image=img)
            self.label.image = img

    def load_pickplace(self):
        filename = tk.filedialog.askopenfilename(title="Select pick and place file")
        components = []
        filetype = "Kicad"
        with open(filename, "r") as ppfile:
            header_read = False
            for line in ppfile:
                line = shlex.split(line)
                if len(line) > 0:
                    if header_read == False:
                        # Try to determine the file type based on the contents
                        if line[0] == "Altium":
                            filetype = "Altium"
                        if line[0] == "Designator" or line[0] == "#":
                            header_read = True
                    else:
                        if filetype == "Altium":
                            component = {}
                            component['designator'] =  line[0]
                            component['part_number'] =  line[1]
                            component['x_mm'] = float(line[4][:-2])
                            component['y_mm'] = float(line[5][:-2])
                            component['layer'] = line[2]
                            component['description'] = line[7]
                            components.append(component)
                        elif filetype == "Kicad":
                            if len(line) > 6:
                                print(line)
                                component = {}
                                component['designator'] =  line[0]
                                component['part_number'] =  line[1]
                                component['x_mm'] = float(line[3])
                                component['y_mm'] = float(line[4])
                                component['layer'] = "TopLayer" if line[6] == "top" else "BottomLayer"
                                if component['layer'] == "BottomLayer":
                                    component['x_mm'] *= -1
                                component['description'] = line[2]
                                components.append(component)
        self.components = components
        self.clist.add_components(self.components, self.layer)


if __name__ == "__main__":
    root = tk.Tk()
    root.title('pickplaceviewer')
    root.option_add('*tearOff', False)

    app = PcbGui(master=root)

    menubar = app.menubar(root)
    root.config(menu=menubar)

    root.bind('<ButtonRelease-1>', app.draw_component)

    app.mainloop()

