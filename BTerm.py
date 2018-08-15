import pygame as pg, pyperclip, keyboard
from copy import copy

def reverse_color(col):
    """
        Reverses color
    """
    return pg.Color(255 - col[0], 255 - col[1], 255 - col[2])


def half_color(col):
    """
        Halves reversed color
    """
    col = reverse_color(col)
    return pg.Color(col[0] // 2, col[1] // 2, col[2] // 2)


class Timer:
    """ Timer
        start   : time at start
        duration: time to elapse
        passed(): time elapsed (bool)
    """
    def __init__(self, milli=0):
        self.start = pg.time.get_ticks()
        self.duration = milli

    def passed(self):
        return pg.time.get_ticks() - self.start >= self.duration


class Letter:
    """	Letter on screen
        size      : size of letter
        letter    : string character
        pos       : screen position (vector/SPos)
        col       : color of letter
        rcol      : reverse of color
        __init__(): parameters: size, letter, pos, col
    """
    def __init__(self, size, letter, pos, col=(0,0,0)):
        self.size   = size
        self.letter = letter
        self.pos    = pos
        self.col    = col
        self.rcol   = reverse_color(col)


class SPos:
    """	Screen position
        size      : size of position
        x         : x position
        y         : y position
        xt        : true x position (size * x)
        yt        : true y position (size * y)
        letter    : letter on position (Can be None)
        hovering(): mouse hovering over
        clicked (): hovering and mouse button down
        transpos(): translate pixel position to SPos (static)
        __init__(): parameters: size, x, y, letter
        __eq__  (): equals operator
        __str__ (): string representation
        __repr__(): same as __str__
    """
    def __init__(self, size, x, y, letter=None):
        self.size   = size
        self.x      = x
        self.y      = y
        self.xt     = size * x / 2
        self.yt     = size * y
        self.letter = letter

    def hovering(self):
        return (self.xt<=pg.mouse.get_pos()[0]<=self.xt+self.size/2)and(self.yt<=pg.mouse.get_pos()[1]<=self.yt+self.size)

    def clicked(self, mButton=0):
        return pg.mouse.get_pressed()[mButton] and self.hovering()

    @staticmethod
    def transpos(size, x, y):
        return SPos(size, x//size*2, y//size)

    def __eq__(self, other):
        if type(other) == SPos:
            return self.size == other.size and self.x == other.x and self.y == other.y
        elif type(other) in [list, tuple]:
            return self.size == other[0] and self.x == other[0] and self[0] == other.y
        return False

    def __str__(self):
        return "SPos(" + str(self.size) + ", " + str(self.x) + ", " + str(self.y) + ")"

    __repr__ = __str__


class BTerm:
    """ Terminal
        clock           : PyGame clock
        screen          : PyGame display
        font            : PyGame font
        w               : letter width (lsize * w)
        h               : letter height(lsize * h)
        wt              : pixel width (must be devisable by lsize)
        ht              : pixel height(must be devisable by lsize)
        aa              : antialias (bool)
        frame           : current frame number
        lsize           : size of positions
        bgcol           : background color
        rbgcol          : reversed background color
        cursor          : cursor position (vector) (Do not edit directly, use setcursor() instead)
        selected        : selected area
        start           : start of the selected area
        selecting       : selecting area (bool)
        positions       : vector of positions
        scrollpos       : scrolling position
        lastcopied      : text last copied (starts as "")
        active          : terminal status (bool)
        stretch         : amount of extra lines below bottom
        print         (): generates letters for relevant positions
        endl          (): equivlent to \n in regular print (function)
        input         (): gets input from user
        sprint        (): prints without clearing selection
        events        (): handles PyGame events
        draw          (): draws info on the screen
        update        (): updates screen and handles logic
        setcursor     (): set the cursor to a position
        clearselection(): clears area from selection
        __init__      (): parameters: w, h, lsize, bgcol, font, aa
    """
    clock = pg.time.Clock()

    def __init__(self, w=700, h=700, lsize=15, bgcol=pg.Color(0,0,0), font="cmd.ttf", aa=False):
        if w % lsize != 0 or h % lsize != 0:
            raise ValueError("Width and Height of terminal must be divisible by letter size.")
        pg.init()
        self.screen     = pg.display.set_mode((w+16, h))
        self.font       = pg.font.Font(font, lsize)
        self.w          = w//lsize * 2
        self.h          = h//lsize
        self.wt         = w
        self.ht         = h
        self.aa         = aa
        self.frame      = 0
        self.lsize      = lsize
        self.bgcol      = bgcol
        self.rbgcol     = reverse_color(bgcol)
        self.cursor     = [0,0]
        self.selecting  = False
        self.selected   = []
        self.start      = None
        self.positions  = [[SPos(lsize, x, y) for y in range(self.h)] for x in range(self.w)]
        self.scrollpos  = 0
        self.stretch    = 0
        self.lastcopied = ""
        self.active     = True

    def setcursor(self, x, y):
        self.cursor[0] = x
        self.cursor[1] = y
        if self.cursor[1] >= self.h + self.stretch:
            self.scrollpos = -((self.stretch+(self.cursor[1] - (self.h + self.stretch) + 1)) * self.lsize) if self.scrollpos == -(self.stretch * self.lsize) else self.scrollpos
            for x in range(self.h + self.stretch, self.cursor[1] + 1):
                for y,elem in enumerate(self.positions):
                    self.positions[y].append(SPos(self.lsize, y, x))
            self.stretch += self.cursor[1] - (self.h + self.stretch) + 1

    def sprint(self, txt, endline=False, color=None):
        for x in txt:
            self.positions[self.cursor[0]][self.cursor[1]].letter = None if x is None else Letter(self.lsize, x, copy(self.cursor), self.rbgcol if color is None else color)
            if self.cursor[0] == self.w-1:
                self.__endl()
            else:
                self.cursor[0] += 1
        if endline:
            self.endl()

    def print(self, txt, endline=False, color=None):
        self.sprint(txt, endline, color)
        self.clearselction()

    def __endl(self):
        self.setcursor(0, self.cursor[1] + 1)

    def endl(self):
        self.positions[self.cursor[0]][self.cursor[1]].letter = Letter(self.lsize, "\r\n", copy(self.cursor))
        self.__endl()
        self.clearselction()

    def input(self, text="", endline=False, color=None):
        inp=""
        keys=[]
        self.print(text, endline, color)
        cursor = copy(self.cursor)
        while t.active:
            inp = "".join(list(keyboard.get_typed_strings(keys)))
            self.sprint(inp)
            if "enter" in [x.name for x in keys]:
                self.endl()
                break
            self.sprint([None] * (self.w - len(inp)))
            self.cursor = copy(cursor)
            keyboard.start_recording()
            self.update()
            keys += keyboard.stop_recording()
        return inp

    def draw(self):
        if self.active:
            self.screen.fill(self.bgcol)
            for x in self.positions:
                for y in x:
                    inside = False
                    if len(self.selected):
                        if self.selected[1].y > y.y > self.selected[0].y:
                            inside = True
                        elif y.y == self.selected[0].y and y.x >= self.selected[0].x and ((y.x <= self.selected[1].x) if self.selected[0].y == self.selected[1].y else True):
                            inside = True
                        elif y.y == self.selected[1].y and y.x <= self.selected[1].x and ((y.x >= self.selected[0].x) if self.selected[0].y == self.selected[1].y else True):
                            inside = True

                    if y.letter is not None:
                        if y.letter.letter != "\r\n":
                            self.screen.blit(
                                self.font.render(y.letter.letter, self.aa, self.bgcol if inside else y.letter.col, self.rbgcol if inside else self.bgcol), (y.xt, y.yt + self.scrollpos))
                    elif inside:
                        surf = pg.Surface((y.size // 2, y.size))
                        surf.fill(self.rbgcol)
                        self.screen.blit(surf, (y.xt, y.yt + self.scrollpos))
            content_size = (self.stretch * self.lsize) + self.ht
            grip_size = self.ht * (self.ht / content_size)
            if grip_size < self.lsize: grip_size = self.lsize
            if grip_size > self.ht: grip_size = self.ht
            grip_pos = (self.ht - grip_size) * (self.scrollpos / (content_size - (self.ht if content_size > self.ht else 1)))
            grip = pg.Surface((16, grip_size))
            grip.fill(half_color(self.bgcol))
            self.screen.blit(grip, (self.wt, -grip_pos))

            pg.display.flip()

    def __events(self):
        if self.active:
            for x in pg.event.get():
                if x.type == pg.QUIT:
                    self.active = False
                    pg.quit()
                elif x.type == pg.KEYDOWN:
                    keys = pg.key.get_pressed()
                    if keys[pg.K_ESCAPE]:
                        self.active = False
                        pg.quit()
                    if keys[pg.K_LCTRL] and keys[pg.K_c]:
                        self.lastcopied = ""
                        for y in range(self.selected[0].y, self.selected[1].y + 1):
                            for z in range(self.selected[0].x if y == self.selected[0].y else 0,
                                           (self.selected[1].x + 1) if y == self.selected[1].y else len(self.positions)):
                                letter = self.positions[z][y].letter
                                if letter is not None:
                                    self.lastcopied += letter.letter
                        pyperclip.copy(self.lastcopied)
                        self.clearselction()
                        print(self.lastcopied)
                if x.type == pg.MOUSEBUTTONDOWN:
                    if x.button == 1:
                        self.start = SPos.transpos(self.lsize, pg.mouse.get_pos()[0], pg.mouse.get_pos()[1])
                        self.selected = [self.start, self.start]
                        self.selecting = True
                    elif x.button == 4:
                        self.scrollpos += self.lsize if self.scrollpos < 0 else 0
                    elif x.button == 5:
                        self.scrollpos -= self.lsize if self.scrollpos > -(self.stretch * self.lsize) else 0
                if self.selecting:
                    pos = SPos.transpos(self.lsize, pg.mouse.get_pos()[0], pg.mouse.get_pos()[1])
                    if pos.y < self.start.y or (pos.y == self.start.y and pos.x < self.start.x):
                        self.selected[1] = self.start
                        self.selected[0] = pos
                    elif pos.y > self.start.y or (pos.y == self.start.y and pos.x > self.start.x):
                        self.selected[0] = self.start
                        self.selected[1] = pos
                if x.type == pg.MOUSEBUTTONUP:
                    self.selecting = False

    def clearselction(self):
        self.selecting = False
        self.selected = []
        self.start = None

    def update(self):
        if self.active:
            self.frame += 1
            self.__events()
            self.draw()
            self.clock.tick(60)