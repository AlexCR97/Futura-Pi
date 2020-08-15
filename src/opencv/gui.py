import src.config as config

dim_boton_w = 100
dim_boton_h = 35
margin_botones = 10
color_boton = (255, 0, 0)


class Boton:
    def __init__(self, x, y, text, on_click, color):
        self.x1 = x
        self.y1 = y
        self.x2 = x + dim_boton_w
        self.y2 = y + dim_boton_h
        self.text = text
        self.on_click = on_click
        self.color = color
        self.top_left = (self.x1, self.y1)
        self.top_right = (self.x1 + dim_boton_w, self.y1)
        self.bottom_left = (self.x1, self.y1 + dim_boton_h)
        self.bottom_right = (self.x2, self.y2)
