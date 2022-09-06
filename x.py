import tkinter as Tk

def countlines(event):
    (line, c) = map(int, event.widget.index("end-1c").split("."))
    print (line, c)

root = Tk.Tk()
root.geometry("200x200")
a = Tk.Text(root)
a.pack()
bindtags = list(a.bindtags())
bindtags.insert(2,"custom")
a.bindtags(tuple(bindtags))
a.bind_class("custom","<Key>", countlines)

root.mainloop()