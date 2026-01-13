import React, {useEffect, useState} from 'react';
import {useDrop} from 'react-dnd'
import {DndProvider} from 'react-dnd-multi-backend'
import { HTML5toTouch } from 'rdndmb-html5-to-touch'

import Tile from "../Components/Tile";
import TileRack from "../Components/TileRack";
import {MULTIPLIERS, TURN_ACTION} from "../constants";

const GameBoard = (props) => {
  const {
    board,
    rack,
    boardConfig,
    scoreUrl,
    turnUrl,
    updateRackUrl,
    gameId,
    inTurn,
    canUndo,
    undoTurnUrl,
    csrfToken,
    enforceWordValidation,
  } = props

  const stackHeight = props.stackHeight || 1
  const idTiles = rack.map((tile, i) => {return {...tile, id: i}})
  const [playedTiles, setPlayedTiles] = useState([])
  const [points, setPoints] = useState(0)
  const [validationError, setValidationError] = useState()
  const [wordValidationError, setWordValidationError] = useState("")
  const [processing, setProcessing] = useState(false)
  const [exchangedTiles, setExchangedTiles] = useState([])

  useEffect(() => {
    const getScore = async () => {
      if (playedTiles.length === 0) {
        setPoints(0)
        setValidationError(null)
        setWordValidationError(null)
        return
      }
      const t = setTimeout(() => setProcessing(true), 300)
      const resp = await fetch(scoreUrl, {
        method: 'post',
        headers: {'X-CSRFToken': csrfToken},
        body: JSON.stringify({'action': TURN_ACTION.play, 'played_tiles': serializePlayedTiles(playedTiles)})
      })
      const data = await resp.json()
      clearTimeout(t)
      if (resp.ok) {
        setPoints(data.points)
        setValidationError(null)
        if (data.invalidWords.length > 0) {
          setWordValidationError("Invalid words: " + data.invalidWords.join(", "))
        } else {
          setWordValidationError(null)
        }
      } else {
        setWordValidationError(null)
        setValidationError(data.error)
      }
      setProcessing(false)
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
    setProcessing(true)
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
      setProcessing(false)
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
    newPlayedTiles.push({tile: {'letter': letter, 'id': id, 'className': "played"}, x: x, y: y})
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

  const returnAllTilesToRack = () => {
    setPlayedTiles([]);
    setExchangedTiles([])
  }

  const renderBoardCol = (letter, xIndex, yIndex) => {
    const multiplier = boardConfig ? boardConfig[yIndex][xIndex] : null
    const played_tile = playedTiles.find(tile => tile.x === xIndex && tile.y === yIndex)
    const tile = played_tile ? {...played_tile.tile} : (letter ? {'letter': letter} : null)
    if (played_tile && letter) {
      tile.letter += letter
    }
    const playTileOnSquare = (letter, id) => {playTile(letter[0], id, xIndex, yIndex)}
    return <BoardSquare hasPlay={!!played_tile} tile={tile} multiplier={multiplier} key={xIndex} gameId={gameId}
                        playTile={playTileOnSquare} stackHeight={stackHeight} extraClass={`pos-${xIndex}${yIndex}`}></BoardSquare>
  }

  const renderBoardRow = (row, index) => {
    return (
      <div className={`${gameId}-board-row`} key={index}>
        {row.map((col, colIndex) => {return renderBoardCol(col, colIndex, index)})}
      </div>
    )
  }

  const turnActions = (
    <>
      <button
        className="btn btn-primary btn-sm mt-2"
        disabled={validationError || playedTiles.length < 1 || (enforceWordValidation && wordValidationError)}
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
    </>
  )

  return (
    <DndProvider options={HTML5toTouch}>
      <div className="row w-100">
        <div className="col d-flex flex-column flex-grow-0">
          <div id={`${gameId}-board`}>
            {board.map(renderBoardRow)}
          </div>
          <TileRack
            gameId={gameId}
            tiles={idTiles}
            removedTileIds={playedTiles.map(tile => tile.tile.id) + exchangedTiles.map(tile => tile.id)}
            returnToRackHandler={returnTileToRack}
            returnAllTilesToRackHandler={returnAllTilesToRack}
            updateRackUrl={updateRackUrl}
          >
          </TileRack>
        </div>
        <div className={`col d-flex flex-column actions-col ${gameId}-actions`}>
          {
            validationError
              ? <div className={`badge rounded-pill ${processing ? 'bg-danger-subtle' : 'bg-danger'}`}>{validationError}</div>
              : (
                wordValidationError && enforceWordValidation
                ? null
                : <div className={`badge rounded-pill ${processing ? 'bg-success-subtle' : 'bg-success'}`}>{points} points</div>
              )
          }
          {
            wordValidationError
              ? <div className={`badge rounded-pill ${processing ? 'bg-danger-subtle' : 'bg-danger'} mt-2`}>{wordValidationError}</div>
              : null
          }
          { inTurn ? turnActions : null }
          {
            canUndo
            ? <form action={undoTurnUrl} method="post" className="d-flex flex-column">
                <input type="hidden" value={csrfToken || ''} name="csrfmiddlewaretoken"/>
                <button type="submit" className="btn btn-sm btn-secondary mt-2">Undo last turn</button>
              </form>
            : null
          }
        </div>
      </div>
    </DndProvider>
  )
}

const BoardSquare = (props) => {
  const {
    tile,
    hasPlay,
    multiplier,
    playTile,
    gameId,
    stackHeight,
    extraClass,
  } = props

  const [{isOver}, drop] = useDrop(
    () => ({
      accept: 'tile',
      canDrop: () => !hasPlay && (!tile || tile.letter.length < stackHeight),
      drop: (item) => playTile(item.letter, item.id),
      collect: monitor => ({isOver: !!monitor.isOver()})
    }),
    [playTile, tile]
  )

  return (
    <div className={`${gameId}-board-square ${extraClass} ${ multiplier || '' } ${isOver ? 'shadow border-success-subtle border-2': ''}`} ref={drop}>
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

export default GameBoard;