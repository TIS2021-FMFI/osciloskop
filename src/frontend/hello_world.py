import tkinter

w = 200
h = 200

win = tkinter.Canvas(width=w, height=h)
win.pack()

tag = 'click'
x = w / 2
y = h / 4
a = 50
b = 25

font = ("Arial", 20, "bold")

##########


win.create_rectangle(x - a, y - b, x + a, y + b, tag=tag, fill='darkgray')
win.create_text(x, y, text="Click", font=font, tag=tag)

hlwrld = -1


def fun():
    global hlwrld
    win.delete(hlwrld)
    hlwrld = win.create_text(w / 2, 3 * h / 4, text="Hello World", font=font)


win.tag_bind(tag, '<Button-1>', lambda event: fun())

tkinter.mainloop()
