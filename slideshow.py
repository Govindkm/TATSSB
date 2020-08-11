from tkinter import *
from PIL import Image, ImageTk
from os import path, mkdir, listdir
from itertools import cycle
import json
import random
from time import sleep

blank = 100
writedelay = 210000
watchdelay = 30000
counter=0
base_dir = path.dirname(path.abspath(__file__))
image_dir = path.join(base_dir, "images")

class Slider:
    def __init__(self, root):
        super().__init__()
        self.pictures=[ImageTk.PhotoImage(file=path.join(image_dir, "image_{}".format(str(1)+".jpg")))]
        self.hoarding = ImageTk.PhotoImage(file=path.join(image_dir, "hoarding.jpg"))
        self.blankimage = ImageTk.PhotoImage(file=path.join(image_dir, "blank.jpg"))
        print(self.pictures)
        if(path.isdir(image_dir)):
            print("Directory Exists")
            self.nop =  len([name for name in listdir(image_dir)]) - 2
            print("Number of images in folder is : " + str(self.nop))
            for i in range(2, self.nop):
                print(self.pictures)
                self.pictures.append(ImageTk.PhotoImage(file=path.join(image_dir, "image_{}".format(str(i)+".jpg"))))
            print("Congratulations.......Pictures Loaded!!!")
        else:
            print("Creating Image Directory")
            mkdir(image_dir, mode=0o777)
            print("Created!!! Please add jpeg files in format 'X.jpg' where X represents image number.")
            exit()
        self.root = root
        self.root.title("SSB TAT Slider")
        self.root.geometry("1280x720+0+0")
        print(self.slide())

    def showWriteLabel(self):
        global counter
        if(counter == 11):
            self.imglbl=Label(self.root, image=self.blankimage)
            self.imglbl.place(x=0,y=0)
            counter=counter+1
            self.imglbl.after(writedelay, self.showWriteLabel)   
        if(counter == 12):
            exit()

        self.writelabel = Label(self.root, image=self.hoarding)
        self.writelabel.place(x=0, y=0)
        counter=counter+1
        self.writelabel.after(writedelay, self.clearScreen)
        

    def clearScreen(self):
        self.imglbl=Label(self.root, image=self.blankimage)
        self.imglbl.place(x=0,y=0)
        self.imglbl.after(blank, self.slide)
        
        

    
    def slide(self):
        global counter
        read_data=None
        if(counter>=self.nop):
            print("Module Completed")
            exit()
        if path.isfile("read_data.json"):
            with open("read_data.json", "r") as file:
                read_data = json.load(file)
                print(read_data)
        else:
            read_data = {"readFiles" : None}
            with open("read_data.json", "w") as file:
                obj=json.dumps(read_data, indent=4)
                file.write(obj)
                print("read_data.json file created!!!")
        if(read_data['readFiles'] == None):
            read_data['readFiles']=[1]
            with open("read_data.json", "w") as file:
                obj=json.dumps(read_data, indent=4)
                file.write(obj)
            self.imglbl=Label(self.root, image=self.pictures[1])
            self.imglbl.place(x=0,y=0)
            self.imglbl.after(watchdelay, self.showWriteLabel)
        else:
            num = random.randint(1, self.nop-1)
            if num in read_data['readFiles']:
                self.clearScreen()
            else:
                read_data['readFiles'].append(num)
                with open("read_data.json", "w") as file:
                    obj=json.dumps(read_data, indent=4)
                    file.write(obj)
                self.imglbl=Label(self.root, image=self.pictures[num])
                self.imglbl.place(x=0,y=0)
                self.imglbl.after(watchdelay, self.showWriteLabel)
        

root = Tk()
obj=Slider(root)
root.mainloop()