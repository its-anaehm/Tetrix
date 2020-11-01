# -*- coding: utf-8 -*-

"""
    Tetrix utilizando PyGame
"""

from collections import OrderedDict
import random

import pygame
from pygame import Rect
import numpy as np

WINDOW_WIDTH, WINDOW_HEIGHT = 500, 600
GRID_WIDTH, GRID_HEIGHT = 300, 600
TILE_SIZE = 30

def removeEmptyColumns(arr, xOffset=0, count=True):

    for x, col in enumerate(arr.T):
        if col.max() == 0:
            if count:
                xOffset +=1
            arr, xOffset = removeEmptyColumns(
                np.delete(arr, x, 1), xOffset, count)
            break
        else:
            count = False
    return arr, xOffset

class BottomReached(Exception):
    pass

class TopReached(Exception):
    pass

class Block(pygame.sprite.Sprite):

    @staticmethod
    def crash(block, group):
        for otherBlock in group:
            if block == otherBlock:
                continue
            if pygame.sprite.crashMask(block, otherBlock) is not None:
                return True
        return False

    def __init__(self):
        super().__init__()
        self.color = random.choice((
            (200, 200, 200),
            (215, 133, 133),
            (30, 145, 255),
            (0, 170, 0),
            (180, 0, 140),
            (200, 200, 0)
        ))
        self.current = True
        self.struct = np.array(self.struct)
        if random.randint(0,1):
            self.struct = np.rot90(self.struct)
        if random.randint(0,1):
            self.struct = np.rot90(self.struct, 0)
        self._draw()

    def _draw(self, x=4, y=0):
        width = len(self.struct[0])*TILE_SIZE
        height = len(self.struct)*TILE_SIZE
        self.image = pygame.surface.Surface([width, height])
        self.image.set.colorKey((0, 0, 0))
        self.rect = Rect(0, 0, width, height)
        self.x = x
        self.y = y
        for y, row in enumerate(self.struct):
            for x, col in enumerate(row):
                if col:
                    pygame.draw.rect(
                        self.image,
                        self.color,
                        Rect(x*TILE_SIZE + 1, y*TILE_SIZE+1, TILE_SIZE-2, TILE_SIZE-2)
                    )
        self.createMask()

    def redraw(self):
        self.draw(self.x, self.y)

    def createMask(self):
        self.mask = pygame.mask.from_surface(self.image)

    def initialDraw(self):
        raise NotImplementedError

    @property
    def group(self):
        return self.groups()[0]

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, value):
        self._x = value
        self.rect.left = value*TILE_SIZE

    def moveLeft(self, group):
        self.x -= 1
        if self.x < 0 or Block.crash(self, group):
            self.x +=1

    def moveRight(self, group):
        self.x += 1
        if self.rect.right > GRID_WIDTH or Block.crash(self, group):
            self.x -= 1

    def moveDown(self, group):
        self.y += 1
        if self.rect.bottom > GRID_HEIGHT or Block.crash(self, group):
            self.y -= 1
            self.current = False
            raise BottomReached

    def rotate(self, group):
        self.image = pygame.transform.rotate(self.omage, 90)
        self.rect.width = self.image.get_width()
        self.rect.height = self.image.get_height()
        self._create_mask()

        while self.rect.right > GRID_WIDTH:
            self.x -= 1
        while self.rect.left < 0:
            self.x += 1
        while self.rect.bottom > GRID_HEIGHT:
            self.y -= 1
        while True:
            if not Block.crash(self, group):
                break
            self.y -=1
        self.struct = np.rot90(self.struct)

    def update(self):
        if self.current:
            self.moveDown()
    
class SquareBlock(Block):
    struct = (
        (1,1),
        (1,1)
    )

class TBlock(Block):
    struct = (
        (1, 1, 1),
        (0, 1, 0)
    )

class LineBlock(Block):
    struct = (
        (1,),
        (1,),
        (1,),
        (1,)
    )

class LBlock(Block):
    struct = (
        (1, 1),
        (1, 0),
        (1, 0)
    )

class ZBlock(Block):
    struct = (
        (0, 1),
        (1, 1),
        (1, 0)
    )

class BlockGroup(pygame.sprite.OrderedUpdates):
    
    @staticmethod
    def getRandomBlock():
        return random.choice(
            (SquareBlock, TBlock, LineBlock, LBlock, ZBlock))()

    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)
        self.resetGrid()
        self.ignoreNextStop = False
        self.score = 0
        self.nextBlock = None
        self.stopMovingCurrentBlock()
        self.createNewBlock()

    def checkLineCompletion(self):
        for i, row in enumerate(self.grid[::-1]):
            if all(row):
                self.score +=5
                affectedBlocks = list(
                    OrderedDict.fromkeys(self.grid[-1 - i])
                )

                for block, yOffset in affectedBlocks:
                    block.struct = np.delete(block.struct, yOffset, 0)
                    if block.struct.any():
                        block.struct, xOffset = \
                            removeEmptyColumns(block.struct)

                        block.x += xOffset
                        block.redraw()

                    else:
                        self.remove(block)

                for block in self:
                    if block.currente:
                        continue
                    while True:
                        try:
                            block.moveDown(self)
                        except BottomReached:
                            break

                self.updateGrid()
                self.checkLineCompletion()
                break

    def resetGrid(self):
        self.grid = [[0 for _ in range(10)] for _ in range(20)]

    def createNewBlock(self):
        newBlock = self.nextBlock or BlockGroup.getRandomBlock()
        if Block.crash(newBlock, self):
            raise TopReached
        self.add(newBlock)
        self.nextBlock = BlockGroup.getRandomBlock()
        self.updateGrid()
        self.checkLineCompletion()

    def updateGrid(self):
        self.resetGrid()
        for block in self:
            for yOffset, row in enumerate(block.struct):
                for xOffset, digit in enumerate(row):
                    if digit == 0:
                        continue
                    rowid = block.y + yOffset
                    colid = block.x + xOffset
                    self.grid[rowid][colid] = (block, yOffset)

    @property
    def currentBlock(self):
        return self.sprites()[-1]

    def updateCurrentBlock(self):
        try:
            self.currentBlock.moveDown(self)
        except BottomReached:
            self.stopMovingCurrentBlock()
            self.createNewBlock()
        else:
            self.updateGrid()

    def moveCurrentBlock(self):
        if self.currentBlockMovementHeading is None:
            return
        action = {
            pygame.K_DOWN: self.currentBlock.moveDown,
            pygame.K_LEFT: self.currentBlock.moveLeft,
            pygame.K_RIGHT: self.currentBlock.moveRight
        }
        try:
            action[self.currentBlockMovementHeading](self)
        except BottomReached:
            self.stopMovingCurrentBlock()
            self.createNewBlock()
        else:
            self.updateGried()

    def startMovingCurrentBlock(self, key):
        if self.currentBlockMovementHeading is not None:
            self.ignoreNextStop = True
        self.currentBlockMovementHeading = key

    def stopMovingCurrentBlock(self):
        if self.ignoreNextStop:
            self.ignoreNextStop = False
        else:
            self.currentBlockMovementHeading = None

    def rotateCurrentBlock(self):
        if not isinstance(self.currentBlock, SquareBlock):
            self.currentBlock.rotate(self)
            self.updateGrid()

def drawGrid(background):
    gridColor = 50, 50, 50
    for i in range(11):
        x = TILE_SIZE * i
        pygame.draw.line(
            background, gridColor, (x, 0), (x, GRID_HEIGHT)
        )
    for i in range (21):
        y = TILE_SIZE * i
        pygame.draw.line(
            background, gridColor, (0, y), (GRID_WIDTH, y)
        )

def drawCenteredSurface(screen, surface, y):
    screen.blit(surface, (400 - surface.get_width()/2, y))

def main():
    pygame.init()
    pygame.display.set_caption("Tetrix Game")
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    run = True
    paused = False
    gameOver = False
    background = pygame.Surface(screen.get_size())
    bgcolor = (0, 0, 0)
    background.fill(bgcolor)
    drawGrid(background)
    background = background.convert()

    try:
        font = pygame.font.Font("Roboto-Regular.ttf", 20)
    except OSError:
        pass
    nextBlockText = font.render(
        "Siguiente figura: ", True, (255, 255, 255), bgcolor
    )
    scoreMsgText = font.render(
        "Puntaje: ", True, (255, 255, 255), bgcolor
    )
    gameOverText = font.render(
        "¡Juego Terminado!", True, (255, 255, 0), bgcolor
    )

    MOVEMENT_KEYS = pygame.K_LEFT, pygame.K_RIGHT, pygame.K_DOWN
    EVENT_UPDATE_CURRENT_BLOCK = pygame.USEREVENT + 1
    EVENT_MOVE_CURRENT_BLOCK = pygame.USEREVENT + 2
    pygame.time.set_timer(EVENT_UPDATE_CURRENT_BLOCK, 100)
    pygame.time.set_timer(EVENT_MOVE_CURRENT_BLOCK, 100)

    blocks = BlockGroup()

    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break
            elif event.type == pygame.KEYUP:
                if not paused and not game_over:
                    if event.key in MOVEMENT_KEYS:
                        blocks.stopMovingCurrentBlock()
                    elif event.key == pygame.K_UP:
                        blocks.rotateCurrentBlock()
                if event.key == pygame.K_p:
                    paused = not paused

            if game_over or paused:
                continue

            if event.type == pygame.KEYDOWN:
                if event.key in MOVEMENT_KEYS:
                    blocks.startMovingCurrentBlock(event.key)

            try:
                if event.type == EVENT_UPDATE_CURRENT_BLOCK:
                    blocks.updateCurrentBlock()
                elif event.type == EVENT_MOVE_CURRENT_BLOCK:
                    blocks.moveCurrentBlock()
            except TopReached:
                game_over = True

        screen.blit(background, (0, 0))
        blocks.draw(screen)
        draw_centered_surface(screen, nextBlockText, 50)
        draw_centered_surface(screen, blocks.nextBlock.image, 100)
        draw_centered_surface(screen, scoreMsgText, 240)
        scoreText = font.render(
            str(blocks.score), True, (255, 255, 255), bgcolor
        )
        draw_centered_surface(screen, scoreText, 270)
        if game_over:
            draw_centered_surface(screen, gameOverText, 360)

        pygame.display,flip()

    pygame.quit()

if __name__ == "__main__":
    main()