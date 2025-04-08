# Python Codes

Python codes to perform molecular simulations with dots. 

## Dependencies:
1. pygame
2. Open-CV
3. numpy

## Description of each code
1. molecular_simulation-base.py: Base code for creating the environment, you can play around with settings
2. molecular_simulation-partition.py: Creates dots on one side of screen with wall partition in between that disappears after a while (controllable). Also, writes output video into MP4 format in 1080p.
3. molecular_simulation-partition-middle.py: Same as previous code, but dots are populated on both sides of the screen (sometimes dots cross over the wall, which I find funny because that's exactly what would happen in real world scenarios sometimes). Also, writes output in MP4 format
4. molecular_simulation-spatial.py: Code build on top of base, helps write the output into video format and increased resolution
5. molecular_simulation-temperature-increase.py: Slow molecules increase in speed as time passes, write video output in MP4 format.
6. molecular_simulation-thermal-conductivity.py: A hot wall to the left and cold wall to the right, with molecules in between. Molecules have initial velocity, which increases when they hit the hot wall and vice-versa.
7. molecular_simulation-viscosity.py: Top wall moves to the right at fixed speed, molecules move along with the wall and hit each other, transferring energy in process. Writes output in MP4 format.
