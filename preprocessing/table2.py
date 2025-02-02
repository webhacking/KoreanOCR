import sys
import cv2
import numpy as np

def remove_dup_horiz(lines):
    res = []
    for index, (x1, y1, x2, y2) in enumerate(lines):
        if (index == 0):
            res.append(lines[0])
        else :
            x3, y3, x4, y4 = res[len(res)-1]
            if (x1!=x3 or y1!=y3 or x2!=x4 or y2!=y4):
                if (abs(y1-y3) <= 3) and (x1 >= x3) and (x2 <= x4):
                    continue
                res.append(lines[index])
                        
    return res
        
def remove_dup_vert(lines):
    res = []
    for index, (x1, y1, x2, y2) in enumerate(lines):
        if (index == 0):
            res.append(lines[0])
        else :
            x3, y3, x4, y4 = res[len(res)-1]
            if (x1!=x3 or y1!=y3 or x2!=x4 or y2!=y4):
                if (abs(x1-x3) <= 3) and (y1 >= y3) and (y2 <= y4):
                    continue
                res.append(lines[index])
    return res

def check_in_range(range_begin, range_end, point):
    if (point >= range_begin and point <= range_end):
        return True
    
    return False
        
def horiz_complement(horiz_lines):
    if (len(horiz_lines) == 0): return horiz_lines
    last_lines = []
    
    last_line =  horiz_lines[len(horiz_lines)-1]
    last_lines.append(last_line)
    lasty = last_line[1]
    
    for i in range(len(horiz_lines)-2, 0, -1):
        line = horiz_lines[i]
        if line[1] <= lasty+3 and line[1] >= lasty-3:
            last_lines.append(line)
        else:
            break
    
    if (len(last_lines) <= 1): return horiz_lines
    
    last_lines.sort(key = lambda x: x[0])
    leftx = last_lines[0][0]
    rightx = last_lines[len(last_lines)-1][2]
    
    last_lines.sort(key = lambda x: x[1], reverse = True)
    newy = last_lines[0][1]
    
    newline = (leftx, newy, rightx, newy)
    new_horiz = horiz_lines[:len(horiz_lines)-len(last_lines)]
    new_horiz.append(newline)
    
    return new_horiz       
    
    
def get_cells(horiz_lines, vert_lines):
    cells = []
    
    for L1_index, (L1_x1, L1_y1, L1_x2, L1_y2) in enumerate(horiz_lines):
        if L1_index == len(horiz_lines) - 1: # or L1_index > 3:
            break
            
        range_begin = 0
        range_end = 0
        
        for L2_index, (L2_x1, L2_y1, L2_x2, L2_y2) in enumerate(horiz_lines):
            if L1_index >= L2_index:
                continue
            if check_in_range(range_begin, range_end, L1_x1) and check_in_range(range_begin, range_end, L1_x2):
                break
                
            if L1_x1 < L2_x2 and L1_x2 > L2_x1:
                # duplicated range (s_x .. l_x)
                s_x = L1_x1 - 1
                if (L1_x1 < L2_x1):
                    s_x = L2_x1 - 1
                l_x = L1_x2 + 1
                if (L1_x2 > L2_x2):
                    l_x = L2_x2 + 1
                    
                if check_in_range(range_begin, range_end, s_x+1) and check_in_range(range_begin, range_end, l_x-1):
                    continue
                    
                old_begin = range_begin
                old_end = range_end
                    
                if range_begin == 0 or range_begin > s_x:
                    range_begin = s_x
                if range_end == 0 or range_end < l_x:
                    range_end = l_x
                    
                cell =[0, L1_y1+1, 0, L2_y1-1]
                for V_x1, V_y1, V_x2, V_y2 in vert_lines:
                    if (V_y1 <= L1_y1+5 and V_y2 >= L2_y1-5 and V_x1 >= s_x-5 and V_x1 <= l_x+5) :
                        if cell[0] == 0:
                            cell[0] = V_x1 + 1
                        elif not check_in_range(old_begin, old_end, cell[0]+2):
                        #else : #if (V_x1 - cell[0]) > 3:
                            #print ("-------", cell[0], V_x1)
                            cells.append([cell[0], cell[1], V_x1 - 1, cell[3]])
                            cell[0] = V_x1 + 1
    
    return cells

def find_table(img):
    grayimg = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    binary_img = cv2.adaptiveThreshold(~grayimg, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 15, -2)
    
    horiz_img = binary_img.copy()
    vert_img = binary_img.copy()
    
    scale = 10;
    
    # horizontal lines
    horizontalsize = int(horiz_img.shape[0] / scale)
    horizontalStructure = cv2.getStructuringElement(cv2.MORPH_RECT,(horizontalsize, 1))
    horiz_img = cv2.erode(horiz_img, horizontalStructure, iterations = 1)
    horiz_img = cv2.dilate(horiz_img, horizontalStructure, iterations = 1)
    edges = cv2.Canny(horiz_img, 100, 200, apertureSize=3)
    _, contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    horiz_lines = []
    mask = np.zeros((img.shape), np.uint8)
    for cnt in contours:
        x,y,w,h = cv2.boundingRect(cnt)
        y = int(y + h / 2)
        horiz_lines.append([x,y,x+w,y])
        #cv2.rectangle(mask,(x,y),(x+w,y+h),(0,255,0), 1)
    
    horiz_lines = np.array(horiz_lines).tolist()
    horiz_lines.sort(key=lambda x: x[2]-x[0], reverse=True)
    horiz_lines.sort(key=lambda x: x[1])
    horiz_lines = remove_dup_horiz(horiz_lines)
    horiz_lines = horiz_complement(horiz_lines)
    #print("horiz", horiz_lines)
    
    #DEBUG
    """
    for x1, y1, x2, y2 in horiz_lines:
        cv2.line(mask, (x1,y1), (x2,y2), (0,255,0), 1)
    """

    # vertical lines
    #verticalsize = int(vert_img.shape[1] / scale)
    verticalsize = 20  # 짧은 세로선이 존재(20px 이상이면 세로선으로 간주)
    verticalStructure = cv2.getStructuringElement(cv2.MORPH_RECT, (1, verticalsize))
    vert_img = cv2.erode(vert_img, verticalStructure, iterations=1)
    vert_img = cv2.dilate(vert_img, verticalStructure, iterations=1)
    edges = cv2.Canny(vert_img, 100, 200, apertureSize=3)
    _, contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    vert_lines = []
    for cnt in contours:
        x,y,w,h = cv2.boundingRect(cnt);
        x = int(x + w / 2)
        vert_lines.append([x,y,x,y+h])
        
    vert_lines = np.array(vert_lines).tolist()
    vert_lines.sort(key=lambda x: x[3]-x[1], reverse=True)
    vert_lines.sort(key=lambda x: x[0])
    vert_lines = remove_dup_vert(vert_lines)
    #print("vert", vert_lines)
    
    #DEBUG
    """
    for x1, y1, x2, y2 in vert_lines:
        cv2.line(mask, (x1,y1), (x2,y2), (0,0,255), 1)
    """
    
    cells = get_cells(horiz_lines, vert_lines)
    #print ("cells", cells)
    
    #DEBUG
    """
    for x1, y1, x2, y2 in cells:
        cv2.rectangle(mask, (x1,y1), (x2,y2), (255,255,0), 1)
    
    global number
    cv2.imwrite("table2_res%d.png" % number, mask)
    number += 1
    """
    return cells

number = 0

    
if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("1 argument needed: <image path>")
        exit(0)
    
    path = sys.argv[1]
    img = cv2.imread(path)
    grayimg = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    binary_img = cv2.adaptiveThreshold(~grayimg, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 15, -2)
    
    horiz_img = binary_img.copy()
    vert_img = binary_img.copy()
    
    scale = 15;
    
    # horizontal lines
    horizontalsize = int(horiz_img.shape[0] / scale)
    horizontalStructure = cv2.getStructuringElement(cv2.MORPH_RECT,(horizontalsize, 1))
    horiz_img = cv2.erode(horiz_img, horizontalStructure, iterations = 1)
    horiz_img = cv2.dilate(horiz_img, horizontalStructure, iterations = 1)
    edges = cv2.Canny(horiz_img, 100, 200, apertureSize=3)
    _, contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    horiz_lines = []
    mask = np.zeros((img.shape), np.uint8)
    for cnt in contours:
        x,y,w,h = cv2.boundingRect(cnt)
        y = int(y + h / 2)
        horiz_lines.append([x,y,x+w,y])
        #cv2.rectangle(mask,(x,y),(x+w,y+h),(0,255,0), 1)
    
    horiz_lines = np.array(horiz_lines).tolist()
    horiz_lines.sort(key=lambda x: x[1])
    horiz_lines = remove_dup_horiz(horiz_lines)
    #print(horiz_lines)
    
    #for x1, y1, x2, y2 in horiz_lines:
    #    cv2.line(mask, (x1,y1), (x2,y2), (0,255,0), 1)

    # vertical lines
    verticalsize = int(vert_img.shape[1] / scale)
    verticalStructure = cv2.getStructuringElement(cv2.MORPH_RECT, (1, verticalsize))
    vert_img = cv2.erode(vert_img, verticalStructure, iterations=1)
    vert_img = cv2.dilate(vert_img, verticalStructure, iterations=1)
    edges = cv2.Canny(vert_img, 100, 200, apertureSize=3)
    _, contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    vert_lines = []
    for cnt in contours:
        x,y,w,h = cv2.boundingRect(cnt);
        x = int(x + w / 2)
        vert_lines.append([x,y,x,y+h])
        
    vert_lines = np.array(vert_lines).tolist()
    vert_lines.sort()
    vert_lines = remove_dup_vert(vert_lines)

    #print("----------------")
    #print(vert_lines);
    
    #for x1, y1, x2, y2 in vert_lines:
    #    cv2.line(mask, (x1,y1), (x2,y2), (0,0,255), 1)
    
    cells = get_cells(horiz_lines, vert_lines)
    #print("----------------")
    #print(cells)
    
    for x1, y1, x2, y2 in cells:
        cv2.rectangle(mask, (x1,y1), (x2,y2), (255,255,0), 1)
    
    cv2.imwrite("table2_res.png", mask)
    
