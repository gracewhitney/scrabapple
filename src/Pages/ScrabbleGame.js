import React from 'react';
import {DndProvider, useDrop} from 'react-dnd'
import { HTML5Backend } from 'react-dnd-html5-backend'

import Tile from "../Components/Tile";
import TileRack from "../Components/TileRack";
import {MULTIPLIERS} from "../constants";

const ScrabbleGame = (props) => {
  const {
    board,
    rack,
    boardConfig,
  } = props

  const renderBoardCol = (letter, index, rowIndex) => {
    const multiplier = boardConfig[rowIndex][index]
    const tile = letter ? {'letter': letter} : null
    return <BoardSquare tile={tile} multiplier={multiplier} key={index}></BoardSquare>
  }

  const renderBoardRow = (row, index) => {
    return (
      <div className="scrabble-board-row">
        {row.map((col, colIndex) => {return renderBoardCol(col, colIndex, index)})}
      </div>
    )
  }

  return (
    <DndProvider backend={HTML5Backend}>
      <div id="scrabble-board">
        {board.map(renderBoardRow)}
      </div>
      <div id="rack" className="d-flex">
        <TileRack tiles={rack}></TileRack>
      </div>
    </DndProvider>
  )
}

const BoardSquare = (props) => {
  const {
    tile,
    multiplier,
  } = props
  return (
    <div className={`scrabble-board-square ${ multiplier }`}>
      {tile ? <Tile {...tile}/> : null}
      { multiplier && multiplier !== MULTIPLIERS.start ? multiplier.toUpperCase(): null}
    </div>
  )
}

export default ScrabbleGame;