import React, {useCallback, useEffect, useState} from 'react';
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
    turnUrl,
  } = props

  const idTiles = rack.map((tile, i) => {return {...tile, id: i}})
  const [playedTiles, setPlayedTiles] = useState([])
  const [points, setPoints] = useState(0)
  const [validationError, setValidationError] = useState()
  const [exchangedTiles, setExchangedTiles] = useState([])

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

  const doPlay = async (action) => {
    const postData = {'action': action}
    if (action === TURN_ACTION.play) {
      postData["played_tiles"] = serializePlayedTiles(playedTiles)
    }
    if (action === TURN_ACTION.exchange) {
      postData["exchanged_tiles"] = exchangedTiles.map(tile => tile.letter)
    }
    const resp = await fetch(turnUrl, {
      method: 'post',
      headers: {'X-CSRFToken': window.csrfmiddlewaretoken},
      body: JSON.stringify(postData)
    })
    if (resp.ok) {
      window.location = resp.url
    } else {
      const data = await resp.json()
      setValidationError(data.error)
    }
  }

  const playTile = (letter, id, x, y) => {
    if (exchangedTiles.findIndex(tile => tile.id === id) >= 0) {
      return
    }
    const newPlayedTiles = [...playedTiles]
    const existingPlayIndex = newPlayedTiles.findIndex(tile => tile.tile.id === id)
    if (existingPlayIndex >= 0) {
      newPlayedTiles.splice(existingPlayIndex, 1)
    }
    newPlayedTiles.push({tile: {'letter': letter, 'id': id}, x: x, y: y})
    setPlayedTiles(newPlayedTiles)
  }

  const returnTileToRack = (id) => {
    const existingPlayIndex = playedTiles.findIndex(tile => tile.tile.id === id)
    if (existingPlayIndex >= 0) {
      const newPlayedTiles = [...playedTiles]
      newPlayedTiles.splice(existingPlayIndex, 1)
      setPlayedTiles(newPlayedTiles)
    }
    const existingExchangeIndex = exchangedTiles.findIndex(tile => tile.id === id)
    if (existingExchangeIndex >= 0) {
      const newExchangedTiles = [...exchangedTiles]
      newExchangedTiles.splice(existingExchangeIndex, 1)
      setExchangedTiles(newExchangedTiles)
    }
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
      <div className="scrabble-board-row" key={index}>
        {row.map((col, colIndex) => {return renderBoardCol(col, colIndex, index)})}
      </div>
    )
  }

  return (
    <DndProvider backend={HTML5Backend}>
      <div className="row w-100">
        <div className="col d-flex flex-column flex-grow-0">
          <div id="scrabble-board">
            {board.map(renderBoardRow)}
          </div>
          <div id="rack" className="d-flex align-self-stretch justify-content-center mb-3">
            <button className="btn btn-secondary align-self-stretch my-2 me-2" onClick={() => {setPlayedTiles([])}}>
              <span className="bi bi-arrow-down-right-square-fill"></span>
            </button>
            <TileRack tiles={idTiles}
                      removedTileIds={playedTiles.map(tile => tile.tile.id) + exchangedTiles.map(tile => tile.id)}
                      returnToRackHandler={returnTileToRack}>
            </TileRack>
          </div>
        </div>
        <div className="col d-flex flex-column" style={{maxWidth: '300px'}}>
          {
            validationError
              ? <div className="badge rounded-pill bg-danger">{validationError}</div>
              : <div className="badge rounded-pill bg-success">{points} points</div>
          }
          <button
            className="btn btn-primary btn-sm mt-2"
            disabled={validationError || playedTiles.length < 1}
            onClick={async () => {await doPlay(TURN_ACTION.play)}}
          >
            <span className="bi bi-person-arms-up"></span> <span>Play</span>
          </button>
          <ExchangeBox exchangedTiles={exchangedTiles} setExchangedTiles={setExchangedTiles} doTurn={doPlay}>
          </ExchangeBox>
          <button
            className="btn btn-secondary btn-sm mt-2"
            onClick={async () => {await doPlay(TURN_ACTION.pass_turn)}}
          >
            Pass
          </button>
          <hr></hr>
          <button
            className="btn btn-danger btn-sm"
            disabled
            onClick={async () => {}}
          >
            <span className="bi bi-exclamation-triangle-fill"></span> Forfeit
          </button>
        </div>
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
    <div className={`scrabble-board-square ${ multiplier || '' } ${isOver ? 'shadow border-success-subtle border-2': ''}`} ref={drop}>
      {tile ? <Tile {...tile}/> : null}
      { multiplier && multiplier !== MULTIPLIERS.start ? multiplier.toUpperCase(): null}
    </div>
  )
}

const ExchangeBox = (props) => {
  const {
    exchangedTiles,
    setExchangedTiles,
    doTurn
  } = props

  const [exchanging, setExchanging] = useState(false)

  const renderNotExchanging = () => {
    return (
      <button
        className="btn btn-secondary btn-sm mt-2"
        onClick={() => {
          setExchanging(true)
        }}
      >
        <span>Exchange</span>
      </button>
    )
  }

  const acceptTile = (letter, id) => {
    setExchangedTiles((currentExchangedTiles) => {
      const existingIndex = currentExchangedTiles.findIndex(tile => tile.id === id)
      if (existingIndex >= 0) {
        return currentExchangedTiles
      }
      return [...currentExchangedTiles, {id: id, letter: letter}]
    })
  }

  const [, drop] = useDrop(
    () => ({
      accept: 'tile',
      drop: (item) => acceptTile(item.letter, item.id),
    })
  )

  const renderExchanging = () => {
    return (
      <>
        <div id="tile-exchange" className="card mt-2" ref={drop}>
          <div className="card-header">Drag tiles here to exchange</div>
          <div className="card-body">
            <div className="row">
              {exchangedTiles.map((tile) => <div className="col" key={tile.id}><Tile {...tile}></Tile></div>)}
            </div>
          </div>
        </div>
        <div className="d-flex justify-content-between">
          <button
            className="btn btn-outline-secondary btn-sm mt-2"
            onClick={() => {setExchanging(false); setExchangedTiles([])}}
          >
            Cancel
          </button>
          <button
            className="btn btn-outline-primary btn-sm mt-2"
            onClick={() => {doTurn(TURN_ACTION.exchange)}}
          >
            Submit
          </button>
        </div>
      </>
    )
  }

  return (exchanging ? renderExchanging() : renderNotExchanging())
}

const serializePlayedTiles = (playedTiles) => {
  return playedTiles.map((tile) => ({'x': tile.x, 'y': tile.y, 'tile': tile.tile.letter}))
}

export default ScrabbleGame;