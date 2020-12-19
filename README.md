# Sphere

Sphere is a small GUI aimed at easily projecting rectangular images of planetary surfaces into azimuthal equidistant images and manipulating them in a simple interface. 

Ultimately, both projection and image manipulation shall be done through the same interface such that even non-specialist can easily perform it.

![Interface](/interface.png)

## Why azimuthal equidistant projection ?

Because this is the type of projection required as input for IRAP EXPLOIT project aimed at projecting planetary surfaces into a real spherical surface. 

Since most images of planetary surfaces are usually found as rectangular images, one must project them into azimuthal equidistant projection so that the system optics can reconstruct the spherical shape.

## What can it do for now ?

Here is a list of things it does and shall do in the future:

- [x] Open configuration files to load the project parameters
- [x] Open projected images given the latitude and longitude
- [x] Update the image when the latitude and/or longitude is/are changed
- [x] Interact with the image in a simple way using the mouse (not very natural yet)
- [ ] Interact in a natural and smooth way using the mouse
- [ ] Have its own interface to perform the projection (for now it is hidden/unusuable in backend code)
- [x] Have a smoother interface for startup loading
- [ ] Be able to save the current state of the application to easily load back later on
- [x] Detach/dupplicate the image into another window (with no/very few buttons and lebls) to have it fullscreen on another monitor for instance
- [ ] Automatically rotate the image along the latitude or longitude at a given speed

## What do I need to run it ?

python3, one of the latest versions would be preferable. glob, tkinter and ttk should be installed by default in theory. Additionnaly, here are the following librairies that you need to install:

- [numpy](https://numpy.org/)
- [matplotlib](https://matplotlib.org/)
- [PyYAML](https://pyyaml.org/)

The code + icons are actually quite light weight. Most of the space comes from the example, which for the moment is mandatory if you want to try this software, but will not in future versions. So hopefully, the example will be moved somewhere else and this project will be much less heavy than it is now.

## Caveats

__This software has only been tested on an Ubuntu 20.04.1 machine.__

A couple of tests were performed on a MAC OSX machine. The threading used to catch SIGINT does not work properly on MAC and is therefore disabled for now. Plenty of issues appear when running this software on a MAC OSX machine. These shall be dealt with once the bulge of the code has been completed. 

Tests on a windows machine should arrive sometimes in the 'near' future as well.
