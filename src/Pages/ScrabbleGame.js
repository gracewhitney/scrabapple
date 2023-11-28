import React, {useEffect, useState} from 'react';
import {DndProvider, useDrop} from 'react-dnd'
import { HTML5Backend } from 'react-dnd-html5-backend'

import Tile from "../Components/Tile";
import TileRack from "../Components/TileRack";
import {MULTIPLIERS, TURN_ACTION} from "../constants";

const ScrabbleGame = (props) => {
  const {
    board,
    rack,
    boardConfig,
    scoreUrl,
  } = props

  const idTiles = rack.map((tile, i) => {return {...tile, id: i}})
  const [currentRack, setCurrentRack] = useState(idTiles)
  const [playedTiles, setPlayedTiles] = useState([])
  const [points, setPoints] = useState(0)
  const [validationError, setValidationError] = useState()

  useEffect(() => {
    const getScore = async () => {
      if (playedTiles.length === 0) {
        setPoints(0)
        setValidationError(null)
        return
      }
      const resp = await fetch(scoreUrl, {
        method: 'post',
        headers: {'X-CSRFToken': window.csrfmiddlewaretoken},
        body: JSON.stringify({'action': TURN_ACTION.play, 'played_tiles': serializePlayedTiles(playedTiles)})
      })
      const data = await resp.json()
      if (resp.ok) {
        setPoints(data.points)
        setValidationError(null)
      } else {
        setValidationError(data.error)
      }
    }
    getScore()
  }, [playedTiles, scoreUrl, setPoints, setValidationError]);

  const playTile = (letter, id, x, y) => {
    const newPlayedTiles = [...playedTiles]
    const existingPlayIndex = newPlayedTiles.findIndex(tile => tile.tile.id === id)
    if (existingPlayIndex >= 0) {
      newPlayedTiles.splice(existingPlayIndex, 1)
    }
    newPlayedTiles.push({tile: {'letter': letter, 'id': id}, x: x, y: y})
    setPlayedTiles(newPlayedTiles)
  }

  const renderBoardCol = (letter, xIndex, yIndex) => {
    const multiplier = boardConfig[yIndex][xIndex]
    const played_tile = playedTiles.find(tile => tile.x === xIndex && tile.y === yIndex)
    const tile = letter ? {'letter': letter} : (played_tile ? played_tile.tile : null)
    const playTileOnSquare = (letter, id) => {playTile(letter, id, xIndex, yIndex)}
    return <BoardSquare tile={tile} multiplier={multiplier} key={xIndex} playTile={playTileOnSquare}></BoardSquare>
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
      {
        validationError
          ? <div className="text-danger">{validationError}</div>
          : <div className="text-success">{points} points</div>
      }
      <div id="rack" className="d-flex">
        <TileRack tiles={currentRack} removedTileIds={playedTiles.map(tile => tile.tile.id)}></TileRack>
      </div>
    </DndProvider>
  )
}

const BoardSquare = (props) => {
  const {
    tile,
    multiplier,
    playTile,
  } = props

  const [{isOver}, drop] = useDrop(
    () => ({
      accept: 'tile',
      canDrop: () => !tile,
      drop: (item) => playTile(item.letter, item.id),
      collect: monitor => ({isOver: !!monitor.isOver()})
    }),
    [playTile, tile]
  )

  return (
    <div className={`scrabble-board-square ${ multiplier || '' } ${isOver ? 'shadow bg-light': ''}`} ref={drop}>
      {tile ? <Tile {...tile}/> : null}
      { multiplier && multiplier !== MULTIPLIERS.start ? multiplier.toUpperCase(): null}
    </div>
  )
}

const serializePlayedTiles = (playedTiles) => {
  return playedTiles.map((tile) => ({'x': tile.x, 'y': tile.y, 'tile': tile.tile.letter}))
}

export default ScrabbleGame;