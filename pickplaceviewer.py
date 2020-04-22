#! /usr/bin/env -S pipenv run python

from io import BytesIO
import tkinter as tk
import tkinter.filedialog
from paphra_tktable import table
from PIL import Image, ImageTk
from cairo import ImageSurface, Context, FORMAT_ARGB32
import shlex


import gerber
from gerber.render.cairo_backend import GerberCairoContext
from gerber.render import RenderSettings, theme

class ComponentListGui(tk.ttk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        titles = [{'text': 'PN', 'width': 30, 'type': 'l'},
                  {'text': 'Description', 'width': 40, 'type': 'l'},
                  {'text': 'Count', 'width': 5, 'type': 'l'}]
        self.tb = table.Table(self, titles=titles,_keys_=["PN", "Description", "Count"], height=600)
    def add_components(self, components, layer):
        bom = []
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

        self.load_gerber()
        self.components = self.load_pickplace()
        self.layer = "TopLayer"

        # self.geometry("{}x{}".format(self._image_ref.width(), self._image_ref.height()))

        self.clist = ComponentListGui(self)
        self.clist.add_components(self.components, self.layer)
        self.clist.pack(expand=True, side="right")

        self.label = tk.Label(self)
        self.label.pack(expand=True, side="left")
        self.draw_component()

        self.bind('<ButtonRelease-1>', self.draw_component)

    def select_gerber_folder(self):
        tk.filedialog.askdirectory(title="Select folder with Gerbers")

    def menubar(self, root):
        menubar = tk.Menu(root)
        pageMenu = tk.Menu(menubar)
        pageMenu.add_command(label="Open Gerber folder", command=self.select_gerber_folder)
        menubar.add_cascade(label="File", menu=pageMenu)

        helpMenu = tk.Menu(menubar, name="help")
        helpMenu.add_command(label="About")
        menubar.add_cascade(label="Help", menu=helpMenu)
        return menubar

    def load_gerber(self):      
        self.layers = []
        self.layers.append(gerber.load_layer('example.GTL'))
        # self.ctx.render_layers(layers, buffer, max_width=self.w, max_height=self.h, verbose=True)

    def draw_component(self, event=None):
        self.ctx.clear()

        copper_settings = RenderSettings(color=theme.COLORS['black'], alpha=0.8, mirror=False)
        
        self.ctx.render_layer(self.layers[0], settings=copper_settings)
        self.ctx.new_render_layer(mirror=False)
        self.ctx._color =(1.0, 0.0, 1.0)
        layer = self.layer
        if self.clist.tb.selected_row != None:
            part_number = self.clist.tb.selected_row['PN']
        else:
            part_number = None
        for c in self.components:
            if (c['layer'] == layer) and (c['part_number'] == part_number):
                self.ctx.render(gerber.primitives.Circle((c['x_mm'],c['y_mm']),1))
        self.ctx.flatten()
        buffer = BytesIO()
        self.ctx.dump(buffer)
        img = ImageTk.PhotoImage(Image.open(buffer))
        self.label.configure(image=img)
        self.label.image = img

    def load_pickplace(self):
        components = []
        with open("example.txt", "r") as ppfile:
            header_read = False
            for line in ppfile:
                line = shlex.split(line)
                if len(line) > 0:
                    if header_read == False:
                        if line[0] == "Designator":
                            header_read = True
                    else:
                        component = {}
                        component['designator'] =  line[0]
                        component['part_number'] =  line[1]
                        component['x_mm'] = float(line[4][:-2])
                        component['y_mm'] = float(line[5][:-2])
                        component['layer'] = line[2]
                        component['description'] = line[7]
                        components.append(component)
        return components


if __name__ == "__main__":
    root = tk.Tk()
    root.option_add('*tearOff', False)

    app = PcbGui(master=root)

    menubar = app.menubar(root)
    root.config(menu=menubar)

    root.bind('<ButtonRelease-1>', app.draw_component)

    app.mainloop()

