import re
import math
import numpy as np
import time
#135
#17.5
# -----------------------------------------------------------------------------------------
# Transformation Settings
# -----------------------------------------------------------------------------------------
FILE_NAME = 'EN_testhook_hb.gcode'                          # filename including extension
FOLDER_NAME = 'gcodes/'                              # name of the subfolder in which the gcode is located
TRANSFORMATION_CODE = "0020016"
if TRANSFORMATION_CODE!="":
    LAYER_TYPE=int(TRANSFORMATION_CODE[0])
    MIDDLE_LAYER_DIRECTION=int(TRANSFORMATION_CODE[1])
    LAYER_PART_RADIUS=int(TRANSFORMATION_CODE[2:5])
    CONE_ANGLE=int(TRANSFORMATION_CODE[5:7])
else:
    CONE_ANGLE = 35#16                                      # transformation angle
    LAYER_PART_RADIUS=3
    LAYER_TYPE = 0#0=triangle, 1=circle
    MIDDLE_LAYER_DIRECTION = 0 #0=outward 1=inward

# if using cura subtact like 5, you might need trial and error to make it work, if it doesnt look right, try again
if LAYER_TYPE==0:
    PLATE_X,PLATE_Y = 110-(52.43/2),110                            # moves your gcode away from the origin into the center of the bed (usually bed size / 2)                                       
else:
    PLATE_X,PLATE_Y = 110,110
X_MOVE,Y_MOVE = 0,0                                # moves the modle away from the center of the bed if wanted
FIRST_LAYER_HEIGHT = 0.12                            # moves all the gcode up to this height. Use also for stacking

def move(x,y,c,n):
    # moves the modle to the origin, or away from it bassed on c, -1 or 1
    if n==1:
        x,y = x+(c * PLATE_X),y+(c* PLATE_Y)
    if n==2:
        x,y = x+(c * PLATE_Y),y+(c* PLATE_X+50)
    return x,y

def transform(x,y,z,e):
    x,y = move(x,y,-1,1)
    if LAYER_TYPE==0:
        if x<=0:
            x=0.0000000000000000001
        if z<=0:
            z=0.0000000000000000001
        nz=z
        ox=x
        x = np.sqrt(x**2+z**2)*np.cos(np.radians(np.degrees(np.arctan(z/x))-CONE_ANGLE))
        z = np.sqrt(ox**2+z**2)*np.sin(np.radians(np.degrees(np.arctan(z/ox))-CONE_ANGLE))+5.7#+12+6.1# + 6.0
        x,y=-y,x
        y=-y
    else:
        z = z - dist_center_transform(x,y,z)
    x,y = move(x,y,1,2)
    #if nz<=z:
    #    print(nz)

    if z<=0:
        z=0
    if e !=0:
        # combines all info to make new row
        row_new = "G1"+" X"+str(round(x+X_MOVE,3))+ " Y"+str(round(y+Y_MOVE,3))+" Z"+str(round(z+FIRST_LAYER_HEIGHT,3))+" E"+str(round(e*1.2,3))+"\n"
    else:
        row_new = "G0"+" X"+str(round(x+X_MOVE,3))+ " Y"+str(round(y+Y_MOVE,3))+" Z"+str(round(z+FIRST_LAYER_HEIGHT,3))+"\n"
    return row_new

def dist_center_transform(x,y,z):
    dist = np.sqrt(x**2 + z**2)
    val= (dist%LAYER_PART_RADIUS)
    num = (np.floor(dist/LAYER_PART_RADIUS)%2)*LAYER_PART_RADIUS
    if x==0 and y==0:
        return 0
    if LAYER_TYPE==0:
        if MIDDLE_LAYER_DIRECTION==0:
            c=LAYER_PART_RADIUS
        else:
            c=0
        if num==c:
            val = LAYER_PART_RADIUS-val
        return val*np.tan(np.radians(CONE_ANGLE)) + (-9.1) + 0.001*dist 
    elif LAYER_TYPE==1:
        if num==LAYER_PART_RADIUS:
            val = LAYER_PART_RADIUS-val
        return np.sqrt(LAYER_PART_RADIUS**2 - val**2)
    else:
        raise ValueError(f'{LAYER_TYPE} is not a admissible type for the transformation')

def change_e(data,i,x,y,z,e):
    i += 1
    pattern_X = r'X[-0-9]*[.]?[0-9]*'
    pattern_Y = r'Y[-0-9]*[.]?[0-9]*'
    pattern_Z = r'Z[-0-9]*[.]?[0-9]*'
    pattern_E = r'E[-0-9]*[.]?[0-9]*'
    pattern_G = r'\AG[1] '
    pattern_G0 = r'\AG[0] '

    g_match = re.search(pattern_G, data[i+1])
    g0_mathch = re.search(pattern_G0, data[i+1])
    x2, y2 = 0, 0
    z2 = 0
    e2 = 0
    #print(data[i+1],i)
    if g_match is None and g0_mathch is None:
        #print(i)
        return 0
    else:
        x_match = re.search(pattern_X, data[i+1])
        y_match = re.search(pattern_Y, data[i+1])
        #z_match = re.search(pattern_Z, data[i+1])
        e_match = re.search(pattern_E, data[i+1])
        #print(e_match)
        if x_match is None or y_match is None or e_match is None:
            #print(i)
            return 0
        else:
            #if z_match is not None:
            #    z2 = float(z_match.group(0).replace('Z', ''))
            x2 = float(x_match.group(0).replace('X', ''))
            y2 = float(y_match.group(0).replace('Y', ''))
            #e2 = float(e_match.group(0).replace('E', ''))

            distx = x-x2
            disty = y-y2
            dist = math.sqrt(distx**2+disty**2)
            
            distz=(math.tan(math.radians(CONE_ANGLE)) * math.sqrt(x**2+y**2))-(math.tan(math.radians(CONE_ANGLE)) * math.sqrt(x2**2+y2**2))
            change = math.sqrt(dist**2+distz**2) / dist
            #print(e)
            return round(change*e*1.2,5)

def backtransform_data(data):
    new_data = []

    # makes the pattern for re to look for in Gcode
    pattern_X = r'X[-0-9]*[.]?[0-9]*'
    pattern_Y = r'Y[-0-9]*[.]?[0-9]*'
    pattern_Z = r'Z[-0-9]*[.]?[0-9]*'
    pattern_E = r'E[-0-9]*[.]?[0-9]*'
    pattern_G = r'\AG[0] '
    pattern_G0 = r'\AG[1] '

    # sets important variables
    x_new, y_new = 0, 0
    z_layer = 0
    for i, row in enumerate(data):
        e_new = 0#####****************************need to be here, so dumb me not put
        # checks if the row is a G1 command
        g_match = re.search(pattern_G, row)
        g0_mathch = re.search(pattern_G0, row)

        if g_match is None and g0_mathch is None:
            new_data.append(row)
        else:
            # finds the matches according to the method astablished before
            x_match = re.search(pattern_X, row)
            y_match = re.search(pattern_Y, row)
            z_match = re.search(pattern_Z, row)
            e_match = re.search(pattern_E, row)


            if x_match is None and y_match is None and z_match is None :
                new_data.append(row)
            else:
                # gets the values from the matches and turns it into a float
                if z_match is not None:
                    z_layer = float(z_match.group(0).replace('Z', ''))
                if x_match is not None:
                    x_new = float(x_match.group(0).replace('X', ''))
                if y_match is not None:
                    y_new = float(y_match.group(0).replace('Y', ''))
                if e_match is not None:
                    e_new = float(e_match.group(0).replace('E', ''))
                
                # adds all updated rows to the list of all rows
                if LAYER_TYPE!=0:
                    e_new = change_e(data,i,x_new,y_new,z_layer,e_new)
                #print(e_new)
                new_data.append(transform(x_new,y_new,z_layer,e_new))
    return new_data


def main(path):
    # reads the file, and back-transforms it
    with open(path, 'r') as f_gcode:
        data = f_gcode.readlines()
    
    while True:
        data.pop(0)#remove(line[1])
        #print(line[0])
        if "; external" in data[0]:
            break
    
    data_bt = backtransform_data(data)#data_bt is data_backtransformed
    
    # turns the list of commands back into a gcode file
    data_bt_string = ' '.join(data_bt)# joins all lines
    data_bt = [row + ' \n' for row in data_bt_string.split('\n')]# splits it into separate lines
    data_bt_string = ''.join(data_bt)# rejoins the lines

    # makes the nes file and puts the gcode commands into it
    path_write = re.sub(r'gcodes', 'gcodes_backtransformed', path)
    path_write = re.sub(r'.gcode',f'_bt_{CONE_ANGLE}.gcode', path_write)
    with open(path_write, 'w+') as f_gcode_bt:
        f_gcode_bt.write(data_bt_string)
    return None

start_time = time.time()

main(FOLDER_NAME + FILE_NAME)

end_time = time.time()
print('Back-transformation time:', end_time - start_time)
