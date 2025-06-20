# Ticker
I made this repository because I wanted to dynamically generate images to use them as texture in 3D game. 
To make ticker displays look like moving, the generated images are shifted gradually.
By operating NumPy.ndarray and memoryview, pixel values are partly got and changed to replace messages. 
The texts in the images are drawn by NumPy, cv2 and pillow.

When tried changing pixel values of the blue circular ticker display while shifting its image by using Intervals of Panda3D, the color change did not go well, resulting in lots of red, green, yellow pixels and no texts.It took many days to finally understand that I need to shift the image at every frame update in the method added by Pnada3D TaskMgr.

https://github.com/user-attachments/assets/00d25dc3-9cca-427a-84ec-d399ded79208

# Requirements
* Panda3D                1.10.15
* numpy                  2.2.2
* opencv-contrib-python  4.11.0.86
* opencv-python          4.11.0.86
* pillow                 11.1.0

# Environment
* Python  3.12.7
* Windows 11


# Usage

* Clone this repository with submodule.
```
git clone --recursive https://github.com/taKana671/Ticker.git
```

* Execute a command below on your command line.
```
>>>python display_message.py
```

* Input a new message in the entry box.
* Press [c]button to change the message in the circular ticker display to the new message.
* Press [s]button to change the message in the square ticker display to the new message.
* Press [v]button to change the message in the vertical ticker display to the new message.


