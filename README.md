# Sphere

Sphere is a small software aimed at easily projecting rectangular images of planetary surfaces into azimuthal equidistant images and manipulating them in a simple interface. 

In the end, both projection and image manipulation will be done through the same interface.

## Why azimuthal equidistant projection ?

Because this is the type of projection required for a project at IRAP aimed at projecting among other things planetary surfaces into a semi opaque sphere. Most images of planetray surfaces are usually found as rectangular images and therefore need to be projected into azimuthal equidistant projection so that the system optics can reconstruct the spherical shape.

## What can it do for now ?

Not much... Here is a list of things it does and should (shall ?) do in the future

- [x] Open configuration files to load the project parameters
- [x] Open projected images given the latitude and longitude
- [x] Update the image when the latitude and/or longitude is/are changed
- [x] Interact with the image in a simple way using the mouse (not very natural yet)
- [ ] Interact in a natural and smooth way using the mouse
- [ ] Have its own interface to perform the projection (for now it is hidden/unusuable in backend code)
- [ ] Have a smoother interface for startup loading
- [ ] Be able to save the current state of the application to easily load back later on
- [ ] Detach/dupplicate the image into another window (with no/very few buttons and lebls) to have it fullscreen on another monitor for instance
- [ ] Automatically rotate the image along the latitude or longitude at a given speed

So still quite a lot of work to do. But if you want to have a try, you can download the project and launch it. It should ask you whether you want to open a venus.yaml file which is located in the example directory. In practice, if you say yes, the data should be loaded and manipulated.

## What do I need to run it ?

Obviously python3, one of the latest versions would be preferable. Tkinter and ttk should be installed by default in theory. Additionnaly, here are the following librairies that you need to install:

- numpy
- matplotlib
- pyyaml
- glob
- __mpl_toolkits.basemap__ (this is the backbone of the projection part of the code, though it is not mandatory for manipulating images)

The code + icons are actually quite light weight. Most of the size comes from the example, which for the moment is mandatory if you want to try this software, but will not in future versions. So hopefully, the example will be moved somewhere else and this project will be much less heavy than it is now.

__This software has only been tested on an Ubuntu 20.04.1 machine.__
